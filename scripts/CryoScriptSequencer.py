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

class CryoScriptSequencer(midas.frontend.EquipmentBase):
    """Queue and execute a sequence of cryostat scripts"""

    QUEUE_MAX_LEN = 64

    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("Enabled", False),     # if true execute the scripts in the queue
        ("_functions", ['']*64),# list of function/equipment names
        ("_inputs", ['']*64),   # parametrs to pass to equipment
        ("_current", -1),       # index of currently running equipment
        ("_queue_length", 0),   # number of queued scripts
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

        self.do_run_next = False

    def exit(self):

        # stop watching all functions
        pass

    def queue_add(self, name):
        """Add an equipment to the queue

        Args:
            name (str): name of the equipment (no full path)
        """

        # get the equipment settings path
        path = f'/Equipment/{name}/Settings'

        # get parameters and their values, make parameter string
        parstr = []
        for parname in self.client.odb_get(f'{path}/_parnames'):
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

    def queue_remove(self, idx):
        """Remove an equipment from the queue

        Args:
            idx (int): index of item in list
        """

        # get settings arrays
        fns = self.client.odb_get(f'{self.odb_settings_dir}/_functions')
        inpts = self.client.odb_get(f'{self.odb_settings_dir}/_inputs')
        n = self.client.odb_get(f'{self.odb_settings_dir}/_queue_length')

        # remove element idx
        fns.pop(idx)
        inpts.pop(idx)
        n -= 1

        # re-add arrays
        self.client.odb_set(f'{self.odb_settings_dir}/_functions', fns)
        self.client.odb_set(f'{self.odb_settings_dir}/_inputs', inpts)
        self.client.odb_set(f'{self.odb_settings_dir}/_queue_length', n)

    def setup_next(self, *args, **kwargs):

        # get current run
        idx = self.settings['_current']

        # stop watching old run
        try:
            name = self.settings['_functions'][idx]
            self.client.odb_stop_watching(f'/Equipment/{name}/Settings/Enabled')
        except KeyError:
            pass

        # start the next run
        idx += 1
        self.client.odb_set(f'{self.odb_settings_dir}/_current', idx)

        # early end condition: run a script that doesn't exist
        if idx >= self.settings['_queue_length']:
            self.client.odb_set(f'{self.odb_settings_dir}/Enabled', False)
            self.client.odb_set(f'{self.odb_settings_dir}/_current', -1)
            self.client.msg('CryoScriptSequencer stopped')
            return

        # get the script settings
        parstrs = self.settings['_inputs'][idx]
        name = self.settings['_functions'][idx]

        # set the settings
        for parstr in parstrs.split(','):
            key, val = parstr.split(':')

            try:
                val = float(val)
            except ValueError:
                pass
            self.client.odb_set(f'/Equipment/{name}/Settings/{key}', val)

        # start run on next runloop
        self.do_run_next = True

    def readout_func(self):
        """
        For a periodic equipment, this function will be called periodically
        (every 100ms in this case). It should return either a `cdms.event.Event`
        or None (if we shouldn't write an event).

        If equipment has finished running, then run the next item in the queue
        """

        # disabled, don't run
        if not self.settings['Enabled']:
            return

        # check if functions exist
        if self.settings['_queue_length'] == 0:
            self.client.odb_set(f'{self.odb_settings_dir}/Enabled', False)

        # run next (needs to be on run loop after setting the ODB parameters)
        if self.do_run_next:
            # enable run
            name = self.settings['_functions'][self.settings['_current']]
            self.client.odb_set(f'/Equipment/{name}/Settings/Enabled', True)

            # watch to start the next run
            self.client.odb_watch(f'/Equipment/{name}/Settings/Enabled', self.setup_next, True)
            self.do_run_next = False

        # check if at start of sequencer
        idx = self.settings['_current']
        if idx < 0:
            self.setup_next()

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

        if 'Enabled' in path:
            if new_value:   self.client.msg('CryoScriptSequencer started')
            else:           self.client.msg('CryoScriptSequencer stopped')