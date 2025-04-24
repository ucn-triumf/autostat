# Various MIDAS equipment which use PID loops to control devices
# Derek Fujimoto
# Mar 2025
import midas
import midas.frontend
import epics
from PIDControllerBase import PIDControllerBase
import time
import numpy as np
import collections

class PIDCtrl_FPV205_TS505(PIDControllerBase):
    """PID_20KShield. Control FPV205 in order to set TS505"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 350),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 100),
                'output_limit_high': (0, 100)}

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             "UCN2:HE4:FPV205:POS",
                'target':           "UCN2:CRY:TS505:RDTEMPK",
                'FPV205_STATON':    "UCN2:HE4:FPV205:STATON",
               }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 1.0),
        ("I", 0.0),
        ("D", 0.0),
        ("inverted_output", True),
        ("target_setpoint", 20),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 100),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
        ("target_timeout_s", 30),
        ("control_pv", EPICS_PV['ctrl']),
        ("target_pv", EPICS_PV['target']),
    ])

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['FPV205_STATON']

    def __init__(self, client):
        super().__init__(client, 'PID_20KShield')

class PIDCtrl_FPV206_TS525(PIDControllerBase):
    """PID_ECollar. Control FPV206 in order to set TS525"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 350),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 100),
                'output_limit_high': (0, 100)}

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             "UCN2:HE4:FPV206:POS",
                'target':           "UCN2:CRY:TS525:RDTEMPK",
                'FPV206_STATON':    "UCN2:HE4:FPV206:STATON",
               }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 1.0),
        ("I", 0.0),
        ("D", 0.0),
        ("inverted_output", True),
        ("target_setpoint", 30),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 100),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
        ("target_timeout_s", 30),
        ("control_pv", EPICS_PV['ctrl']),
        ("target_pv", EPICS_PV['target']),
    ])

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['FPV206_STATON']

    def __init__(self, client):
        super().__init__(client, 'PID_ECollar')

class PIDCtrl_FPV207_TS508(PIDControllerBase):
    """PID_100KShield. Control FPV207 in order to set TS508"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 350),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 100),
                'output_limit_high': (0, 100)}

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             "UCN2:HE4:FPV207:POS",
                'target':           "UCN2:CRY:TS508:RDTEMPK",
                'FPV207_STATON':    "UCN2:HE4:FPV207:STATON",
               }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 1.0),
        ("I", 0.0),
        ("D", 0.0),
        ("inverted_output", True),
        ("target_setpoint", 100),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 100),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
        ("target_timeout_s", 30),
        ("control_pv", EPICS_PV['ctrl']),
        ("target_pv", EPICS_PV['target']),
    ])

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['FPV207_STATON']

    def __init__(self, client):
        super().__init__(client, 'PID_100KShield')

class PIDCtrl_FPV209_TS351(PIDControllerBase):
    """PID_Wall2Temp. Control FPV209 in order to set TS351"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 350),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 100),
                'output_limit_high': (0, 100)}

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             "UCN2:HE4:FPV209:POS",
                'target':           "UCN2:LD2:TS351:RDTEMPK",
                'FPV209_STATON':    "UCN2:HE4:FPV209:STATON",
               }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 1.0),
        ("I", 0.0),
        ("D", 0.0),
        ("inverted_output", True),
        ("target_setpoint", 100),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 100),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
        ("target_timeout_s", 30),
        ("control_pv", EPICS_PV['ctrl']),
        ("target_pv", EPICS_PV['target']),
    ])

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['FPV209_STATON']

    def __init__(self, client):
        super().__init__(client, 'PID_Wall2Temp')

class PIDCtrl_FPV212_TS245(PIDControllerBase):
    """PID_TransLineTemp. Control FPV212 in order to set TS245"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 350),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 100),
                'output_limit_high': (0, 100)}

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             "UCN2:HE4:FPV212:POS",
                'target':           "UCN2:HE4:TS245:RDTEMPK",
                'FPV212_STATON':    "UCN2:HE4:FPV212:STATON",
               }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 3.0),
        ("I", 0.0),
        ("D", 0.0),
        ("inverted_output", True),
        ("target_setpoint", 80),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 100),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
        ("target_timeout_s", 30),
        ("control_pv", EPICS_PV['ctrl']),
        ("target_pv", EPICS_PV['target']),
    ])

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['FPV212_STATON']

    def __init__(self, client):
        super().__init__(client, 'PID_TransLineTemp')

class PIDCtrl_HTR204_PT206(PIDControllerBase):
    """PID_4KPressure (autopurify). Control HTR204 in order to set PT206"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 1500),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1000),
                'output_limit_high': (0, 1000),
                'pt206_pressure_high_thresh': (0, 1500),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:HE4:HTR204:CUR', # write access
                'target':           'UCN2:HE4:PT206:RDPRESS',
                'htr204_staton':    'UCN2:HE4:HTR204:STATON',
                'fpv201_pos':       'UCN2:HE4:FPV201:POS',
                'fpv201_staton':    'UCN2:HE4:FPV201:STATON',
                'fpv201_read':      'UCN2:HE4:FPV201:RDDACP',
                'fpv202_read':      'UCN2:HE4:FPV202:RDDACP',
                'fpv203_read':      'UCN2:HE4:FPV203:RDDACP',
                'fpv204_read':      'UCN2:HE4:FPV204:RDDACP',
                'fpv205_read':      'UCN2:HE4:FPV205:RDDACP',
                'fpv206_read':      'UCN2:HE4:FPV206:RDDACP',
                'fpv207_read':      'UCN2:HE4:FPV207:RDDACP',
                'fpv208_read':      'UCN2:HE4:FPV208:RDDACP',
                'fpv209_read':      'UCN2:HE4:FPV209:RDDACP',
                'fpv211_read':      'UCN2:HE4:FPV211:RDDACP',
                'fpv212_read':      'UCN2:HE4:FPV212:RDDACP',
                'av203_staton':     'UCN2:HE4:AV203:STATON',
                'fpv211_staton':    'UCN2:HE4:FPV211:STATON',
                'fpv211autofill_staton': 'UCN2:HE4:FPV211:STAT.B8'}

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 0.9),
        ("I", 0.05),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 1400),
        ("pt206_pressure_high_thresh", 1480),
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
    DEVICE_THRESH_OFF= {'fpv201_read': 20,
                        'fpv202_read': 10,
                        'fpv204_read': 10,
                        'fpv205_read': 10,
                        'fpv206_read': 10,
                        'fpv207_read': 10,
                        'fpv208_read': 10,
                        'fpv211_read': 2,
                        'fpv212_read': 101}

    # readbacks should be above a threshold value (float)
    DEVICE_THRESH_ON = {'fpv203_read':80,
                        'fpv209_read':20}

    # the state of these devices should be off (boolean 0)
    DEVICE_STATE_OFF = ['av203_staton',
                        'fpv211autofill_staton',
                        'fpv211_staton']

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = [ 'htr204_staton',
                        'fpv201_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_4KPressure')

        self.panic_thresh = self.get_limited_var('pt206_pressure_high_thresh')
        self.panic_state = False
        self.t_panic = 0 # time at which we have panicked and opened safety valve
        self.fpv201_setpt = self.pv['fpv201_pos'].get() # current setpoint of fpv201, for reset

        self.client.odb_watch(f'{self.odb_settings_dir}/pt206_pressure_high_thresh',
                              self.callback_press_high_thresh,
                              pass_changed_value_only=True)

    def callback_press_high_thresh(self, client, path, idx, odb_value):
        self.panic_thresh = self.limit_var('pt206_pressure_high_thresh', odb_value)
        client.msg(f'{self.name} pressure high threshold changed to {self.panic_thresh}')

    def disable(self):
        self.ensure_set('ctrl', 0.0)
        super().disable()

    def ensure_set(self, setname, val):
        """Ensure value is set by checking the readback periodically after set

        Args:
            setname (str): name of the variable to set, without full path
            readname (str): name of the variable to read, without full path
            val (float): value to set
        """

        # time between set attempts in seconds
        delay = 1

        # number of attempts limit
        nlimit = 10
        n = 0

        # try to repeatedly set the value
        while abs(self.pv[setname].get() - val) > 1:
            time.sleep(delay)
            self.pv[setname].put(val)
            n += 1

            if n > nlimit:
                msg = f'{self.name}: Cannot set {setname} to {val}. Tried {nlimit} attempts. Consider setting manually.'
                n = 0
                self.client.trigger_internal_alarm('AutoStat', msg,
                                               default_alarm_class='Warning')

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
            msg = f'HTR204 setpoint ({self.pv["ctrl"].get():.0f}) does not match '+\
                  f'previously set value ({self.last_setpoint:.0f}) - disabling {self.name}'
            self.ensure_set('ctrl', 0.0)
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
        elif (self.target_timeout_s > 0) and (t1 - self.t_target_last > self.target_timeout_s):
            msg = f'"{self.EPICS_PV["target"]}" timeout! Value read back has been {target_val} for the last {t1 - self.t_target_last} seconds'
            self.client.trigger_internal_alarm('AutoStat', f'"{self.EPICS_PV["target"]}" timeout',
                                               default_alarm_class='Warning')
            self.client.msg(msg)
            self.disable()

        # check if panic state
        if target_val > self.panic_thresh:

            if not self.panic_state:

                # get values before we do anything
                self.fpv201_setpt = self.pv['fpv201_pos'].get()
                self.last_output = self.pv['ctrl'].get()

                # set the panic state, open valves and stop the heater
                self.pv['fpv201_pos'].put(100)
                self.ensure_set('ctrl', 0.0)
                self.last_setpoint = np.nan
                self.t_panic = time.time()
                self.panic_state = True
                self.client.msg(f'PT206 pressure too high ({target_val:.1f} > {self.panic_thresh})! Opening FPV201 to 100%')

        # panicking: wait at least 30 s for the pressure to go down
        elif self.panic_state and (t1 - self.t_panic) > 30:

            # restore prev values
            self.pv['fpv201_pos'].put(self.fpv201_setpt)
            self.pv['ctrl'].put(self.last_output*0.8)
            self.last_setpoint = self.last_output*0.8

            # stop panicking
            self.panic_state = False
            self.client.msg(f'PT206 pressure back under control! Setting FPV201 to {self.fpv201_setpt:.0f}%')

        # new control value
        if t1-self.t0 >= self.time_step_s and not self.panic_state:

            # apply control operation
            val = self.pid(target_val)
            self.pv['ctrl'].put(val)

            # new t0 and htr setpoint value to check against
            self.t0 = t1
            self.last_setpoint = val

