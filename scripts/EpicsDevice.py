# Set and get EPICS PVs associated with a single device
# Derek Fujimoto
# May 2025

import epics
import time

class EpicsError(Exception): pass
class EpicsInterlockError(Exception): pass
class EpicsTimeoutError(Exception): pass

# collection of epics devices - access to all UCN2 devices like a dictionary
class EpicsDeviceCollection(dict):
    """Store devices like a dictionary, make entries if they don't exist. Basically easy access to any and all devices

    Notes:
        Can only connect to UCN2 devices (for security reasons)
        Can access like attributes or dictionary keys
        keys are key of device without prefix or suffix. Ex: "TS512" or "FM208"

    Args:
        logfn (fn handle): function for posting logging messages. Format: fn(message, is_error=False)
        timeout (int): duration in seconds before throwing timeouterror
        dry_run (bool): instead of performing action, just log the action

    Returns
        EpicsDevice: connected device
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

    def __init__(self, logfn=None, timeout=10, dry_run=False):
        self._devices = {}
        self.logfn = logfn
        self.timeout = timeout
        self.dry_run = dry_run

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):

        # if exists in dictionary, then return that
        try:
            return self._devices[key]

        # doesn't exist: make EpicsDevice
        except KeyError:
            # find the prefix from leading value
            fullname = f'{self.prefix[key[-3]]}:{key}'

            # add to devices
            self._devices[key] = get_device(path=fullname,
                                            logfn=self.logfn,
                                            timeout=self.timeout,
                                            dry_run=self.dry_run,
                                            )

            return self._devices[key]

# assign a class to a device based on the path
def get_device(path, logfn=None, timeout=10, dry_run=False):

    obj = None

    if ':AV' in path:

        # normally closed valves
        obj = EpicsAV

        # special valves
        if 'AV020' in path:
            obj = EpicsAV020
        elif 'AV021' in path:
            obj = EpicsAV021

        # normally open valves
        else:
            for av in ['AV024', 'AV025', 'AV026', 'AV108', 'AV203', ]:
                if av in path:
                    obj = EpicsAVNormOpen
                    break

    elif ':CG' in path:     obj = EpicsCG
    elif ':CRV' in path:    obj = EpicsCRV
    elif ':FM' in path:     obj = EpicsFM
    elif ':FPV' in path:    obj = EpicsFPV

    elif ':HTR' in path:
        num = int(path.split(':')[-1].replace('HTR', ''))
        if num in [208, 209, 210, 211, 212, 206, 207, 213, 214]:
            obj = EpicsHTRCalibrated
        else:
            obj = EpicsHTR

    elif ':IG' in path:     obj = EpicsIG
    elif ':MFC' in path:    obj = EpicsMFC
    elif ':PT' in path:     obj = EpicsPT
    elif ':TP' in path:     obj = EpicsTP
    elif ':TS' in path:     obj = EpicsTS
    else:                   obj = EpicsDevice

    return obj(path, logfn, timeout, dry_run)

# base class for simple devices ---------------------------------------------
class EpicsDevice(object):
    """
        Basic device class. Allows one to treat a collection of PVs as a single device
        which you can read/write or turn on/off.

        Args:
            devicepath (str): top path to device, excluding its components. Ex: UCN2:HE4:FPV212
            timeout (float): timeout for operations in seconds
            logfn (fn handle): function for posting logging messages. Format: fn(message, is_error=False)
            dry_run (bool): if true, log instructions instead of operating the cryostat
    """

    # suffixes common to most devices
    suffixes = ('STATON',   # on/off status
                'STATTMO',  # timeout status
                'STATDRV',  # drive status
                'STATINT',  # interlock status
                'STATBYP',  # interlock bypass status
                'DRVON',    # on button
                'DRVOFF',   # off button
                'RST',      # reset button
                )

    # for setting setpoint. Should be one of the suffixes
    setpoint_name = None
    readback_name = None

    # other connections for inherited classes
    other_suffixes = list()

    # sleep time after actuating or setting values in seconds
    sleep_time = 1

    # time between reset attempts if device timeout
    reset_check_delay = 2

    def __init__(self, devicepath, logfn=None, timeout=10, dry_run=False):

        # check inputs
        if not isinstance(devicepath, str):
            raise RuntimeError(f'devicepath must be of type str')
        if not isinstance(timeout, (float, int)):
            raise RuntimeError(f'timeout must be of numerical type (int or float)')

        # save inputs
        self.path = devicepath
        self.timeout = timeout
        self.logfn = logfn
        self.dry_run = dry_run

        # try to connect to all PVs associated with that device
        self.pv = {key: epics.PV(f'{devicepath}:{key}') for key in self.suffixes}
        self.pv = {**self.pv,
                   **{key: epics.PV(f'{devicepath}:{key}') for key in self.other_suffixes}}

        # wait for keys to connect
        all_connected = all([pv.connected for pv in self.pv.values()])
        t0 = time.time()
        while not all_connected:
            # timeout
            if time.time()-t0 > self.timeout:
                raise TimeoutError(f'EpicsDevice {devicepath} unable to connect to all PVs within {timeout} seconds')

            # check status
            time.sleep(0.001)
            all_connected = all([pv.connected for pv in self.pv.values()])

    def __ge__(self, other):
        if hasattr(other, 'readback'):  return self.readback >= other.readback
        else:                           return self.readback >= other

    def __gt__(self, other):
        if hasattr(other, 'readback'):  return self.readback > other.readback
        else:                           return self.readback > other

    def __le__(self, other):
        if hasattr(other, 'readback'):  return self.readback <= other.readback
        else:                           return self.readback <= other

    def __lt__(self, other):
        if hasattr(other, 'readback'):  return self.readback < other.readback
        else:                           return self.readback < other

    def _log(self, message, is_error=False):
        if self.logfn is None:
            return
        self.logfn(message, is_error)

    def _switch(self, on=True):
        """Turn device on or off

        Args:
            valve (bool): if true, print open/closed instead of on/off
            on (bool): if true turn on, else turn off
        """

        # check health
        self.healthcheck()

        # on or off
        if on:
            suffix = 'DRVON'
            attr = 'is_off'
            state = 'on'

        else:
            suffix = 'DRVOFF'
            attr = 'is_on'
            state = 'off'

        # early stop condition
        if not getattr(self, attr):
            self._log(f'{self.path} is already {state}', False)
            return

        # switch with timeout
        t0 = time.time()
        while getattr(self, attr):

            # timeout
            if (self.timeout > 0) and (time.time()-t0 > self.timeout):
                msg = f'{self.path} timeout while trying to turn {state}'
                self._log(msg, True)
                raise TimeoutError(msg)

            # set
            if self.dry_run:
                break
            else:
                self.pv[suffix].put(1)
                time.sleep(self.sleep_time)

        # switch success
        self._log(f'{self.path} turned {state}', False)

    def healthcheck(self):
        # some simple checks of device health

        if self.is_interlocked and not self.is_bypassed:
            msg = f'{self.path} is interlocked'
            self._log(msg, True)
            if not self.dry_run:
                raise EpicsInterlockError(msg)

        if self.is_timeout:
            self._log(f'{self.path} has timed-out', False)

            # try to reset
            t0 = time.time()
            nattempts = 0
            while self.is_timeout:

                # try again
                if (time.time()-t0 < self.reset_check_delay) or (nattempts == 0):

                    # too many failed attempts
                    if nattempts > 1:
                        msg = f'{self.path} has timed-out and is unresponsive to reset (tried {nattempts} times)'
                        self._log(msg, True)
                        raise EpicsTimeoutError(msg)

                    # reset
                    self.reset()
                    nattempts += 1
                    t0 = time.time()

                # sleep before checking again
                time.sleep(self.sleep_time)

            self._log(f'Reset of {self.path} successful')

    def off(self):
        """Turn device off"""
        self._switch(on=False)

    def on(self):
        """Turn device on"""
        self._switch(on=True)

    def reset(self):
        """Reset device"""
        if not self.dry_run:
            self.pv['RST'].put(1)
        self._log(f'{self.path} reset', False)

    def set(self, setpoint):
        """Set the setpoint variable pointed to by self.setpoint_name"""

        # check that a setpoint variable exists
        if self.setpoint_name is None:
            msg = f'{self.path} does not define a setpoint key'
            self._log(msg, True)
            raise RuntimeError(msg)

        # run health check
        self.healthcheck()

        # check setpoint limits
        if setpoint < self.pv[self.setpoint_name].lower_ctrl_limit or \
           setpoint > self.pv[self.setpoint_name].upper_ctrl_limit:
            msg = f'Attempting to set a setpoint of {self.path} which is out of bounds. Attempted value: {setpoint}. Bounds: ({self.pv[self.setpoint_name].lower_ctrl_limit}, {self.pv[self.setpoint_name].upper_ctrl_limit})'
            self._log(msg, True)
            raise RuntimeError(msg)

        t0 = time.time()
        while self.pv[self.setpoint_name].get() != setpoint:

            # timeout
            if (self.timeout > 0) and (time.time()-t0 > self.timeout):
                msg = f'{self.path} has timed out while trying to set flow setpoint'
                self._log(msg, True)
                raise TimeoutError(msg)

            # set
            if self.dry_run:
                break
            else:
                self.pv[self.setpoint_name].put(setpoint)
            time.sleep(self.sleep_time)

        # set success
        self._log(f"{self.path}:{self.setpoint_name} set to {setpoint} {self.setpoint_units}")

    # dynamic properties
    @property
    def is_bypassed(self):      return bool(self.pv['STATBYP'].get())
    @property
    def is_off(self):           return not bool(self.pv['STATON'].get())
    @property
    def is_on(self):            return bool(self.pv['STATON'].get())
    @property
    def is_driven(self):        return bool(self.pv['STATDRV'].get())
    @property
    def is_interlocked(self):   return not bool(self.pv['STATINT'].get())
    @property
    def is_timeout(self):       return bool(self.pv['STATTMO'].get())
    @property
    def readback(self):         return self.pv[self.readback_name].get()
    @property
    def readback_units(self):   return self.pv[self.readback_name].units
    @property
    def setpoint(self):         return self.pv[self.setpoint_name].get()
    @property
    def setpoint_units(self):   return self.pv[self.setpoint_name].units

# device-type specific classes ----------------------------------------------
class EpicsAV(EpicsDevice):
    """Automatic Valves"""
    sleep_time = 1

    on_state = 'open'
    off_state = 'close'

    def _switch(self, on=True):
        """Turn device on or off

        Args:
            valve (bool): if true, print open/closed instead of on/off
            on (bool): if true turn on, else turn off
        """

        # check health
        self.healthcheck()

        # on or off
        if on:
            suffix = 'DRVON'
            state = self.on_state
            if 'open' in state: attr = 'is_closed'
            else:               attr = 'is_open'

        else:
            suffix = 'DRVOFF'
            state = self.off_state
            if 'open' in state: attr = 'is_closed'
            else:               attr = 'is_open'

        # early stop condition
        if not getattr(self, attr):
            self._log(f'{self.path} is already {state}', False)
            return

        # switch with timeout
        t0 = time.time()
        while getattr(self, attr):

            # timeout
            if (self.timeout > 0) and (time.time()-t0 > self.timeout):
                msg = f'{self.path} timeout while trying to {state}'
                self._log(msg, True)
                raise TimeoutError(msg)

            # set
            if self.dry_run:
                break
            else:
                self.pv[suffix].put(1)
                time.sleep(self.sleep_time)

        # switch success
        state = f'{state}ed' if 'open' in state else f'{state}d'
        self._log(f'{self.path} {state}', False)

    def close(self):
        """synonym for off, but for valves"""
        self._switch(on=False)

    def open(self):
        """synonym for on, but for valves"""
        self._switch(on=True)

    @property
    def is_open(self):          return self.is_on
    @property
    def is_closed(self):        return not self.is_open

class EpicsAVNormOpen(EpicsAV):
    """Normally open AV"""

    on_state = 'close'
    off_state = 'open'

    def close(self):
        """synonym for off, but for valves"""
        self._switch(on=True)

    def open(self):
        """synonym for on, but for valves"""
        self._switch(on=False)

class EpicsCG(EpicsDevice):
    readback_name = 'RDVAC'
    suffixes = ['RDVAC', 'STATON', 'STATOK']

    @property
    def is_vacok(self):
        return bool(self.pv['STATOK'].get())

class EpicsCRV(EpicsDevice):
    """Cryo valves"""
    other_suffixes = ('RDDACP', 'POS')
    setpoint_name = 'POS'
    readback_name = 'RDDACP'

class EpicsFM(EpicsDevice):
    """Flow meter"""
    suffixes = ('RDFLOW',)
    readback_name = 'RDFLOW'

class EpicsFPV(EpicsDevice):
    """Flow proportional valves"""
    other_suffixes = ('RDDACP', 'POS', 'STATLOC')
    setpoint_name = 'POS'
    readback_name = 'RDDACP'

    @property
    def readback(self): return self.pv['RDDACP'].get()
    @property
    def is_autoenable(self): return bool(self.pv['STATLOC'].get())

class EpicsHTR(EpicsDevice):
    """Heaters"""
    other_suffixes = (  'STAT.B8',
                        'CMD',
                        'CUR',
                        'RDCUR',
                        'RDHILIMI',
                    )
    setpoint_name = 'CUR'
    readback_name = 'RDCUR'

    def disable_auto(self):
        # check health
        self.healthcheck()

        # switch with timeout
        t0 = time.time()
        while self.is_autoenable:
            # timeout
            if (self.timeout > 0) and (time.time()-t0 > self.timeout):
                msg = f'{self.path} timeout while trying to disable autocontrol'
                self._log(msg, True)
                raise TimeoutError(msg)

            # set
            if self.dry_run:
                break
            else:
                self.pv['CMD'].put(1)
                time.sleep(self.sleep_time)

        # success
        self._log(f'{self.path} autocontrol disabled')

    def enable_auto(self):
        # check health
        self.healthcheck()

        # switch with timeout
        t0 = time.time()
        while not self.is_autoenable:
            # timeout
            if (self.timeout > 0) and (time.time()-t0 > self.timeout):
                msg = f'{self.path} timeout while trying to enable autocontrol'
                self._log(msg, True)
                raise TimeoutError(msg)

            # set
            if self.dry_run:
                break
            else:
                self.pv['CMD'].put(1)
                time.sleep(self.sleep_time)

        # success
        self._log(f'{self.path} autocontrol enabled')

    @property
    def is_autoenable(self):    return bool(self.pv['STAT.B8'].get())
    @property
    def setpoint_limit(self):   return self.pv['RDHILIMI'].get()

class EpicsHTRCalibrated(EpicsHTR):
    """Heater that has been calibrated so that you set the temperature directly"""
    other_suffixes = (  'STATLOC',
                        'CMD',
                        'SETTEMP',
                        'RDSETTEMP',
                    )
    setpoint_name = 'SETTEMP'
    readback_name = 'RDSETTEMP'

    @property
    def is_autoenable(self):    return bool(self.pv['STATLOC'].get())

class EpicsIG(EpicsDevice):
    """Ion gauge"""
    readback_name = 'RDVAC'
    suffixes = ['RDVAC']

class EpicsMFC(EpicsDevice):
    """Mass flow controller"""
    other_suffixes = ('FLOW', 'RDFLOW')
    setpoint_name = 'FLOW'
    readback_name = 'RDFLOW'

class EpicsPT(EpicsDevice):
    """Pressure sensor"""
    readback_name = 'RDPRESS'
    suffixes = ['RDPRESS']

class EpicsTP(EpicsDevice):
    """Turbo pump"""

    sleep_time = 3
    other_suffixes = ('STATLSPD',   # low speed status
                      'STATSTRT',   # start status
                      'STATPTMO',   # pump timeout
                      'STATFLT',    # fault status
                      'STATATSPD',  # at speed status
                      'DRVLSPD',    # low speed button
                      'RDHRS',      # hours readback
                      'RDSPD',      # speed readback in volts
                    )

    def healthcheck(self):
        super().healthcheck()

        if self.is_pump_timeout:
            msg = f'{self.path} shows pump has timed-out'
            self._log(msg, True)
            raise EpicsTimeoutError(msg)

        if self.is_faulted:
            msg = f'{self.path} shows pump has faulted'
            self._log(msg, True)
            raise EpicsError(msg)

    def low(self):
        """Toggle low speed state"""
        self.healthcheck()

        target_state = not self.is_low
        t0 = time.time()
        while self.is_low != target_state:
            if (self.timeout) > 0 and (time.time()-t0 > self.timeout):
                msg = f'{self.path} timed out while toggling the low speed setting from {self.is_low} to {target_state}'
                self._log(msg, True)
                raise TimeoutError(msg)

            if self.dry_run:
                break
            else:
                self.pv['DRVLSPD'].put(1)
                time.sleep(self.sleep_time)

        if target_state:
            self._log(f'{self.path} put into low speed state')
        else:
            self._log(f'{self.path} put into high speed state')

    @property
    def is_atspeed(self):       return bool(self.pv['STATATSPD'].get())
    @property
    def is_faulted(self):       return bool(self.pv['STATFLT'].get())
    @property
    def is_low(self):           return bool(self.pv['STATLSPD'].get())
    @property
    def is_pump_timeout(self):  return bool(self.pv['STATPTMO'].get())
    @property
    def is_started(self):       return bool(self.pv['STATSTRT'].get())
    @property
    def hours(self):            return self.pv['RDHRS'].get()
    @property
    def hours_unit(self):       return self.pv['RDHRS'].units
    @property
    def speed(self):            return self.pv['RSPD'].get()
    @property
    def speed_unit(self):       return self.pv['RSPD'].units

class EpicsTS(EpicsDevice):
    """Temperature sensor"""
    readback_name = 'RDTEMPK'
    suffixes = ['RDTEMPK']

# device-specific classes ---------------------------------------------------
class EpicsAV020(EpicsAV):
    """Automatic Valve UCN2:ISO:AV020"""

    other_suffixes = ('STAT.B8', 'CMD')

    def __init__(self, devicepath, logfn=None, timeout=10, dry_run=False):
        super().__init__(devicepath, logfn=logfn, timeout=timeout, dry_run=dry_run)

        # connect to other devices, specific to particular AV
        self.pv['PT001High'] = epics.PV(f'UCN2:ISO:PT001:SETTHRESH1')
        self.pv['PT001Low'] = epics.PV(f'UCN2:ISO:PT001:SETTHRESH2')
        self.pv['PT009High'] = epics.PV(f'UCN2:ISO:PT009:SETTHRESH1')
        self.pv['PT009Low'] = epics.PV(f'UCN2:ISO:PT009:SETTHRESH2')

    @property
    def is_autoenable(self):return bool(self.pv['STAT.B8'].get())
    @property
    def pt001_high(self): return self.pv['PT001High'].get()
    @property
    def pt001_low(self): return self.pv['PT001Low'].get()
    @property
    def pt009_high(self): return self.pv['PT009High'].get()
    @property
    def pt009_low(self): return self.pv['PT009Low'].get()

    def enable_auto(self):
        # check health
        self.healthcheck()

        # switch with timeout
        t0 = time.time()
        while not self.is_autoenable:
            # timeout
            if (self.timeout > 0) and (time.time()-t0 > self.timeout):
                msg = f'{self.path} timeout while trying to enable autocontrol'
                self._log(msg, True)
                raise TimeoutError(msg)

            # set
            if self.dry_run:
                break
            else:
                self.pv['CMD'].put(1)
                time.sleep(self.sleep_time)

        # success
        self._log(f'{self.path} autocontrol enabled')

    def disable_auto(self):
        # check health
        self.healthcheck()

        # switch with timeout
        t0 = time.time()
        while self.is_autoenable:
            # timeout
            if (self.timeout > 0) and (time.time()-t0 > self.timeout):
                msg = f'{self.path} timeout while trying to disable autocontrol'
                self._log(msg, True)
                raise TimeoutError(msg)

            # set
            if self.dry_run:
                break
            else:
                self.pv['CMD'].put(1)
                time.sleep(self.sleep_time)

        # success
        self._log(f'{self.path} autocontrol disabled')

class EpicsAV021(EpicsAV):
    """Automatic Valve UCN2:ISO:AV021"""

    other_suffixes = ('STAT.B8', 'CMD')

    def __init__(self, devicepath, logfn=None, timeout=10, dry_run=False):
        super().__init__(devicepath, logfn=logfn, timeout=timeout, dry_run=dry_run)

        # connect to other devices, specific to particular AV
        self.pv['PT001High'] = epics.PV(f'UCN2:ISO:PT001:SETTHRESH3')
        self.pv['PT001Low'] = epics.PV(f'UCN2:ISO:PT001:SETTHRESH4')
        self.pv['PT009High'] = epics.PV(f'UCN2:ISO:PT009:SETTHRESH3')
        self.pv['PT009Low'] = epics.PV(f'UCN2:ISO:PT009:SETTHRESH4')

    @property
    def is_autoenable(self):return bool(self.pv['STAT.B8'].get())
    @property
    def pt001_high(self): return self.pv['PT001High'].get()
    @property
    def pt001_low(self): return self.pv['PT001Low'].get()
    @property
    def pt009_high(self): return self.pv['PT009High'].get()
    @property
    def pt009_low(self): return self.pv['PT009Low'].get()

    def enable_auto(self):
        # check health
        self.healthcheck()

        # switch with timeout
        t0 = time.time()
        while not self.is_autoenable:
            # timeout
            if (self.timeout > 0) and (time.time()-t0 > self.timeout):
                msg = f'{self.path} timeout while trying to enable autocontrol'
                self._log(msg, True)
                raise TimeoutError(msg)

            # set
            if self.dry_run:
                break
            else:
                self.pv['CMD'].put(1)
                time.sleep(self.sleep_time)

        # success
        self._log(f'{self.path} autocontrol enabled')

    def disable_auto(self):
        # check health
        self.healthcheck()

        # switch with timeout
        t0 = time.time()
        while self.is_autoenable:
            # timeout
            if (self.timeout > 0) and (time.time()-t0 > self.timeout):
                msg = f'{self.path} timeout while trying to disable autocontrol'
                self._log(msg, True)
                raise TimeoutError(msg)

            # set
            if self.dry_run:
                break
            else:
                self.pv['CMD'].put(1)
                time.sleep(self.sleep_time)

        # success
        self._log(f'{self.path} autocontrol disabled')
