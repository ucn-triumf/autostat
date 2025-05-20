# Class for queuing and executing a sequence of cryostat control operations
# Derek Fujimoto
# May 2025

import midas, midas.client
from EpicsDevice import EpicsDeviceCollection
import time, logging
from logging.handlers import RotatingFileHandler

import midas
import midas.frontend
import epics
from simple_pid import PID
import time
import collections
import numpy as np

class CryoScript(midas.frontend.EquipmentBase):
    """Queue and execute a sequence of cryostat control operations

    Base class for most things

    Attributes:
        _devices (dict): dict of key:EpicsDevice to track connected devices
        client (midas.client): connect to midas server
        devices_above (dict): initial checklist of names:thresh (no prefix or suffix). Pass if greater than thresh
        devices_below (dict): initial checklist of names:thresh (no prefix or suffix). Pass if less than thresh
        devices_off (list): initial checklist of names (no prefix or suffix). Pass if off/closed
        devices_on (list): initial checklist of names (no prefix or suffix). Pass if on/open
        run_state: defines what state the system is in to better put the cryostat in a safe operation mode upon failure
    """

    # variables for initial checks of cryo state

    # lists of status variables names
    devices_off = []
    devices_on = []
    devices_closed = []
    devices_open = []

    # dict of name:threshold
    devices_below = {}      # pass if readback < threshold
    devices_above = {}      # pass if readback > threshold

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("timeout_s", 10),
        ('dry_run', False),
        ('wait_print_delay_s', 900),
        ("Enabled", False),
        ("_exit_with_error", False),    # if true, script exited unexpectedly
    ])

    def __init__(self, client, logger):
        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_PERIODIC
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 2323
        default_common.period_ms = 5000
        default_common.read_when = midas.RO_ALWAYS
        default_common.log_history = 5

        # You MUST call midas.frontend.EquipmentBase.__init__ in your equipment's __init__ method!
        midas.frontend.EquipmentBase.__init__(self, client, self.equip_name, default_common, self.DEFAULT_SETTINGS)

        # initialization
        self.logger = logger
        self.devices = EpicsDeviceCollection(self.log,
                                            timeout=self.timeout,
                                            dry_run=self.dry_run)

    def check_status(self):
        """Verify that the state of the system is as expected"""

        # devices should be on
        for name in sorted(self.devices_on):
            if self.devices[name].is_off:
                msg = f'{name} is off when it should be on'
                if self.dry_run:    self.log(msg)
                else:               raise RuntimeError(msg)

            elif self.dry_run:
                self.log(f'{name} is on, as it should')

        # devices should be off
        for name in sorted(self.devices_off):
            if self.devices[name].is_on:
                msg = f'{name} is on when it should be off'
                if self.dry_run:    self.log(msg)
                else:               raise RuntimeError(msg)

            elif self.dry_run:
                self.log(f'{name} is off, as it should')

        # devices should be closed
        for name in sorted(self.devices_closed):
            if self.devices[name].is_open:
                msg = f'{name} is open when it should be closed'
                if self.dry_run:    self.log(msg)
                else:               raise RuntimeError(msg)
            elif self.dry_run:
                self.log(f'{name} is closed, as it should')

        # devices should be open
        for name in sorted(self.devices_open):
            if self.devices[name].is_closed:
                msg = f'{name} is closed when it should be open'
                if self.dry_run:    self.log(msg)
                else:               raise RuntimeError(msg)
            elif self.dry_run:
                self.log(f'{name} is open, as it should')

        # devices below threshold
        for name, thresh in self.devices_below.items():
            val = self.devices[name].readback
            if val > thresh:
                msg = f'{name} is above threshold ({val:.3f} > {thresh:.3f})'
                if self.dry_run:    self.log(msg)
                else:               raise RuntimeError(msg)
            elif self.dry_run:
                self.log(f'{name} is below threshold ({val:.3f} < {thresh:.3f}), as it should')

        # devices above threshold
        for name, thresh in self.devices_above.items():
            val = self.devices[name].readback
            if val < thresh:
                msg = f'{name} is below threshold ({val:.3f} < {thresh:.3f})'
                if self.dry_run:    self.log(msg)
                else:               raise RuntimeError(msg)
            elif self.dry_run:
                self.log(f'{name} is above threshold ({val:.3f} > {thresh:.3f}), as it should')

        self.log(f'All checks passed', False)

    @property
    def dry_run(self):      return bool(self.client.odb_get(f'{self.odb_settings_dir}/dry_run'))
    @property
    def equip_name(self):   return self.__class__.__name__
    @property
    def timeout(self):      return self.settings['timeout_s']

    def exit(self):
        """Put the system into a safe state upon error or exit

        make use of the self.run_state variable to choose between exit strategies

        Args:
            state: define system state to select between different exit strategies
        """

        # must have the following to ensure that the sequencer knows to start the next script in the queue
        self.client.odb_set('/Equipment/CryoScriptSequencer/Settings/_script_is_running', False)

    def get_odb(self, path):
        return self.client.odb_get(path)

    def log(self, msg, is_error=False):

        # dry run message reformat
        if self.dry_run:
            msg = f'[DRY RUN] {msg}'

        # reformat msg to include name
        msg = f'[{self.equip_name}] {msg}'

        # dry run print
        if self.dry_run:
            print(msg)

        # send logging messages
        if is_error:
            self.logger.error(msg)

            # no alarms in a dry run
            if not self.dry_run:
                self.client.trigger_internal_alarm(self.program_name, msg,
                                                   default_alarm_class='Alarm')
        else:
            self.logger.info(msg)

        # no midas messages on dry run
        if not self.dry_run:
            try:
                self.client.msg(msg, is_error=is_error)
            except Exception as err:
                self.logger.error(f'MIDAS client failed to recieve message. Traceback: {err}')

    def readout_func(self):
        """
        For a periodic equipment, this function will be called periodically
        (every 100ms in this case). It should return either a `cdms.event.Event`
        or None (if we shouldn't write an event).
        """
        pass

    def run(self):
        """Run the script. Implement here the actions to take"""
        pass

    def set_odb(self, path, value):
        """Set ODB variable

        Args:
            path (str): odb path to variable which to set
            value: value to set
        """

        # dry run print
        if self.dry_run:
            self.log(f'Set {path} to {value}')
            return

        t0 = time.time()
        while self.client.odb_get(path) != value:
            # timeout
            if time.time()-t0 > self.timeout:
                raise TimeoutError(f'Attempted to set {path} for {self.timeout} seconds, stuck at {client.odb_get(path)}')

            self.client.odb_set(path, value)
            time.sleep(1)

        self.log(f'Set {path} to {value}')

    def detailed_settings_changed_func(self, path, idx, new_value):
        """
        You MAY implement this function in your derived class if you want to be
        told when a variable in /Equipment/<xxx>/Settings has changed.

        If you don't care about what changed (just that any setting has changed),
        implement `settings_changed_func()` instead,

        We will automatically update self.settings before calling this function,
        but you may want to implement this function to validate any settings
        the user has set, for example.

        It may return anything (we don't check it).

        Args:
            * path (str) - The ODB path that changed
            * idx (int) - If the entry is an array, the array element that changed
            * new_value (int/float/str etc) - The new ODB value (the single array
                element if it's an array that changed)
        """
        # new device collection if timeout or dry_run changed
        if 'timeout' in path or 'dry_run' in path:
            self.devices = EpicsDeviceCollection(self.log,
                                                timeout=self.timeout,
                                                dry_run=self.dry_run)

        # start run
        elif 'Enabled' in path and new_value:

            self.log(f'started')
            self.client.odb_set(f'{self.odb_settings_dir}/_exit_with_error', False)
            try:
                self.check_status()
                self.run()
            except Exception as err:
                self.log('Exiting with error!')
                self.client.odb_set(f'{self.odb_settings_dir}/_exit_with_error', True)

            else:
                self.run_state = None
                self.log('completed')

            finally:
                self.exit()
                self.client.odb_set(f'{self.odb_settings_dir}/Enabled', False)

    def wait(self, condition, printfn=None):
        """Pause execution until condition evaluates to True or Enabled is False

        Args:
            condition (function handle): function with prototype fn(), which returns True if execution should continue, else wait.
            printfn (function handle): function with prototype fn(), which returns the statement to log during the wait process. If not use a default statement. Example: lambda: 'Waiting...'
        """

        # dry run print
        if self.dry_run:
            self.log('Wait condition bypassed')
            return

        # print function
        if printfn is None:
            printfn = lambda : 'Condition not satisfied. Waiting...'

        t0 = time.time()
        while not condition() and self.settings['Enabled']:
            if (time.time()-t0) > self.settings['wait_print_delay_s']:
                t0 = time.time()
                self.log(printfn())

            # sleep 1s
            self.client.communicate(1000)

    def wait_until_greaterthan(self, name, thresh):
        """Block program execution until device readback is above the theshold

        Args:
            name (str): device name which should be above threshold
            thresh (float): threshold
        """
        device = self.devices[name]

        if device.readback < thresh:
            self.log(f'Waiting for {device.path} to rise above threshold {thresh} {device.readback_units}, currently {device.readback:.3f} {device.readback_units}')

            self.wait(condition=lambda : device.readback > thresh,
                      printfn=lambda : f'{device.path} below threshold, currently {device.readback:.3f} {device.readback_units}')

        self.log(f'{device.path} readback ({device.readback:.2f} {device.readback_units}) is greater than threshold of {thresh} {device.readback_units}')

    def wait_until_lessthan(self, name, thresh):
        """Block program execution until device readback is below the theshold

        Args:
            name (str): device name which should be below threshold
            thresh (float): threshold
        """
        device = self.devices[name]

        if device.readback > thresh:
            self.log(f'Waiting for {device.path} to drop below threshold {thresh} {device.readback_units}, currently {device.readback:.3f} {device.readback_units}')

            self.wait(condition=lambda : device.readback < thresh,
                      printfn=lambda : f'{device.path} above threshold, currently {device.readback:.3f} {device.readback_units}')

        self.log(f'{device.path} readback ({device.readback:.2f} {device.readback_units}) is less than threshold of {thresh} {device.readback_units}')
