# Class for queuing and executing a sequence of cryostat control operations
# Derek Fujimoto
# May 2025

import midas, midas.client, midas.frontend
import json
from EpicsDevice import EpicsDeviceCollection
import time, logging
from logging.handlers import RotatingFileHandler
import collections
# TODO: test changing of variable mid-run

class CryoScriptSequencer(midas.frontend.EquipmentBase):
    """Queue and execute a sequence of cryostat scripts"""

    QUEUE_MAX_LEN = 64

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),     # if true execute the scripts in the queue
        ("dry_run", False),     # if true, don't log messages to MIDAS
        ("_functions", ['']*64),# list of function/equipment names
        ("_inputs", ['']*64),   # parametrs to pass to equipment
        ("_current", -1),       # index of currently running equipment
        ("_script_is_running", False), # is the script still in the middle of execution?
        ("_queue_length", 0),   # number of queued scripts
        ("_nloops", 0),         # number of loops of the queue remaining
    ])

    def __init__(self, client):
        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_PERIODIC
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 2323
        default_common.period_ms = 5000
        default_common.read_when = midas.RO_ALWAYS
        default_common.log_history = 5

        # You MUST call midas.frontend.EquipmentBase.__init__ in your equipment's __init__ method!
        midas.frontend.EquipmentBase.__init__(self, client, 'CryoScriptSequencer', default_common, self.DEFAULT_SETTINGS)

        self.client.register_jrpc_callback(self.rpc_handler, True)

    def exit(self):

        # stop watching all functions
        pass

    @property
    def current(self): return self.client.odb_get(f'{self.odb_settings_dir}/_current')

    def log(self, msg, is_error=False):

        if self.settings['dry_run']:
            print(f'[DRY RUN] {msg}')

        else:
            self.client.msg(msg, is_error)

    def queue_add(self, name):
        """Add an equipment to the end of the queue

        Args:
            name (str): name of the equipment (no full path)
        """

        # get the equipment settings path
        path = f'/Equipment/{name}/Settings'

        # get parameters and their values, make parameter string
        parstr = []
        parnames = self.client.odb_get(f'{path}/_parnames')
        parnames = [parnames] if isinstance(parnames, str) else parnames
        for parname in parnames:
            val = self.client.odb_get(f'{path}/{parname}')
            parstr.append(f'{parname}:{val}')
        parstr = ','.join(parstr)

        # add to settings
        i = self.client.odb_get(f'{self.odb_settings_dir}/_queue_length')
        self.client.odb_set(f'{self.odb_settings_dir}/_functions[{i}]', name)
        self.client.odb_set(f'{self.odb_settings_dir}/_inputs[{i}]', parstr)
        self.client.odb_set(f'{self.odb_settings_dir}/_queue_length', i+1)

    def queue_clear(self):
        """Clear the queue of all entries"""
        self.client.odb_set(f'{self.odb_settings_dir}/_functions', ['']*self.QUEUE_MAX_LEN)
        self.client.odb_set(f'{self.odb_settings_dir}/_inputs', ['']*self.QUEUE_MAX_LEN)
        self.client.odb_set(f'{self.odb_settings_dir}/_queue_length', 0)
        self.client.odb_set(f'{self.odb_settings_dir}/_current', 0)
        self.client.odb_set(f'{self.odb_settings_dir}/Enabled', False)

    def queue_down(self, idx):
        """Move queued item from idx to idx+1

        Args:
            idx (int): index of item in list
        """

        # get settings arrays
        fns = self.client.odb_get(f'{self.odb_settings_dir}/_functions')
        inpts = self.client.odb_get(f'{self.odb_settings_dir}/_inputs')
        n = self.client.odb_get(f'{self.odb_settings_dir}/_queue_length')
        idx_now = self.client.odb_get(f'{self.odb_settings_dir}/_current')

        # early end condition
        if idx == n-1:
            return

        # swap element idx
        fns[idx], fns[idx+1] = fns[idx+1], fns[idx]
        inpts[idx], inpts[idx+1] = inpts[idx+1], inpts[idx]

        # check if swapped with currently running script
        if idx == idx_now:
            idx_now += 1
        elif idx+1 == idx_now:
            idx_now -= 1

        # re-add arrays
        self.client.odb_set(f'{self.odb_settings_dir}/_functions', fns)
        self.client.odb_set(f'{self.odb_settings_dir}/_inputs', inpts)
        self.client.odb_set(f'{self.odb_settings_dir}/_current', idx_now)

    def queue_remove(self, idx):
        """Remove an equipment from the queue

        Args:
            idx (int): index of item in list
        """

        # get settings arrays
        fns = self.client.odb_get(f'{self.odb_settings_dir}/_functions')
        inpts = self.client.odb_get(f'{self.odb_settings_dir}/_inputs')
        n = self.client.odb_get(f'{self.odb_settings_dir}/_queue_length')
        idx_now = self.client.odb_get(f'{self.odb_settings_dir}/_current')
        enabled = self.client.odb_get(f'{self.odb_settings_dir}/Enabled')

        # disallow removal of currently running script
        if idx == idx_now and enabled:
            self.client.msg('I will not permit removal of the currently running script from the queue')
            return

        # remove element idx
        fns.pop(idx)
        inpts.pop(idx)
        n -= 1

        # de-increment the current run
        if idx_now > idx:
            idx_now -= 1

        # re-add arrays
        self.client.odb_set(f'{self.odb_settings_dir}/_functions', fns)
        self.client.odb_set(f'{self.odb_settings_dir}/_inputs', inpts)
        self.client.odb_set(f'{self.odb_settings_dir}/_queue_length', max(0, n))
        self.client.odb_set(f'{self.odb_settings_dir}/_current', idx_now)

    def queue_up(self, idx):
        """Move queued item from idx to idx-1

        Args:
            idx (int): index of item in list
        """
        # early end condition
        if idx == 0:
            return

        # get settings arrays
        fns = self.client.odb_get(f'{self.odb_settings_dir}/_functions')
        inpts = self.client.odb_get(f'{self.odb_settings_dir}/_inputs')
        idx_now = self.client.odb_get(f'{self.odb_settings_dir}/_current')

        # swap element idx
        fns[idx], fns[idx-1] = fns[idx-1], fns[idx]
        inpts[idx], inpts[idx-1] = inpts[idx-1], inpts[idx]

        # check if swapped with currently running script
        if idx == idx_now:
            idx_now -= 1
        elif idx-1 == idx_now:
            idx_now += 1

        # re-add arrays
        self.client.odb_set(f'{self.odb_settings_dir}/_functions', fns)
        self.client.odb_set(f'{self.odb_settings_dir}/_inputs', inpts)
        self.client.odb_set(f'{self.odb_settings_dir}/_current', idx_now)

    def start_script(self, idx):

        # get the script settings
        parstrs = self.settings['_inputs'][idx].strip()
        name = self.settings['_functions'][idx]

        # set the settings
        for parstr in parstrs.split(','):
            try:
                key, val = parstr.strip().split(':')
            except ValueError as err:
                print(f'Attempting to split "{parstr.strip()}" by deliniator ":"')
                raise err from None

            val = val.strip()
            key = key.strip()

            try:
                val = float(val)
            except ValueError:
                pass
            self.client.odb_set(f'/Equipment/{name}/Settings/{key}', val)

        # set dry_run status
        self.client.odb_set(f'/Equipment/{name}/Settings/dry_run', self.settings['dry_run'])

        # enable script
        self.client.odb_set(f'/Equipment/{name}/Settings/Enabled', True)

        # indicate that the script is running
        self.client.odb_set(f'{self.odb_settings_dir}/_script_is_running', True)

    def readout_func(self):
        """
        For a periodic equipment, this function will be called periodically
        (every 100ms in this case). It should return either a `cdms.event.Event`
        or None (if we shouldn't write an event).

        If equipment has finished running, then run the next item in the queue
        """
        pass

    def rpc_handler(self, client, cmd, args, max_len):
        """
        This is the function that will be called when something/someone
        triggers the "JRPC" for this client (e.g. by using the javascript
        code above).

        Arguments:

        * client (midas.client.MidasClient)
        * cmd (str) - The command user wants to execute
        * args (str) - Other arguments the user supplied
        * max_len (int) - The maximum string length the user accepts in the return value

        Returns:

        2-tuple of (int, str) for status code, message.
        """
        ret_int = midas.status_codes["SUCCESS"]
        ret_str = ""

        if cmd == "add":
            self.queue_add(args)
            ret_int = midas.status_codes["SUCCESS"]
            ret_str = f'Added {args}'

        elif cmd == 'remove':
            self.queue_remove(int(args))
            ret_int = midas.status_codes["SUCCESS"]
            ret_str = f'Removed queued item at index {args}'
        elif cmd == 'up':
            args = int(args)
            self.queue_up(args)
            ret_int = midas.status_codes["SUCCESS"]
            ret_str = f'Moved queued item at index {args} to {args-1}'
        elif cmd == 'down':
            args = int(args)
            self.queue_down(args)
            ret_int = midas.status_codes["SUCCESS"]
            ret_str = f'Moved queued item at index {args} to {args+1}'
        elif cmd == 'clear':
            self.queue_clear()
            ret_int = midas.status_codes["SUCCESS"]
            ret_str = f'Cleared full queue'
        else:
            ret_int = midas.status_codes["FE_ERR_DRIVER"]
            ret_str = "Unknown command '%s'" % cmd

        # return string is message passed back to webpage client
        return (ret_int, ret_str)

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

        # start or stop the sequencer
        if 'Enabled' in path:
            if new_value:
                self.log('CryoScriptSequencer started')

                # check if functions exist
                if self.settings['_queue_length'] == 0:
                    self.client.odb_set(f'{self.odb_settings_dir}/Enabled', False)
                    self.log('No items in queue')
                    return

                # start the sequence
                self.start_script(self.current)
            else:
                # stop equipment from running, if it exists (it won't if queue is being cleared)
                name = self.settings['_functions'][self.settings['_current']]
                if self.client.odb_exists(f'/Equipment/{name}/Settings'):
                    self.client.odb_set(f'/Equipment/{name}/Settings/Enabled', False)
                    self.log('CryoScriptSequencer stopped')

        # start the next script in the sequence if the currently running script is being stopped
        elif '_script_is_running' in path and not new_value:

            # check if the sequencer is enabled
            if not bool(self.client.odb_get(f'{self.odb_settings_dir}/Enabled')):
                return

            # check if the currently running script exited cleanly - if not stop sequencer
            name = self.settings['_functions'][self.current]
            if self.client.odb_get(f'/Equipment/{name}/Settings/_exit_with_error'):
                self.client.odb_set(f'{self.odb_settings_dir}/Enabled', False)
                return

            # index of current run
            idx = self.current

            # check if we are past the end of the queue, if we are then see if we need to loop
            if self.current+1 >= self.settings['_queue_length']:
                self.client.odb_set(f'{self.odb_settings_dir}/_current', 0)
                idx = 0

                # start the next loop
                if self.settings['_nloops'] > 0:
                    self.client.odb_set(f'{self.odb_settings_dir}/_nloops', self.settings['_nloops']-1)

                # stop the sequencer
                else:
                    self.client.odb_set(f'{self.odb_settings_dir}/Enabled', False)
                    return

            # iterate the index of the currently running script
            else:
                idx += 1
                self.client.odb_set(f'{self.odb_settings_dir}/_current', self.current+1)

            # start the script
            self.start_script(idx)

        # TODO: test this
        # synchronize inputs
        # elif '_inputs' in path:
        #     fnname = self.settings['_functions'][idx]
        #     inputs = new_value

        #     # set the equipment parameter if its the currently running equipment
        #     if self.client.odb_get(f'/Equipment/{fnname}/Settings/Enabled'):

        #         # iterate parameters in param string
        #         for parname in inputs.split(','):

                    # par, value = parname.strip().split(':')
                    # par = par.strip()

                    # # convert to numerical, if possible
                    # try:
                    #     value = float(value)
                    # except ValueError:
                    #     pass

                    # # set the value
                    # self.client.odb_set(f'/Equipment/{fnname}/Settings/{par}', value)