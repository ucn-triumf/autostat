# Class for queuing and executing a sequence of cryostat control operations
# Derek Fujimoto
# May 2025

import midas, midas.client
from EpicsDevice import EpicsDeviceCollection
import time, logging
from logging.handlers import RotatingFileHandler

class CryoScript(object):
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

    Args:
        timeout (int): duration in seconds before raising timeout exeception
        dry_run (bool): if true, instead of performing actions print action to screen

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

    # don't change this unless you want to pollute the ODB programs directory
    program_name = 'CryoScript'

    def __init__(self, timeout=10, dry_run=False):

        # make logger
        self.logger = logging.getLogger(self.program_name)
        self.logger.setLevel(logging.INFO)
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        # setup file handler with rotating file handling
        rfile_handler = RotatingFileHandler(f'{self.program_name}.log', mode='a',
                                            maxBytes=5*1024*1024, backupCount=1,
                                            encoding=None, delay=False)
        rfile_handler.setFormatter(log_formatter)
        rfile_handler.setLevel(logging.INFO)

        # only add handler if it doesn't exist already
        add_handler = True
        for handler in self.logger.handlers:
            if handler.baseFilename == rfile_handler.baseFilename:
                add_handler = False
                break

        if add_handler:
            self.logger.addHandler(rfile_handler)

        # connect to midas client
        self.client = midas.client.MidasClient(self.program_name)

        # initialization
        self.devices = EpicsDeviceCollection(self.log, timeout=timeout, dry_run=dry_run)
        self.timeout = timeout
        self.dry_run = dry_run
        self.run_state = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):

        # put cryo in a safe state
        if exc_type is not None:
            self.log(str(exc_value), is_error=True)
            self.exit()

        # disconnect from midas client
        self.client.disconnect()

        # wait period
        time.sleep(1)

        return

    def __call__(self, *args, **kwargs):
        self.log(f'started')
        self.check_status()
        self.run(*args, **kwargs)
        self.log(f'completed')

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

        # bad exit
        self.log(f'All checks passed', False)

    @property
    def name(self):
        return self.__class__.__name__

    def exit(self):
        """Put the system into a safe state upon error or exit

        make use of the self.run_state variable to choose between exit strategies

        Args:
            state: define system state to select between different exit strategies
        """
        pass

    def get_odb(self, path):

        nattempts = 0

        while nattempts < 2:
            try:
                return self.client.odb_get(path)

            # try reconnecting
            except midas.MidasError as err:
                self.client = midas.client.MidasClient(self.program_name)
                time.sleep(1)
                nattempts += 1

    def log(self, msg, is_error=False):

        # dry run message reformat
        if self.dry_run:
            msg = f'[DRY RUN] {msg}'

        # reformat msg to include name
        msg = f'[{self.name}] {msg}'

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

    def run(self):
        """Run the script

        Notes:
            This function is called inside of self.__call__() as a conveniance wrapper
            Define self.run_state and self.exit() to exit safely on crash or error
            Error messages are caught by self.__exit__() and are automatically logged
            Best practice is to run inside of "with" statement
        """
        pass

    def set_odb(self, path, value, timeout=10, exit_strategy=None):
        """Set ODB variable

        Args:
            path (str): odb path to variable which to set
            value: value to set
            timeout (int): timeout in seconds for setting the variable
            exit_strategy: passed to self.exit
        """

        # dry run print
        if self.dry_run:
            self.log(f'Set {path} to {value}')
            return

        t0 = time.time()
        while self.client.odb_get(path) != value:
            # timeout
            if time.time()-t0 > timeout:
                raise TimeoutError(f'Attempted to set {path} for {timeout} seconds, stuck at {client.odb_get(path)}')

            self.client.odb_set(path, value)
            time.sleep(1)

        self.log(f'Set {path} to {value}')

    def wait(self, condition, printfn=None, sleep_dt=60, print_dt=900):
        """Pause execution until condition evaluates to True

        Args:
            condition (function handle): function with prototype fn(), which returns True if execution should continue, else wait.
            printfn (function handle): function with prototype fn(), which returns the statement to log during the wait process. If not use a default statement. Example: lambda: 'Waiting...'
            sleep_dt (int): number of seconds to sleep before checking the condition again
            print_dt (int): number of seconds between print statement
        """

        # dry run print
        if self.dry_run:
            self.log('Wait condition bypassed')
            return

        # print function
        if printfn is None:
            printfn = lambda : 'Condition not satisfied. Waiting...'

        t0 = time.time()
        while not condition():
            if (time.time()-t0) > print_dt:
                t0 = time.time()
                self.log(printfn())

            time.sleep(sleep_dt)

    def wait_until_greaterthan(self, name, thresh, sleep_dt=60, print_dt=900):
        """Block program execution until device readback is above the theshold

        Args:
            name (str): device name which should be above threshold
            thresh (float): threshold
            sleep_dt (int): number of seconds to sleep before checking the condition again
            print_dt (int): number of seconds between print statement
        """
        device = self.devices[name]

        if device.readback < thresh:
            self.log(f'Waiting for {device.path} to rise above threshold {thresh} {device.readback_units}, currently {device.readback:.3f} {device.readback_units}')

            self.wait(condition=lambda : device.readback > thresh,
                      printfn=lambda : f'{device.path} below threshold, currently {device.readback:.3f} {device.readback_units}',
                      sleep_dt=sleep_dt,
                      print_dt=print_dt)

        self.log(f'{device.path} readback ({device.readback:.2f} {device.readback_units}) is greater than threshold of {thresh} {device.readback_units}')

    def wait_until_lessthan(self, name, thresh, sleep_dt=60, print_dt=900):
        """Block program execution until device readback is below the theshold

        Args:
            name (str): device name which should be below threshold
            thresh (float): threshold
            sleep_dt (int): number of seconds to sleep before checking the condition again
            print_dt (int): number of seconds between print statement
        """
        device = self.devices[name]

        if device.readback > thresh:
            self.log(f'Waiting for {device.path} to drop below threshold {thresh} {device.readback_units}, currently {device.readback:.3f} {device.readback_units}')

            self.wait(condition=lambda : device.readback < thresh,
                      printfn=lambda : f'{device.path} above threshold, currently {device.readback:.3f} {device.readback_units}',
                      sleep_dt=sleep_dt,
                      print_dt=print_dt)

        self.log(f'{device.path} readback ({device.readback:.2f} {device.readback_units}) is less than threshold of {thresh} {device.readback_units}')
