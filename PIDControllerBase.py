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
    LIMITS = {  'setpoint': (0, 1500),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1000),
                'output_limit_high': (0, 1000)}

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {}

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 1.0),
        ("I", 0.0),
        ("D", 0.0),
        ("setpoint", 1400),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1000),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
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
        self.client.odb_watch(f'{self.odb_settings_dir}/Enabled',
                              self.callback_enabled,
                              pass_changed_value_only=True)

        self.client.odb_watch(f'{self.odb_settings_dir}/P',
                              self.callback_P,
                              pass_changed_value_only=True)

        self.client.odb_watch(f'{self.odb_settings_dir}/I',
                              self.callback_I,
                              pass_changed_value_only=True)

        self.client.odb_watch(f'{self.odb_settings_dir}/D',
                              self.callback_D,
                              pass_changed_value_only=True)

        self.client.odb_watch(f'{self.odb_settings_dir}/setpoint',
                              self.callback_setpoint,
                              pass_changed_value_only=True)

        self.client.odb_watch(f'{self.odb_settings_dir}/proportional_on_measurement',
                              self.callback_prop_on_meas,
                              pass_changed_value_only=True)

        self.client.odb_watch(f'{self.odb_settings_dir}/differential_on_measurement',
                              self.callback_diff_on_meas,
                              pass_changed_value_only=True)

        self.client.odb_watch(f'{self.odb_settings_dir}/output_limit_low',
                              self.callback_out_lim_low,
                              pass_changed_value_only=True)

        self.client.odb_watch(f'{self.odb_settings_dir}/output_limit_high',
                              self.callback_out_lim_high,
                              pass_changed_value_only=True)

        self.client.odb_watch(f'{self.odb_settings_dir}/time_step_s',
                              self.callback_time_step,
                              pass_changed_value_only=True)

        # get epics readback variables to read and write
        # by default uses the monitor backend (desired)
        self.pv = {key: epics.PV(val) for key, val in self.EPICS_PV.items()}

        # setup PID controller
        # see https://simple-pid.readthedocs.io/en/latest/reference.html
        self.pid = PID(
            Kp = self.client.odb_get(f'{self.odb_settings_dir}/P'), # P
            Ki = self.client.odb_get(f'{self.odb_settings_dir}/I'), # I
            Kd = self.client.odb_get(f'{self.odb_settings_dir}/D'), # D
            setpoint = self.get_limited_var('setpoint'), # target pressure
            output_limits = (self.get_limited_var('output_limit_low'),
                             self.get_limited_var('output_limit_high')),
            proportional_on_measurement = self.client.odb_get(f'{self.odb_settings_dir}/proportional_on_measurement'),
            differential_on_measurement = self.client.odb_get(f'{self.odb_settings_dir}/differential_on_measurement'),
            starting_output = self.pv['ctrl'].get() # The starting point for the PID’s output.
            )
        self.last_setpoint = self.pv['ctrl'].get()
        self.time_step_s = self.get_limited_var('time_step_s')
        self.t0 = 0

        # You can set the status of the equipment (appears in the midas status page)
        if self.is_enabled:
            self.set_status("Running", status_color='greenLight')
        else:
            self.set_status("Ready, Disabled", status_color='yellowGreenLight')

        # check device states
        self.check_device_states()

    def callback_enabled(self, client, path, idx, odb_value):
        """Called when enable flag is changed"""
        if odb_value:
            self.set_status("Running", status_color='greenLight')
            client.msg(f'{self.name} has been enabled')
        else:
            self.set_status("Ready, Disabled", status_color='yellowGreenLight')
            client.msg(f'{self.name} has been disabled')

    def callback_P(self, client, path, idx, odb_value):
        self.pid.Kp = odb_value
        client.msg(f'{self.name} P value changed to {self.pid.Kp}')

    def callback_I(self, client, path, idx, odb_value):
        self.pid.Ki = odb_value
        client.msg(f'{self.name} I value changed to {self.pid.Ki}')

    def callback_D(self, client, path, idx, odb_value):
        self.pid.Kd = odb_value
        client.msg(f'{self.name} D value changed to {self.pid.Kd}')

    def callback_setpoint(self, client, path, idx, odb_value):
        self.pid.setpoint = self.limit_var('setpoint', odb_value)
        client.msg(f'{self.name} setpoint changed to {self.pid.setpoint}')

    def callback_prop_on_meas(self, client, path, idx, odb_value):
        self.pid.proportional_on_measurement = odb_value
        client.msg(f'{self.name} proportional_on_measurement changed to {self.pid.proportional_on_measurement}')

    def callback_diff_on_meas(self, client, path, idx, odb_value):
        self.pid.differential_on_measurement = odb_value
        client.msg(f'{self.name} differential_on_measurement changed to {self.pid.differential_on_measurement}')

    def callback_setpoint(self, client, path, idx, odb_value):
        self.pid.setpoint = self.limit_var('setpoint', odb_value)
        client.msg(f'{self.name} setpoint changed to {self.pid.setpoint}')

    def callback_out_lim_low(self, client, path, idx, odb_value):
        val0 = self.limit_var('output_limit_low', odb_value)
        val1 = client.odb_get(self.odb_settings_dir+'/output_limit_high')
        self.pid.output_limits = (val0, val1)
        client.msg(f'{self.name} output limits changed to {self.pid.output_limits}')

    def callback_out_lim_high(self, client, path, idx, odb_value):
        val0 = client.odb_get(self.odb_settings_dir+'/output_limit_low')
        val1 = self.limit_var('output_limit_high', odb_value)
        self.pid.output_limits = (val0, val1)
        client.msg(f'{self.name} output limits changed to {self.pid.output_limits}')

    def callback_time_step(self, client, path, idx, odb_value):
        self.time_step_s = self.limit_var('time_step_s', odb_value)
        client.msg(f'{self.name} time step changed to {self.time_step_s}')

    def check_device_states(self):
        """Check devices are set properly

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
                name_pretty = name.split("_")[0].upper()
                self.client.msg(f'"{name_pretty}" is above threshold ({lim})',
                                is_error=True)

        # these should be on
        for name, lim in self.DEVICE_THRESH_ON.items():
            if self.pv[name].get() < lim:
                state_ok = False
                name_pretty = name.split("_")[0].upper()
                self.client.msg(f'"{name_pretty}" is below threshold ({lim})',
                                is_error=True)

        # these should be off
        for name in self.DEVICE_STATE_OFF:
            if int(self.pv[name].get()):
                state_ok = False
                name_pretty = name.split("_")[0].upper()
                self.client.msg(f'"{name_pretty}" should not be in the ON state. Turn it OFF',
                                is_error=True)

        # these should be on
        for name in self.DEVICE_STATE_ON:
            if not int(self.pv[name].get()):
                state_ok = False
                name_pretty = name.split("_")[0].upper()
                self.client.msg(f'"{name_pretty}" should not be in the OFF state. Turn it ON',
                                is_error=True)

        # alarm on fail
        if not state_ok:
            msg = f'{self.name} failed device check. See messages.'
            self.client.trigger_internal_alarm('AutoStat', msg,
                                               default_alarm_class='Warning')
            self.disable()

        return state_ok

    def disable(self):
        """Set disable status in the event of program crash"""
        self.client.odb_set(self.odb_settings_dir + '/Enabled', False)
        self.set_status("Ready, Disabled", status_color='yellowGreenLight')

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

        # get time
        t1 = time.time()

        # new control value
        if t1-self.t0 >= self.time_step_s:

            # apply control operation
            val = self.pid(self.pv['target'].get())
            self.pv['ctrl'].put(val)
            self.t0 = t1

            # new t0 and htr setpoint value to check against
            self.t0 = t1
            self.last_setpoint = val
