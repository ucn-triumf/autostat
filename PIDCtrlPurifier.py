# Various MIDAS equipment which use PID loops to control devices
# Derek Fujimoto
# Mar 2025
from PIDControllerBase import PIDControllerBase_ZeroOnDisable
import collections

class PIDCtrl_HTR105_TS510(PIDControllerBase_ZeroOnDisable):
    """PID_PUR_HE70K. Control purifier HTR105 in order to set TS510"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 1480),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1480),
                'output_limit_high': (0, 1480),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:HE3:HTR105:CUR', # write access
                'target':           'UCN2:CRY:TS510:RDTEMPK',
                'htr_staton':       'UCN2:HE3:HTR105:STATON',
                'htr_statloc':      'UCN2:HE3:HTR105:STATLOC',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 0.9),
        ("I", 0.04),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 70),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1480),
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
    DEVICE_STATE_OFF = ['htr_statloc']

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_PUR_HE70K')

class PIDCtrl_HTR010_TS512(PIDControllerBase_ZeroOnDisable):
    """PID_PUR_ISO70K. Control purifier HTR010 in order to set TS512"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 1480),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1480),
                'output_limit_high': (0, 1480),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:ISO:HTR010:CUR', # write access
                'target':           'UCN2:CRY:TS512:RDTEMPK',
                'htr_staton':       'UCN2:ISO:HTR010:STATON',
                'htr_statloc':      'UCN2:ISO:HTR010:STATLOC',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 0.9),
        ("I", 0.04),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 70),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1480),
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
    DEVICE_STATE_OFF = ['htr_statloc']

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_PUR_ISO70K')

class PIDCtrl_HTR107_TS511(PIDControllerBase_ZeroOnDisable):
    """PID_PUR_HE20K. Control purifier HTR107 in order to set TS511"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 1480),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1480),
                'output_limit_high': (0, 1480),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:HE3:HTR107:CUR', # write access
                'target':           'UCN2:CRY:TS511:RDTEMPK',
                'htr_staton':       'UCN2:HE3:HTR107:STATON',
                'htr_statloc':      'UCN2:HE3:HTR107:STATLOC',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 0.9),
        ("I", 0.04),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 20),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1480),
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
    DEVICE_STATE_OFF = ['htr_statloc']

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_PUR_HE20K')

class PIDCtrl_HTR012_TS513(PIDControllerBase_ZeroOnDisable):
    """PID_PUR_ISO20K. Control purifier HTR012 in order to set TS513"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 1480),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 1480),
                'output_limit_high': (0, 1480),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             'UCN2:ISO:HTR012:CUR', # write access
                'target':           'UCN2:CRY:TS513:RDTEMPK',
                'htr_staton':       'UCN2:ISO:HTR012:STATON',
                'htr_statloc':      'UCN2:ISO:HTR012:STATLOC',
                }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 0.9),
        ("I", 0.04),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 20),
        ("time_step_s", 10),
        ("output_limit_low", 0),
        ("output_limit_high", 1480),
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
    DEVICE_STATE_OFF = ['htr_statloc']

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['htr_staton']

    def __init__(self, client):
        super().__init__(client, 'PID_PUR_ISO20K')

