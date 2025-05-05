# Class for queuing and executing a sequence of cryostat control operations
# Derek Fujimoto
# May 2025

import midas, midas.client
from EpicsDevice import EpicsDeviceCollection
import time, logging
from logging.handlers import RotatingFileHandler

# timeout error when turning stuff on/off
class TimeoutError(Exception): pass

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
        scriptname (str): name of this class
    """

    # variables for initial checks of cryo state

    # lists of status variables names
    devices_off = []        # pass if False
    devices_on = []         # pass if True

    # dict of name:threshold
    devices_below = {}      # pass if readback < threshold
    devices_above = {}      # pass if readback > threshold

    def __init__(self):

        self.scriptname = __class__.__name__

        # make logger
        self.logger = logging.getLogger('cryoscript')
        self.logger.setLevel(logging.INFO)
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        # setup file handler with rotating file handling
        rfile_handler = RotatingFileHandler(f'{self.scriptname}.log', mode='a',
                                            maxBytes=5*1024*1024, backupCount=1,
                                            encoding=None, delay=False)
        rfile_handler.setFormatter(log_formatter)
        rfile_handler.setLevel(logging.INFO)
        self.logger.addHandler(rfile_handler)

        # connect to midas client
        self.client = midas.client.MidasClient(self.scriptname)

        # initialization
        self.devices = EpicsDeviceCollection(self.log)
        self.run_state = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):

        # put cryo in a safe state
        if exc_type is not None:
            self.exit()

        # disconnect from midas client
        self.client.disconnect()

    def log(self, msg, is_error=False):
        # send logging messages
        if is_error:
            logger.error(msg)
            self.client.trigger_internal_alarm(self.scriptname, msg,
                                        default_alarm_class='Alarm')
        else:
            logger.info(msg)
        self.client.msg(msg, is_error=is_error)

    def check_status(self):
        """Verify that the state of the system is as expected"""

        all_good = True

        # devices should be on
        for name in self.devices_on:
            if self.devices[name].is_off:
                msg = f'{name} is on/open when it should be off/closed!'
                all_good = False

        # devices should be off
        for name in self.devices_off:
            if self.devics[name].is_on:
                msg = f'{name} is off/closed when it should be on/open!'
                all_good = False

        # devices below threshold
        for name, thresh in self.devices_below.items():
            if self.devices[name].readback > thresh:
                msg = f'{name} is above threshold ({self.devices[name].readback:.3f} > {thresh:.3f})'
                all_good = False

        # devices above threshold
        for name, thresh in self.devices_above.items():
            if self.devices[name].readback < thresh:
                msg = f'{name} is below threshold ({self.devices[name].readback:.3f} < {thresh:.3f})'
                all_good = False

        # bad exit
        if not all_good:
            self.log(msg, True)
            self.exit()
            raise RuntimeError(msg)
        else:
            self.log('All checks passed', False)

    def exit(self):
        """Put the system into a safe state upon error or exit

        make use of the self.run_state variable to choose between exit strategies

        Args:
            state: define system state to select between different exit strategies
        """
        pass

    def run(self):
        """Run the script"""
        self.log(f'Started {self.scriptname}')
        pass

    def set_odb(path, value, timeout=10, exit_strategy=None):
        """Set ODB variable

        Args:
            path (str): odb path to variable which to set
            value: value to set
            timeout (int): timeout in seconds for setting the variable
            exit_strategy: passed to self.exit
        """
        t0 = time.time()
        while self.client.odb_get(path) != value:
            # timeout
            if time.time()-t0 > timeout:
                msg = f'Attempted to set {path} for {timeout} seconds, stuck at {client.odb_get(path)}'
                self.log(msg, True)
                self.exit(exit_strategy)
                raise TimeoutError(msg)

            client.odb_set(path, value)
            time.sleep(1)
        self.log(f'Set {path} to {value}')

    def wait(self, condition, sleep_dt=60, print_dt=900):
        """Pause execution until condition evaluates to True

        Args:
            condition (function handle): function with prototype fn(), which returns True if execution should continue, else wait.
            sleep_dt (int): number of seconds to sleep before checking the condition again
            print_dt (int): number of seconds between print statement
        """
        t0 = 0
        while not condition():
            if (time.time()-t0) > print_dt:
                t0 = time.time()
                self.log('Condition not satisfied. Waiting...')

            time.sleep(sleep_dt)

    def wait_until_greaterthan(name, thresh, sleep_dt=60, print_dt=900):
        """Block program execution until device readback is above the theshold

        Args:
            name (str): device name which should be above threshold
            thresh (float): threshold
            sleep_dt (int): number of seconds to sleep before checking the condition again
            print_dt (int): number of seconds between print statement
        """
        device = self.devices[name]

        if device.readback > thresh:
            log(f'Waiting for {device.path} to drop above threshold {thresh} {device.readback_units}, currently {device.readback:.3f} {device.readback_units}')

            self.wait(condition = lambda : device.readback < thresh,
                      sleep_dt=sleep_dt,
                      print_dt=print_dt)

        self.log(f'{device.path} ({device.readback:.2f} {device.readback_units}) satisfies threshold of {thresh} {device.readback_units}')

    def wait_until_lessthan(name, thresh, sleep_dt=60, print_dt=900):
        """Block program execution until device readback is below the theshold

        Args:
            name (str): device name which should be below threshold
            thresh (float): threshold
            sleep_dt (int): number of seconds to sleep before checking the condition again
            print_dt (int): number of seconds between print statement
        """
        device = self.devices[name]

        if device.readback > thresh:
            log(f'Waiting for {device.path} to drop below threshold {thresh} {device.readback_units}, currently {device.readback:.3f} {device.readback_units}')

            self.wait(condition = lambda : device.readback < thresh,
                      sleep_dt=sleep_dt,
                      print_dt=print_dt)

        self.log(f'{device.path} ({device.readback:.2f} {device.readback_units}) satisfies threshold of {thresh} {device.readback_units}')
