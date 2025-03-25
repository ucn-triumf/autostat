# Run the purification process using the cryostat
# Derek Fujimoto
# Mar 2025

# Jeff modified to check FPVs and AV203 to make sure they are ready,
# before starting.  This would have saved me a few minutes on Mar. 22,
# 2025.

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
    
    # settable limits
    LIMITS = {  'pt206_setpoint': (0, 1500),
                'time_step_s': (0, 500),
                'pt206_pressure_high_thresh': (0, 1500),
                'htr204_output_limit_low': (0, 1000),
                'htr204_output_limit_high': (0, 1000)
             }
             
    # must be lower than this
    FPV201_START_LIMIT = 40 
    
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
            ("pt206_setpoint", 1400),
            ("time_step_s", 60),
            ("pt206_pressure_high_thresh", 1480),
            ("htr204_output_limit_low", 0),
            ("htr204_output_limit_high", 1000),
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
                   'fpv201_read': epics.PV('UCN2:HE4:FPV201:RDDACP'), # Jeff added this and the following so that we can check the status of all FPV's and AV203
                   'fpv202_read': epics.PV('UCN2:HE4:FPV202:RDDACP'),
                   'fpv203_read': epics.PV('UCN2:HE4:FPV203:RDDACP'),
                   'fpv204_read': epics.PV('UCN2:HE4:FPV204:RDDACP'),
                   'fpv205_read': epics.PV('UCN2:HE4:FPV205:RDDACP'),
                   'fpv206_read': epics.PV('UCN2:HE4:FPV206:RDDACP'),
                   'fpv207_read': epics.PV('UCN2:HE4:FPV207:RDDACP'),
                   'fpv208_read': epics.PV('UCN2:HE4:FPV208:RDDACP'),
                   'fpv209_read': epics.PV('UCN2:HE4:FPV209:RDDACP'),
                   'fpv211_read': epics.PV('UCN2:HE4:FPV211:RDDACP'),
                   'fpv212_read': epics.PV('UCN2:HE4:FPV212:RDDACP'),
                   'av203_staton': epics.PV('UCN2:HE4:AV203:STATON'),
                   'fpv211_autostat': epics.PV('UCN2:HE4:FPV211:STAT.B8'),
                  }

        # get limited values

        # setup PID controller
        # see https://simple-pid.readthedocs.io/en/latest/reference.html
        self.pid = PID(
            Kp = self.client.odb_get(f'{self.odb_settings_dir}/P'), # P
            Ki = self.client.odb_get(f'{self.odb_settings_dir}/I'), # I
            Kd = self.client.odb_get(f'{self.odb_settings_dir}/D'), # D
            setpoint = self._get_limited_var('pt206_setpoint'), # target pressure
            output_limits = (self._get_limited_var('htr204_output_limit_low'),
                             self._get_limited_var('htr204_output_limit_high')), # HTR204 setpoint limits
            proportional_on_measurement = self.client.odb_get(f'{self.odb_settings_dir}/proportional_on_measurement'),
            differential_on_measurement = self.client.odb_get(f'{self.odb_settings_dir}/differential_on_measurement'),
            starting_output = self.pv['setvar'].get() # The starting point for the PID’s output.
            )

        # setup start of run values
        self.t0 = time.time()                           # time of last set value
        self.htr204_t0 = self.pv['setvar'].get()        # heater setpoint of last read/set
        self.t_panic = 0                                # time at which we have panicked and
                                                        # opened safety valve
        self.panic_thresh = self._get_limited_var('pt206_pressure_high_thresh')
        self.panic_state = False
        
        self.fpv201_setpt = self.pv['fpv201_pos'].get() # current setpoint of fpv201, for reset
        self.time_step_s = self._get_limited_var('time_step_s')

        # check that FPV201 is suitably low, to allow to relief of pressure
        if self.pv['fpv201_pos'].get() > self.FPV201_START_LIMIT:
            self.client.msg(f'FPV201 setpoint ({self.pv["fpv201_pos"].get():.1f}) too high (>{self.FPV201_START_LIMIT}), cannot guarantee relief of pressure if PT206 gets too high', is_error=True)
            self.disconnect()

        # check to make sure that the pattern of FPV's and AV203 is correct
        if (self.pv['fpv201_read'].get() > self.FPV201_START_LIMIT     # ON
            or self.pv['fpv202_read'].get() > self.FPV201_START_LIMIT  # ON
            or self.pv['fpv203_read'].get() < self.FPV201_START_LIMIT  # OFF
            or self.pv['fpv204_read'].get() > self.FPV201_START_LIMIT  # ON
            or self.pv['fpv205_read'].get() > self.FPV201_START_LIMIT  # ON
            or self.pv['fpv206_read'].get() > self.FPV201_START_LIMIT  # ON
            or self.pv['fpv207_read'].get() > self.FPV201_START_LIMIT  # ON
            or self.pv['fpv208_read'].get() > self.FPV201_START_LIMIT  # ON
            or self.pv['fpv209_read'].get() < self.FPV201_START_LIMIT  # OFF
            or self.pv['fpv211_read'].get() > self.FPV201_START_LIMIT  # ON
            or self.pv['fpv212_read'].get() > self.FPV201_START_LIMIT  # ON
            or self.pv['av203_staton'].get() == 1 
            or self.pv['fpv211_autostat'].get() == 1):
            self.client.msg(f'Only FPV203 and FPV209 should be open. FPV211 autofill should be off. Check all FPVs and AV203', is_error=True)
            self.disconnect()


        # You can set the status of the equipment (appears in the midas status page)
        self.set_status("Initialized")

    def _ensure_set(self, setname, val):
        """Ensure value is set by checking the readback periodically after set
        
        Args: 
            setname (str): name of the variable to set, without full path
            readname (str): name of the variable to read, without full path
            val (float): value to set
        """
        
        # time between set attempts in seconds
        delay = 1 
        
        # number of attempts limit
        nlimit = 100
        n = 0
        
        # try to repeatedly set the value
        while abs(self.pv[setname].get() - val) > 1:
            time.sleep(delay)
            self.pv[setname].put(val)
            n += 1
            
            if n > nlimit: 
                msg = f'Cannot set {setname} to {val}. Tried {nlimit} attempts. Consider setting manually.'
                n = 0
                self.client.trigger_internal_alarm('AutoPurifyStop', msg,
                                               default_alarm_class='Warning')

    def _get_limited_var(self, varname):
        val = self.client.odb_get(f'{self.odb_settings_dir}/{varname}')
        return self._limit_var(varname, val)

    def _limit_var(self, varname, val):
        """Get a variable while respecting the limits 
        
        Args:
            varname (str): name of the variable, without full path
            odb_value (dict): dict that was passed to settings_callback
        Returns: 
            float: value, forced within limits
        """

        lim = self.LIMITS[varname]
        if val < lim[0]:
            val = lim[0]
            self.client.odb_set(f'{self.odb_settings_dir}/{varname}', val)
            self.client.msg(f'"{varname}" value too low, bounded by {lim[0]}')
        elif val > lim[1]:
            val = lim[1]
            self.client.odb_set(f'{self.odb_settings_dir}/{varname}', val)
            self.client.msg(f'"{varname}" value too high, bounded by {lim[1]}')

        return val

    def settings_callback(self, client, path, odb_value):
        """Callback function when setting tree is changed"""
        
        # PID
        self.pid.Kp = odb_value['P']
        self.pid.Ki = odb_value['I']
        self.pid.Kd = odb_value['D']
        
        # setpoint
        self.pid.setpoint = self._limit_var('pt206_setpoint', odb_value['pt206_setpoint'])
        
        # output limits
        val0 = self._limit_var('htr204_output_limit_low', odb_value['htr204_output_limit_low'])
        val1 = self._limit_var('htr204_output_limit_high', odb_value['htr204_output_limit_high'])
        self.pid.output_limits = (val0, val1)
        
        # boolean values
        self.pid.proportional_on_measurement = odb_value['proportional_on_measurement']
        self.pid.differential_on_measurement = odb_value['differential_on_measurement']
        
        # time step
        self.time_step_s = self._limit_var('time_step_s', odb_value['time_step_s'])

        # panic threshold
        self.panic_thresh = self._limit_var('pt206_pressure_high_thresh',
                                            odb_value['pt206_pressure_high_thresh'])

        msg = [f'P={self.pid.Kp}',
               f'I={self.pid.Ki}', 
               f'D={self.pid.Kd}', 
               f'setpoint={self.pid.setpoint}', 
               f'limits={self.pid.output_limits}', 
               f'prop_on_meas={self.pid.proportional_on_measurement}',
               f'diff_on_meas={self.pid.differential_on_measurement}',
               f'pressure_high_thresh={self.panic_thresh}',
               ]

        client.msg(f'{self.equip_name} settings changed: ' + ', '.join(msg))

    def readout_func(self):
        """
        For a periodic equipment, this function will be called periodically
        (every 100ms in this case). It should return either a `cdms.event.Event`
        or None (if we shouldn't write an event).
        """

        # check that controls are active
        if self.pv['htr204_staton'].get() != 1:
            self._ensure_set('setvar', 0)
            msg = f'HTR204 is not on - stopping AutoPurify'
            self.client.trigger_internal_alarm('AutoPurifyStop', msg,
                                               default_alarm_class='Warning')
            self.client.disconnect()
            return

        if self.pv['fpv201_staton'].get() != 1:
            msg = f'FPV201 is not on - stopping AutoPurify'
            self._ensure_set('setvar', 0)
            self.client.trigger_internal_alarm('AutoPurifyStop', msg,
                                               default_alarm_class='Warning')
            self.client.disconnect()
            return

        # check to make sure that the pattern of FPV's and AV203 is correct
        if (self.pv['fpv201_read'].get() > self.FPV201_START_LIMIT      # ON
            or self.pv['fpv202_read'].get() > self.FPV201_START_LIMIT   # ON
            or self.pv['fpv203_read'].get() < self.FPV201_START_LIMIT   # OFF
            or self.pv['fpv204_read'].get() > self.FPV201_START_LIMIT   # ON
            or self.pv['fpv205_read'].get() > self.FPV201_START_LIMIT   # ON
            or self.pv['fpv206_read'].get() > self.FPV201_START_LIMIT   # ON
            or self.pv['fpv207_read'].get() > self.FPV201_START_LIMIT   # ON
            or self.pv['fpv208_read'].get() > self.FPV201_START_LIMIT   # ON
            or self.pv['fpv209_read'].get() < self.FPV201_START_LIMIT   # OFF
            or self.pv['fpv211_read'].get() > self.FPV201_START_LIMIT   # ON
            or self.pv['fpv212_read'].get() > self.FPV201_START_LIMIT   # ON
            or self.pv['av203_staton'].get() == 1
            or self.pv['fpv211_autostat'].get() == 1) and not self.panic_state:

            self._ensure_set('setvar', 0)
            msg = f'Only FPV203 and FPV209 should be open. FPV211 autofill should be off. Check all FPVs and AV203'
            self.client.trigger_internal_alarm('AutoPurifyStop', msg,
                                               default_alarm_class='Warning')
            self.client.disconnect()
            return

        # check if htr setpoint changed significantly between calls
        if abs(self.pv['setvar'].get() - self.htr204_t0) > 1:
            msg = f'HTR204 setpoint ({self.pv["setvar"].get():.0f}) does not match '+\
                  f'previously set value ({self.htr204_t0:.0f})- stopping AutoPurify'
            self._ensure_set('setvar', 0)
            self.client.trigger_internal_alarm('AutoPurifyStop', msg,
                                               default_alarm_class='Warning')
            self.client.disconnect()
            return

        # get time
        t1 = time.time()

        # check if panic state
        if self.pv['rdvar'].get() > self.panic_thresh:
        
            if not self.panic_state:
                
                # get values before we do anything 
                self.fpv201_setpt = self.pv['fpv201_pos'].get()
                self.last_output = self.pv['setvar'].get()
                
                # set the panic state, open valves and stop the heater
                self.pv['fpv201_pos'].put(100)
                self._ensure_set('setvar', 0)
                self.htr204_t0 = 0
                self.t_panic = time.time()
                self.panic_state = True
                self.client.msg(f'PT206 pressure too high ({self.pv["rdvar"].get():.1f} > {self.panic_thresh})! Opening FPV201 to 100%')

        # panicking: wait at least 30 s for the pressure to go down
        elif self.panic_state and (t1 - self.t_panic) > 30:
        
            # restore prev values
            self.pv['fpv201_pos'].put(self.fpv201_setpt)
            self.pv['setvar'].put(self.last_output*0.8)
            
            # stop panicking
            self.panic_state = False
            self.client.msg(f'PT206 pressure back under control! Setting FPV201 to {self.fpv201_setpt:.0f}%')

        # new control value
        if t1-self.t0 >= self.time_step_s and not self.panic_state:

            # apply control operation
            val = self.pid(self.pv['rdvar'].get())
            self.pv['setvar'].put(val)

            # new t0 and htr setpoint value to check against
            self.t0 = t1
            self.htr204_t0 = val

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
