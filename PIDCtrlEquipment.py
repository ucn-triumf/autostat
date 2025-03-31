# Various MIDAS equipment which use PID loops to control devices
# Derek Fujimoto
# Mar 2025
import midas
import midas.frontend
import epics
from PIDControllerBase import PIDControllerBase
import time
import collections

class PIDCtrl_FPV212_TS245(PIDControllerBase):
    """Control FPV212 in order to set TS245"""

    # settable limits
    LIMITS = {  'setpoint': (0, 350),
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
        ("P", 1.0),
        ("I", 0.0),
        ("D", 0.0),
        ("setpoint", 100),
        ("time_step_s", 250),
        ("output_limit_low", 0),
        ("output_limit_high", 100),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
    ])

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['FPV212_STATON']

    def __init__(self, client):
        super().__init__(client, 'PID_TransLineTemp')

class PIDCtrl_FPV209_TS351(PIDControllerBase):
    """Control FPV209 in order to set TS351"""

    # settable limits
    LIMITS = {  'setpoint': (0, 350),
                'time_step_s': (0, 500),
                'output_limit_low': (0, 100),
                'output_limit_high': (0, 100)}

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             "UCN2:HE4:FPV209:POS",
                'target':           "UCN2:HE4:TS351:RDTEMPK",
                'FPV209_STATON':    "UCN2:HE4:FPV209:STATON",
               }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 1.0),
        ("I", 0.0),
        ("D", 0.0),
        ("setpoint", 100),
        ("time_step_s", 250),
        ("output_limit_low", 0),
        ("output_limit_high", 100),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
    ])

    # the state of these devices should be on (boolean 1)
    DEVICE_STATE_ON = ['FPV209_STATON']

    def __init__(self, client):
        super().__init__(client, 'PID_Wall2Temp')


