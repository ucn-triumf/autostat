# Class for queuing and executing a sequence of cryostat control operations
# Derek Fujimoto
# May 2025

import midas, midas.client
from EpicsDevice import get_device
import time

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
    """

    # device prefixes
    prefix = {  '0': 'UCN2:ISO',
                '1': 'UCN2:HE3',
                '2': 'UCN2:HE4',
                '3': 'UCN2:LD2',
                '5': 'UCN2:CRY',
                '7': 'UCN2:UDG',
                '8': 'UCN2:VAC',
            }

    # variables for initial checks of cryo state

    # lists of status variables names
    devices_off = []        # pass if False
    devices_on = []         # pass if True

    # dict of name:threshold
    devices_below = {}      # pass if readback < threshold
    devices_above = {}      # pass if readback > threshold


    def __init__(self, scriptname):

        # initialization
        self._devices = {}   # name:EpicsDevice

        # make logger
        logger = logging.getLogger('cryoscript')
        logger.setLevel(logging.INFO)
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        # setup file handler with rotating file handling
        rfile_handler = RotatingFileHandler(f'{scriptname}.log', mode='a',
                                            maxBytes=5*1024*1024, backupCount=1,
                                            encoding=None, delay=False)
        rfile_handler.setFormatter(log_formatter)
        rfile_handler.setLevel(logging.INFO)
        logger.addHandler(rfile_handler)

        # connect to midas client
        self.client = midas.client.MidasClient(scriptname)

        # save
        self.scriptname = scriptname
        self.logger = logger

        self.log(f'Started {scriptname}')

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
            if self.device(name).is_off:
                msg = f'{name} is on/open when it should be off/closed!'
                all_good = False

        # devices should be off
        for name in self.devices_off:
            if self.device(name).is_on:
                msg = f'{name} is off/closed when it should be on/open!'
                all_good = False

        # devices below threshold
        for name, thresh in self.devices_below.items():
            if self.device(name).readback > thresh:
                msg = f'{name} is above threshold ({self.device(name).readback:.3f} > {thresh:.3f})'
                all_good = False

        # devices above threshold
        for name, thresh in self.devices_above.items():
            if self.device(name).readback < thresh:
                msg = f'{name} is below threshold ({self.device(name).readback:.3f} < {thresh:.3f})'
                all_good = False

        # bad exit
        if not all_good:
            self.log(msg, True)
            self.exit()
            raise RuntimeError(msg)
        else:
            self.log('All checks passed', False)

    def device(self, name):
        """Get a devices from self._devices, if doesn't exist then connect and return

        Notes:
            Can only connect to UCN2 devices (for security reasons)

        Args:
            name (str): name of device without prefix or suffix. Ex: "TS512"

        Returns
            EpicsDevice: connected device
        """

        # if exists in dictionary, then return that
        try:
            return self._devices[name]

        # doesn't exist: make EpicsDevice
        except KeyError:
            # find the prefix from leading value
            fullname = f'{self.prefix[name[-3]]}:name'

            # add to devices
            self._devices[name] = get_device(path=fullnane, logfn=self.log)

            return self._devices[name]

    def exit(self, state=None):
        """Put the system into a safe state upon error or exit

        Args:
            state: define system state to select between different exit strategies
        """
        pass
        self.client.disconnect()

    def run(self):
        """Run the script"""
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
        device = self.device(name)

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
        device = self.device(name)

        if device.readback > thresh:
            log(f'Waiting for {device.path} to drop below threshold {thresh} {device.readback_units}, currently {device.readback:.3f} {device.readback_units}')

            self.wait(condition = lambda : device.readback < thresh,
                      sleep_dt=sleep_dt,
                      print_dt=print_dt)

        self.log(f'{device.path} ({device.readback:.2f} {device.readback_units}) satisfies threshold of {thresh} {device.readback_units}')
