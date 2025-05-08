# PID controller base class
# Derek Fujimoto
# Mar 2025
"""

"""

import midas
import midas.frontend
import epics
from simple_pid import PID
import time
import collections
import numpy as np

class PIDControllerBase(midas.frontend.EquipmentBase):
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
    LIMITS = {  'target_setpoint': (0, 1500),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1000),
                'output_limit_high': (0, 1000)}

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':None,
                'target':None}

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 1.0),
        ("I", 0.0),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 1400),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1000),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
        ("target_timeout_s", 30),
        ("control_pv", EPICS_PV['ctrl']),
        ("target_pv", EPICS_PV['target']),
    ])

    # readbacks which should be below a threshold value (float)
    DEVICE_THRESH_OFF= {}

    # readbacks should be above a threshold value (float)
    DEVICE_THRESH_ON = {}

    # the state of these devices should be off (boolean 0)
    DEVICE_STATE_OFF = []

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = []

    def __init__(self, client, equip_name):
        # The name of our equipment. This name will be used on the midas status
        # page, and our info will appear in /Equipment/AutoPurify in
        # the ODB.

        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_PERIODIC
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 2323
        default_common.period_ms = 5000
        default_common.read_when = midas.RO_ALWAYS
        default_common.log_history = 5

        # You MUST call midas.frontend.EquipmentBase.__init__ in your equipment's __init__ method!
        midas.frontend.EquipmentBase.__init__(self, client, equip_name, default_common, self.DEFAULT_SETTINGS)

        # Setup callback on ODB keys
        self.client.odb_watch(self.odb_settings_dir,
                              self.callback_main,
                              pass_changed_value_only=True)

        # get epics readback variables to read and write
        # by default uses the monitor backend (desired)
        self.pv = {key: epics.PV(val) for key, val in self.EPICS_PV.items()}

        # setup PID controller
        # see https://simple-pid.readthedocs.io/en/latest/reference.html
        self.reset_pid()
        self.t0 = 0 # time of last setpoint change

        # setup checking readback functionality
        self.t_target_last = time.time()     # time of last change
        self.target_last = self.pv['target'].get() # value of last target readback

        # You can set the status of the equipment (appears in the midas status page)
        if self.is_enabled:
            self.disable()

    def callback_main(self, client, path, idx, odb_value):
        """Main callback that actually gets set. Depending on the changed value, update internal variables

        Note that only 256 callbacks are permitted according to MAX_OPEN_RECORDS which is checked during db_add_open_record()
        See:  https://daq00.triumf.ca/~daqweb/doc/midas-develop/html/group__odbfunctionc.html#gae77a045264f3933cdff85f35a3407f86
        also: https://daq00.triumf.ca/~daqweb/doc/midas-develop/html/group__odbfunctionc.html#ga972fa15324a309897f832e5dd47755b9
        """

        # choose callback operation
        if '/Enabled' in path:
            if odb_value:
                self.set_status("Running", status_color='greenLight')
                self.reset_pid()

                settings_list = [f'P={self.pid.Kp}',
                                f'I={self.pid.Ki}',
                                f'D={self.pid.Kd}',
                                f'setpoint={self.pid.setpoint}',
                                f'limits={self.pid.output_limits}',
                                f'proportional_on_measurement={self.pid.proportional_on_measurement}',
                                f'differential_on_measurement={self.pid.differential_on_measurement}',
                                f'last_setpoint={self.last_setpoint}',
                                f'time_step_s={self.time_step_s}',
                                f'inverted={self.inverted == -1}',
                                ]
                client.msg(f'{self.name} has been enabled with settings: '+', '.join(settings_list))
            else:
                self.set_status("Ready, Disabled", status_color='yellowGreenLight')
                self.last_setpoint = np.nan
                client.msg(f'{self.name} has been disabled')

        elif '/P' == path[-2:]:
            self.pid.Kp = odb_value*self.inverted
            client.msg(f'{self.name} P value changed to {self.pid.Kp}')

        elif '/I' == path[-2:]:
            self.pid.Ki = odb_value*self.inverted
            client.msg(f'{self.name} I value changed to {self.pid.Ki}')

        elif '/D' == path[-2:]:
            self.pid.Kd = odb_value*self.inverted
            client.msg(f'{self.name} D value changed to {self.pid.Kd}')

        elif '/target_setpoint' in path:
            self.pid.setpoint = self.limit_var('target_setpoint', odb_value)
            client.msg(f'{self.name} setpoint changed to {self.pid.setpoint}')

        elif '/output_limit_low' in path:
            val0 = self.limit_var('output_limit_low', odb_value)
            val1 = client.odb_get(self.odb_settings_dir+'/output_limit_high')
            self.pid.output_limits = (val0, val1)
            client.msg(f'{self.name} output limits changed to {self.pid.output_limits}')

        elif '/output_limit_high' in path:
            val0 = client.odb_get(self.odb_settings_dir+'/output_limit_low')
            val1 = self.limit_var('output_limit_high', odb_value)
            self.pid.output_limits = (val0, val1)
            client.msg(f'{self.name} output limits changed to {self.pid.output_limits}')

        elif '/time_step_s' in path:
            self.time_step_s = self.limit_var('time_step_s', odb_value)
            client.msg(f'{self.name} time step changed to {self.time_step_s}')

        elif '/inverted_output' in path:
            self.inverted = -1.0 if odb_value else 1.0
            client.msg(f'{self.name} inverted output state changed to {self.inverted}')

        elif '/target_timeout_s' in path:
            self.target_timeout_s = odb_value
            client.msg(f'{self.name} target timeout changed to {self.target_timeout_s} seconds')

        elif '/control_pv' in path:
            if client.odb_get(self.odb_settings_dir + '/control_pv') != self.EPICS_PV['ctrl']:
                client.odb_set(self.odb_settings_dir + '/control_pv', self.EPICS_PV['ctrl'])
                client.msg(f'{self.name} control_pv is read-only')

        elif '/target_pv' in path:
            if client.odb_get(self.odb_settings_dir + '/target_pv') != self.EPICS_PV['target']:
                client.odb_set(self.odb_settings_dir + '/target_pv', self.EPICS_PV['target'])
                client.msg(f'{self.name} target_pv is read-only')

        elif '/proportional_on_measurement' in path:
            self.pid.proportional_on_measurement = odb_value
            client.msg(f'{self.name} proportional_on_measurement changed to {self.pid.proportional_on_measurement}')

        elif '/differential_on_measurement' in path:
            self.pid.differential_on_measurement = odb_value
            client.msg(f'{self.name} differential_on_measurement changed to {self.pid.differential_on_measurement}')

    def check_device_states(self, alarm=True):
        """Check devices are set properly

        Args:
            alarm (bool): if true, when devices fail check raise MIDAS alarm

        Returns:
            bool: if true, everything is ok, else should disconnect
        """

        state_ok = True

        # if any of the following conditions are true, then the flow state is
        # not correct and we disconnect

        # these should be off
        for name, lim in self.DEVICE_THRESH_OFF.items():
            if self.pv[name].get() > lim:
                state_ok = False
                self.client.msg(f'{self.name}: "{self.EPICS_PV[name]}" is above threshold ({lim})',
                                is_error=True)

        # these should be on
        for name, lim in self.DEVICE_THRESH_ON.items():
            if self.pv[name].get() < lim:
                state_ok = False
                self.client.msg(f'{self.name}: "{self.EPICS_PV[name]}" is below threshold ({lim})',
                                is_error=True)

        # these should be off
        for name in self.DEVICE_STATE_OFF:
            if int(self.pv[name].get()):
                state_ok = False
                self.client.msg(f'{self.name}: "{self.EPICS_PV[name]}" should not be in the ON state. Turn it OFF',
                                is_error=True)

        # these should be on
        for name in self.DEVICE_STATE_ON:
            if not int(self.pv[name].get()):
                state_ok = False
                self.client.msg(f'{self.name}: "{self.EPICS_PV[name]}" should not be in the OFF state. Turn it ON',
                                is_error=True)

        # alarm on fail
        if not state_ok:
            self.disable()
            if alarm:
                msg = f'{self.name} failed device check. See messages.'
                self.client.trigger_internal_alarm('AutoStat', msg,
                                               default_alarm_class='Warning')

        return state_ok

    def disable(self):
        """Set disable status in the event of program crash"""
        self.client.odb_set(self.odb_settings_dir + '/Enabled', False)
        self.set_status("Ready, Disabled", status_color='yellowGreenLight')
        self.last_setpoint = np.nan

    @property
    def is_enabled(self):
        return self.client.odb_get(self.odb_settings_dir + '/Enabled')

    def get_limited_var(self, varname):
        val = self.client.odb_get(f'{self.odb_settings_dir}/{varname}')
        return self.limit_var(varname, val)

    def limit_var(self, varname, val):
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

    def readout_func(self):
        """
        For a periodic equipment, this function will be called periodically
        (every 100ms in this case). It should return either a `cdms.event.Event`
        or None (if we shouldn't write an event).
        """

        # don't run if not enabled
        if not self.is_enabled:
            return

        # check that all devices are withing operating limits
        if not self.check_device_states():
            return

        # check if setpoint changed significantly between calls
        if not np.isnan(self.last_setpoint) and abs(self.pv['ctrl'].get() - self.last_setpoint) > 1:
            msg = f'"{self.EPICS_PV["ctrl"]}" setpoint ({self.pv["ctrl"].get():.0f}) '+\
                  f'does not match previously set value ({self.last_setpoint:.0f}) - disabling {self.name}'
            self.client.trigger_internal_alarm('AutoStat', msg,
                                               default_alarm_class='Warning')
            self.disable()
            return

        # get time
        t1 = time.time()

        # check if target is updating
        target_val = self.pv['target'].get()

        # target is updating, update saved values
        if self.target_last != target_val:
            self.target_last = target_val
            self.t_target_last = t1

        # target has not been updated past the timeout duration
        elif (self.target_timeout_s > 0) and (t1-self.t_target_last > self.target_timeout_s):
            msg = f'"{self.EPICS_PV["target"]}" timeout! Value read back has been {target_val} for the last {t1 - self.t_target_last:.1f} seconds'
            self.client.trigger_internal_alarm('AutoStat', f'"{self.EPICS_PV["target"]}" timeout',
                                               default_alarm_class='Warning')
            self.client.msg(msg)
            self.disable()

        # new control value
        if t1-self.t0 >= self.time_step_s:

            # apply control operation
            val = self.pid(target_val)
            self.pv['ctrl'].put(val)
            self.t0 = t1

            # new t0 and htr setpoint value to check against
            self.t0 = t1
            self.last_setpoint = val

    def reset_pid(self):
        """Reset PID internal values and reset parameters according to ODB values"""
        self.inverted = -1.0 if self.client.odb_get(f'{self.odb_settings_dir}/inverted_output') else 1.0

        # reset internal values as well as derivative and integral history
        if hasattr(self, 'pid'):
            self.pid.reset()

        # make new PID object
        self.pid = PID(
            Kp = self.client.odb_get(f'{self.odb_settings_dir}/P')*self.inverted, # P
            Ki = self.client.odb_get(f'{self.odb_settings_dir}/I')*self.inverted, # I
            Kd = self.client.odb_get(f'{self.odb_settings_dir}/D')*self.inverted, # D
            setpoint = self.get_limited_var('target_setpoint'), # target pressure
            output_limits = (self.get_limited_var('output_limit_low'),
                             self.get_limited_var('output_limit_high')),
            proportional_on_measurement = self.client.odb_get(f'{self.odb_settings_dir}/proportional_on_measurement'),
            differential_on_measurement = self.client.odb_get(f'{self.odb_settings_dir}/differential_on_measurement'),
            starting_output = self.pv['ctrl'].get() # The starting point for the PID’s output.
            )
        self.last_setpoint = self.pv['ctrl'].get()
        self.time_step_s = self.get_limited_var('time_step_s')
        self.target_timeout_s = self.client.odb_get(f'{self.odb_settings_dir}/target_timeout_s')

class PIDControllerBase_ZeroOnDisable(PIDControllerBase):
    """Same as PIDControllerBase, but sets ctrl variable to zero upon self disable"""

    def disable(self):
        self.pv['ctrl'].put(0.0)
        super().disable()

    def readout_func(self):
        """
        For a periodic equipment, this function will be called periodically
        (every 100ms in this case). It should return either a `cdms.event.Event`
        or None (if we shouldn't write an event).
        """

        # don't run if not enabled
        if not self.is_enabled:
            return

        # check that all devices are withing operating limits
        if not self.check_device_states():
            self.disable()
            return

        # check if setpoint changed significantly between calls
        if not np.isnan(self.last_setpoint) and abs(self.pv['ctrl'].get() - self.last_setpoint) > 1:
            msg = f'"{self.EPICS_PV["ctrl"]}" setpoint ({self.pv["ctrl"].get():.0f}) '+\
                  f'does not match previously set value ({self.last_setpoint:.0f}) - disabling {self.name}'
            self.client.trigger_internal_alarm('AutoStat', msg,
                                               default_alarm_class='Warning')
            self.disable()
            return

        # get time
        t1 = time.time()

        # check if target is updating
        target_val = self.pv['target'].get()

        # target is updating, update saved values
        if self.target_last != target_val:
            self.target_last = target_val
            self.t_target_last = t1

        # target has not been updated past the timeout duration
        elif (self.target_timeout_s > 0) and (t1-self.t_target_last > self.target_timeout_s):
            msg = f'"{self.EPICS_PV["target"]}" timeout! Value read back has been {target_val} for the last {t1 - self.t_target_last:.1f} seconds'
            self.client.trigger_internal_alarm('AutoStat', f'"{self.EPICS_PV["target"]}" timeout',
                                               default_alarm_class='Warning')
            self.client.msg(msg)
            self.disable()

        # new control value
        if t1-self.t0 >= self.time_step_s:

            # apply control operation
            val = self.pid(target_val)
            self.pv['ctrl'].put(val)
            self.t0 = t1

            # new t0 and htr setpoint value to check against
            self.t0 = t1
            self.last_setpoint = val

class PIDControllerBase_ZeroOnDisable_Panic(PIDControllerBase_ZeroOnDisable):
    """Class which includes panic state and zeroing on disable, which includes during panic state"""

    def __init__(self, client, name):
        super().__init__(client, name)
        self.panic_thresh = self.get_limited_var('target_high_thresh')
        self.panic_state = False
        self.t_panic = 0 # time at which we have panicked and opened safety valve

    def callback_main(self, client, path, idx, odb_value):
        """Add callback for target high threshold"""

        if '/target_high_thresh' in path:
            self.panic_thresh = self.limit_var('target_high_thresh', odb_value)
            client.msg(f'{self.name} target high threshold changed to {self.panic_thresh}')
        else:
            super().callback_main(client, path, idx, odb_value)

    def readout_func(self):
        """
        For a periodic equipment, this function will be called periodically
        (every 100ms in this case). It should return either a `cdms.event.Event`
        or None (if we shouldn't write an event).
        """

        # don't run if not enabled
        if not self.is_enabled:
            return

        # check that all devices are withing operating limits
        # exceptions to be made if in panic state
        if not self.panic_state and not self.check_device_states():
            self.ensure_set('ctrl', 0.0)
            self.last_setpoint = np.nan
            return

        # check if htr setpoint changed significantly between calls
        if not np.isnan(self.last_setpoint) and abs(self.pv['ctrl'].get() - self.last_setpoint) > 1:
            msg = f'"{self.EPICS_PV["ctrl"]}" setpoint ({self.pv["ctrl"].get():.0f}) '+\
                  f'does not match previously set value ({self.last_setpoint:.0f}) - disabling {self.name}'
            self.client.trigger_internal_alarm('AutoStat', msg,
                                               default_alarm_class='Warning')
            self.disable()
            return

        # get time
        t1 = time.time()

        # check if target is updating
        target_val = self.pv['target'].get()

        # target is updating, update saved values
        if self.target_last != target_val:
            self.target_last = target_val
            self.t_target_last = t1

        # target has not been updated past the timeout duration
        elif (self.target_timeout_s > 0) and (t1-self.t_target_last > self.target_timeout_s):
            msg = f'"{self.EPICS_PV["target"]}" timeout! Value read back has been {target_val} for the last {t1 - self.t_target_last:.1f} seconds'
            self.client.trigger_internal_alarm('AutoStat', f'"{self.EPICS_PV["target"]}" timeout',
                                               default_alarm_class='Warning')
            self.client.msg(msg)
            self.disable()

        # check if panic state
        if target_val > self.panic_thresh:

            if not self.panic_state:

                # get values before we do anything
                self.last_output = self.pv['ctrl'].get()

                # set the panic state stop the control variable
                self.ensure_set('ctrl', 0.0)
                self.last_setpoint = np.nan
                self.t_panic = time.time()
                self.panic_state = True
                self.client.msg(f'{self.name}: Target over threshold. Stopping control and setting {self.EPICS_PV["ctrl"]} to zero')

        # panicking: wait at least 30 s for the pressure to go down
        elif self.panic_state and (t1 - self.t_panic) > 30:

            # restore prev values
            self.pv['ctrl'].put(self.last_output*0.8)
            self.last_setpoint = self.last_output*0.8

            # stop panicking
            self.panic_state = False
            self.client.msg(f'{self.name}: Target back under threshold. Resuming PID control.')

        # new control value
        if t1-self.t0 >= self.time_step_s and not self.panic_state:

            # apply control operation
            val = self.pid(target_val)
            self.pv['ctrl'].put(val)

            # new t0 and htr setpoint value to check against
            self.t0 = t1
            self.last_setpoint = val
