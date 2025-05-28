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

class PIDCtrl_NV101_FM101(PIDControllerBase):
    """PID_TransLineTemp. Control FPV212 in order to set TS245"""

    # settable limits
    LIMITS = {  'target_setpoint': (0, 500),
                'time_step_s': (30, 900),
                'output_limit_low': (0, 90),
                'output_limit_high': (0, 90),
                'min_NV_step': (0, 100),
                'percent_error_allowed': (0, 100),
                'average_last_s': (0, 900),
                }

    # devices/indicators from epics to monitor or write to
    # ctrl: the device to control directly
    # target: the device whose value should be approaching the setpoint
    EPICS_PV = {'ctrl':             "UCN2:HE3:NV101:POS",
                'ctrl_rdbk':        "UCN2:HE3:NV101:RDACP",
                'ctrl_domove':      "UCN2:HE3:NV101:DRVON",
                'ctrl_ismove':      "UCN2:HE3:NV101:STATON",
                'target':           "UCN2:HE3:FM101:RDFLOW",
                'staton':           "UCN2:HE3:NV101:STATDRV",
               }

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),
        ("P", 3.0),
        ("I", 0.0),
        ("D", 0.0),
        ("inverted_output", False),
        ("target_setpoint", 20),
        ("time_step_s", 60),            # time between set actions
        ("average_last_s", 30),         # average over the last x seconds to reduce noise
        ("percent_error_allowed", 5),   # target must be at least x% from its setpoint before trying to move NV
        ("min_NV_step", 0.1),           # minimum change in NV position
        ("NV_move_timeout_s", 30),      # duration before alarm is raised that NV failed to move
        ("output_limit_low", 0),
        ("output_limit_high", 90),
        ("proportional_on_measurement", False),
        ("differential_on_measurement", False),
        ("target_timeout_s", 30),
        ("control_pv", EPICS_PV['ctrl']),
        ("target_pv", EPICS_PV['target']),
    ])

    def __init__(self, client):
        super().__init__(client, 'PID_NV101')

        # for averaging values
        self.times = []
        self.values = []
        self.idx = 0
        self.average_last_s = self.get_limited_var('average_last_s')

    def detailed_settings_changed_func(self, path, idx, odb_value):

        super().detailed_settings_changed_func(path, idx, odb_value)

        if '/average_last_s' in path:
            self.average_last_s = self.limit_var(average_last_s, odb_value)
            self.client.msg(f'{self.name} average_last_s changed to {self.average_last_s}')

        elif '/percent_error_allowed' in path:
            self.settings["percent_error_allowed"] = self.limit_var('percent_error_allowed', odb_value)
            self.client.msg(f'{self.name} percent_error_allowed changed to {self.settings["percent_error_allowed"]}')

        elif '/min_NV_step' in path:
            self.settings["min_NV_step"] = self.limit_var(min_NV_step, odb_value)
            self.client.msg(f'{self.name} min_NV_step changed to {self.settings["min_NV_step"]}')

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

        # # check if setpoint changed significantly between calls
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
        self.check_target_timeout(t1, target_val)

        # average the last average_last_s values ----------

        # first entry
        if len(self.times) == 0:
            self.times.append(t1)
            self.values.append(target_val)

        # check if current index is earlier than the limit
        elif t1 - self.times[self.idx] > self.average_last_s:
            self.times[self.idx] = t1
            self.values[self.idx] = target_val
            self.idx = (self.idx + 1) % len(self.times)

        else:
            self.times.append(t1)
            self.values.append(target_val)

        # timestep check
        if t1-self.t0 >= self.time_step_s:

            # check device status
            is_ready = bool(self.pv['staton'].get())

            # check the threshold for updating the needle setpoint
            readback = np.mean(self.values)
            percent_error = abs(readback - self.pid.setpoint) / self.pid.setpoint * 100
            outside_target =  percent_error > self.settings['percent_error_allowed']

            # setpoint is not the same
            val = self.pid(readback)
            setpoint_has_changed = abs(self.last_setpoint - val) > 0.1

            # apply control operation -----
            if outside_target and setpoint_has_changed and is_ready:
                self.pv['ctrl'].put(val)
                self.last_setpoint = val

                # ensure that the valve moves
                t0_move = time.time()
                while abs(self.pv['ctrl_rdbk'].get() - val) > self.settings['min_NV_step']:

                    # rapid clicks until move starts
                    while not self.pv['ctrl_ismove'].get():

                        # timeout
                        if time.time() - t0_move > self.settings['NV_move_timeout_s']:
                            self.client.trigger_internal_alarm('AutoStat', 'NV101 move timeout')
                            self.client.odb_set(f'{self.odb_settings_dir}/Enabled', False)
                            return

                        # move
                        self.pv['ctrl_domove'].put(1)

                    # it's moving... wait
                    time.sleep(5)

                # reset averaging
                self.times = []
                self.values = []
                self.idx = 0


                # new t0 to check against
                self.t0 = t1