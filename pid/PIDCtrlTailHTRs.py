# Various MIDAS equipment which use PID loops to control devices
# Derek Fujimoto
# Apr 2025
from PIDControllerBase import PIDControllerBase_Panic
import collections

class PIDCtrl_HTR001(PIDControllerBase_Panic):
    """PID_HTR001. Control HTR001 in order to set TS112"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 2000),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 2000),
                'output_limit_high': (0, 2000),
                'target_high_thresh': (0, 500),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:ISO:HTR001:CUR', # write access
                'target':           'UCN2:HE3:TS112:RDTEMPK',
                'htr_staton':       'UCN2:ISO:HTR001:STATON',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 640),
        ("I", 1),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 350),
        ("target_high_thresh", 373),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 2000),
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
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_HTR001')

class PIDCtrl_HTR003(PIDControllerBase_Panic):
    """PID_HTR003. Control HTR003 in order to set TS019"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 1700),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1700),
                'output_limit_high': (0, 1700),
                'target_high_thresh': (0, 500),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:ISO:HTR003:CUR', # write access
                'target':           'UCN2:ISO:TS019:RDTEMPK',
                'htr_staton':       'UCN2:ISO:HTR003:STATON',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 640),
        ("I", 1),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 350),
        ("target_high_thresh", 373),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1700),
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
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_HTR003')

class PIDCtrl_HTR004(PIDControllerBase_Panic):
    """PID_HTR004. Control HTR004 in order to set TS020"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 1700),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1700),
                'output_limit_high': (0, 1700),
                'target_high_thresh': (0, 500),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:ISO:HTR004:CUR', # write access
                'target':           'UCN2:ISO:TS020:RDTEMPK',
                'htr_staton':       'UCN2:ISO:HTR004:STATON',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 640),
        ("I", 1),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 350),
        ("target_high_thresh", 373),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1700),
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
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_HTR004')

class PIDCtrl_HTR005(PIDControllerBase_Panic):
    """PID_HTR005. Control HTR005 in order to set TS021"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 1700),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1700),
                'output_limit_high': (0, 1700),
                'target_high_thresh': (0, 500),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:ISO:HTR005:CUR', # write access
                'target':           'UCN2:ISO:TS021:RDTEMPK',
                'htr_staton':       'UCN2:ISO:HTR005:STATON',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 640),
        ("I", 1),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 350),
        ("target_high_thresh", 373),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1700),
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
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_HTR005')

class PIDCtrl_HTR006(PIDControllerBase_Panic):
    """PID_HTR006. Control HTR006 in order to set TS022"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 1700),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1700),
                'output_limit_high': (0, 1700),
                'target_high_thresh': (0, 500),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:ISO:HTR006:CUR', # write access
                'target':           'UCN2:ISO:TS022:RDTEMPK',
                'htr_staton':       'UCN2:ISO:HTR006:STATON',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 640),
        ("I", 1),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 350),
        ("target_high_thresh", 373),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1700),
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
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_HTR006')

class PIDCtrl_HTR007(PIDControllerBase_Panic):
    """PID_HTR007. Control HTR006 in order to set TS017"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 2200),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 2200),
                'output_limit_high': (0, 2200),
                'target_high_thresh': (0, 500),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:ISO:HTR007:CUR', # write access
                'target':           'UCN2:ISO:TS017:RDTEMPK',
                'htr_staton':       'UCN2:ISO:HTR007:STATON',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 640),
        ("I", 1),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 350),
        ("target_high_thresh", 373),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 2200),
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
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_HTR007')

class PIDCtrl_HTR008(PIDControllerBase_Panic):
    """PID_HTR008. Control HTR008 in order to set TS224"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 325),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 2200),
                'output_limit_high': (0, 2200),
                'target_high_thresh': (0, 350),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:ISO:HTR008:CUR', # write access
                'target':           'UCN2:HE4:TS224:RDTEMPK',
                'htr_staton':       'UCN2:ISO:HTR008:STATON',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 640),
        ("I", 1),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 300),
        ("target_high_thresh", 325),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 2200),
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
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_HTR008')