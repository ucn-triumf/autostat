# Run the purification process using the cryostat
# Derek Fujimoto
# Mar 2025

"""
    AUTOPURIFY

    This runs the cryostat in heater on mode. It uses a PID loop to control
    HTR204 in order to keep PT206 to some target pressure.

    Control logic:
        - Use the simple_pid package to get the setpoints
        - Wait an extended duration between control operations
        - If PT206 is above safety threshold, then open FPV201 to 100% for at least 30s to reduce pressure
        - If PT206 is below threshold and FPV201 is 100% open, then reset FPV201 to the value prior to the script changing its value
        - If at any point FPV201 or HTR204 are turned off, stop PID control
        - If at any point HTR204 has changed by more than 1 mA between control operations, then stop PID control

    ODB settings (/Equipment/AutoPurify/Settings)
        P: proportional control value
        I: intregral control value
        D: differential control value
        setpoint: target for PT206 in mbar
        time_step_s: duration between control operations in seconds
        pressure_high_thresh: threshold pressure of PT206 in mbar, above which FPV201 opens
        output_limit_low: lower bound on possible setpoint of HTR204
        output_limit_high: upper bound on possible setpoint of HTR204
        proportional_on_measurement: Whether the proportional term should be calculated on the
            input directly rather than on the error (which is the traditional way). Using proportional-on-measurement avoids overshoot for some types of systems.
        differential_on_measurement: Whether the differential term should be calculated on the
            input directly rather than on the error (which is the traditional way).

    When settings are changed in the ODB they are also changed for the control script, no restart required
"""

import midas
import midas.frontend
import epics
from simple_pid import PID
import time
import collections

class AutoPurify(midas.frontend.EquipmentBase):
    fcontext = None
    fsocket = None
    fpoller = None
    fmessage = None
    """
    We define an "equipment" for each logically distinct task that this frontend
    performs. For example, you may have one equipment for reading data from a
    device and sending it to a midas buffer, and another equipment that updates
    summary statistics every 10s.

    Each equipment class you define should inherit from
    `midas.frontend.EquipmentBase`, and should define a `readout_func` function.
    If you're creating a "polled" equipment (rather than a periodic one), you
    should also define a `poll_func` function in addition to `readout_func`.
    """
    def __init__(self, client):
        # The name of our equipment. This name will be used on the midas status
        # page, and our info will appear in /Equipment/AutoPurify in
        # the ODB.
        self.equip_name = "AutoPurify"

        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_PERIODIC
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 2323
        default_common.period_ms = 5000
        default_common.read_when = midas.RO_ALWAYS
        default_common.log_history = 5

        # Settings
        default_settings = collections.OrderedDict([
            ("P", 1.0),
            ("I", 0.0),
            ("D", 0.0),
            ("setpoint", 1400),
            ("time_step_s", 60),
            ("pressure_high_thresh", 1480),
            ("output_limit_low", 0),
            ("output_limit_high", 1000),
            ("proportional_on_measurement", False),
            ("differential_on_measurement", False),
        ])

        # You MUST call midas.frontend.EquipmentBase.__init__ in your equipment's __init__ method!
        midas.frontend.EquipmentBase.__init__(self, client, self.equip_name, default_common,default_settings)

        # Setup callback on port enable ODB keys
        self.client.odb_watch(self.odb_settings_dir, self.settings_callback)

        # get epics readback variables to read and write
        # by default uses the monitor backend (desired)
        self.pv = {'setvar': epics.PV('UCN2:HE4:HTR204:CUR'), # set this variable
                   'rdvar': epics.PV('UCN2:HE4:PT206:RDPRESS'), # control this variable to be at setpoint
                   'htr204_staton': epics.PV('UCN2:HE4:HTR204:STATON'),
                   'fpv201_pos': epics.PV('UCN2:HE4:FPV201:POS'),
                   'fpv201_staton': epics.PV('UCN2:HE4:FPV201:STATON'),
                  }

        # setup PID controller
        # see https://simple-pid.readthedocs.io/en/latest/reference.html
        self.pid = PID(
            Kp = self.client.odb_get(f'{self.odb_settings_dir}/P'), # P
            Ki = self.client.odb_get(f'{self.odb_settings_dir}/I'), # I
            Kd = self.client.odb_get(f'{self.odb_settings_dir}/D'), # D
            setpoint = self.client.odb_get(f'{self.odb_settings_dir}/setpoint'), # target pressure
            output_limits = (self.client.odb_get(f'{self.odb_settings_dir}/output_limit_low'),
                             self.client.odb_get(f'{self.odb_settings_dir}/output_limit_high')), # HTR204 setpoint limits
            proportional_on_measurement = self.client.odb_get(f'{self.odb_settings_dir}/proportional_on_measurement'),
            differential_on_measurement = self.client.odb_get(f'{self.odb_settings_dir}/differential_on_measurement'),
            starting_output = self.pv['setvar'].get() # The starting point for the PID’s output.
            )

        # setup start of run values
        self.t0 = time.time()                           # time of last set value
        self.htr204_t0 = self.pv['setvar'].get()         # heater setpoint of last read/set
        self.t_panic = 0                                # time at which we have panicked and
                                                        # opened safety valve
        self.fpv201_setpt = 0                           # current setpoint of fpv201, for reset
        self.time_step_s = self.client.odb_get(f'{self.odb_settings_dir}/time_step_s')

        # You can set the status of the equipment (appears in the midas status page)
        self.set_status("Initialized")

    def settings_callback(self, client, path, odb_value):
        """Callback function when setting tree is changed"""
        self.pid.Kp = odb_value['P']
        self.pid.Ki = odb_value['I']
        self.pid.Kd = odb_value['D']
        self.pid.setpoint = odb_value['setpoint']
        self.pid.output_limit = (odb_value['output_limit_low'],
                                 odb_value['output_limit_high'])
        self.pid.proportional_on_measurement = odb_value['proportional_on_measurement']
        self.pid.differential_on_measurement = odb_value['differential_on_measurement']
        self.time_step_s = odb_value['time_step_s']

        client.msg(f'{self.equip_name} settings changed: P={self.pid.Kp}, I={self.pid.Ki}, D={self.pid.Kd}, setpoint={self.pid.setpoint}, limits={self.pid.output_limit}, prop_on_meas={self.pid.proportional_on_measurement}, diff_on_meas={self.pid.differential_on_measurement}, time_step_s={self.time_step_s}')

    def readout_func(self):
        """
        For a periodic equipment, this function will be called periodically
        (every 100ms in this case). It should return either a `cdms.event.Event`
        or None (if we shouldn't write an event).
        """

        # check that controls are active
        if self.pv['htr204_staton'].get() != 1:
            msg = f'HTR204 is not on - stopping AutoPurify'
            self.client.trigger_internal_alarm('AutoPurifyStop', msg,
                                               default_alarm_class='Warning')
            self.client.disconnect()

        if self.pv['fpv201_staton'].get() != 1:
            msg = f'FPV201 is not on - stopping AutoPurify'
            self.client.trigger_internal_alarm('AutoPurifyStop', msg,
                                               default_alarm_class='Warning')
            self.client.disconnect()

        # check if htr setpoint changed significantly between calls
        if abs(self.pv['setvar'].get() - self.htr204_t0) > 1:
            msg = f'HTR204 setpoint does not match previously set value - stopping AutoPurify'
            self.client.trigger_internal_alarm('AutoPurifyStop', msg,
                                               default_alarm_class='Warning')
            self.client.disconnect()

        # get time
        t1 = time.time()

        # check if panic state
        if self.pv['rdvar'].get() > self.client.odb_get(f'{self.odb_settings_dir}/pressure_high_thresh'):
            self.fpv201_setpt = self.pv['fpv201_pos'].get()
            self.pv['fpv201_pos'].put(100)
            self.t_panic = time.time()
            self.client.msg('PT206 pressure too high! Opening FPV201 to 100%')

        # panicking: wait at least 30 s for the pressure to go down
        elif self.pv['fpv201_pos'].get() > 0 and (t1 - self.t_panic) > 30:
            self.pv['fpv201_pos'].put(self.fpv201_setpt)
            self.client.msg(f'PT206 pressure back under control! Opening FPV201 to {self.fpv201_setpt:.0f}%')

        # new control value
        if t1-self.t0 >= self.time_step_s:

            # apply control operation
            self.pv['setvar'].put(self.pid(self.pv['rdvar'].get()))

            # new t0 and htr setpoint value to check against
            self.t0 = t1
            self.htr204_t0 = self.pv['setvar'].get()

class MyFrontend(midas.frontend.FrontendBase):
    """
    A frontend contains a collection of equipment.
    You can access self.client to access the ODB etc (see `midas.client.MidasClient`).
    """
    def __init__(self):
        # You must call __init__ from the base class.
        midas.frontend.FrontendBase.__init__(self, "autopurify")

        self.add_equipment(AutoPurify(self.client))
        self.client.msg("AutoPurify frontend initialized.")

    def frontend_exit(self):
        """
        Most people won't need to define this function, but you can use
        it for final cleanup if needed.
        """
        self.client.msg("AutoPurify frontend stopped.")

if __name__ == "__main__":
    # The main executable is very simple - just create the frontend object,
    # and call run() on it.
    with MyFrontend() as my_fe:
        my_fe.run()
