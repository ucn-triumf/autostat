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

