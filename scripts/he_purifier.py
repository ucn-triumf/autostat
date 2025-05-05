#!/usr/bin/python3
# run with "nohup ./he_purifier.py &" to keep the code running in the background even if disconnected
# Transition the He purifier from regeneration to cooling
# Derek Fujimoto
# May 2025

import epics
import midas, midas.client
import time, datetime
from CryoScript import CryoScript

# TODO: Make elog entry on completion?
# TODO: stop_circulation should check for clogs
# TODO: cleaner management of scripts and logging

# make scripts ------------------------------------------------------------
class StartCooling(CryoScript):
    devices_off = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
                   'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
                   'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
                   'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
                   'AV032', 'AV034', 'AV050', 'AV051']

    def run(self, temperature):
        self.log(f'Started {self.scriptname}')

        # turn on heaters and set setpoints to zero
        for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
            self.devices[htr].set(0)
            # self.devices[htr].on() # TODO: Uncomment this line once permissions are given

        # wait until pressure is low before turning on the pump
        self.wait_until_lessthan(self.devices['PT050'], 30)

        # turn on pump
        self.devices.CP101.on()

        # block until temps are low
        self.wait_until_lessthan(self.devices.TS512, 300)
        self.wait_until_lessthan(self.devices.TS513, 300)

        # turn on pump
        self.devices.CP001.on()

        # turn on autostat enable and change setpoints
        pids = ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']
        for pid in pids:
            self.set_odb(f'/Equipment/{pid}/Settings/target_setpoint', temperature)
            self.set_odb(f'/Equipment/{pid}/Settings/Enabled', True)

        # you are now cooling!
        log(f'System is now cooling to {temperature}')

class StopRegeneration(CryoScript):
    devices_off = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
                   'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
                   'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
                   'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
                   'AV032', 'AV034', 'BP001']

    devices_on = ['HTR010', 'HTR012', 'HTR105', 'HTR107']

    def run(self, fm208_thresh):

        # Block execution until FM208 is below threshold
        self.wait_until_lessthan(self.devices['FM208'], fm208_thresh)

        # turn off autostat enable
        pids = ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']
        for pid in pids:
            self.set_odb(f'/Equipment/{pid}/Settings/Enabled', False)

        # set heater setpoints to zero
        htrs = ['HTR010', 'HTR012', 'HTR105', 'HTR107']
        for htr in htrs:
            self.devices[htr].set(0)

        # Close valves to atmosphere
        self.devices.AV050.close()
        self.devices.AV051.close()

        # turn off pump
        self.devices.BP002.off()

        # done
        log(f'System has finished regenerating')

def stop_cooling(temperature=70):
    """Block execution until cold"""


    # check valve states. These should be closed:
    avlist = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
              'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
              'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
              'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
              'AV032', 'AV034', 'AV050', 'AV051']

    for av in avlist:
        if self.devices[av].is_open:
            msg = f'{av} is open when it should be closed! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check that pumps are off
    pumplist = ['BP001', 'BP002']
    for pump in pumplist:
        if self.devices[pump].is_open:
            msg = f'{pump} is on when it should be off! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check that heaters are on and setpoints are properly set
    for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
        if self.devices[htr].is_off:
            msg = f'{htr} is off when it should be on! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    for pid in ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']:
        if not client.odb_get(f'/Equipment/{pid}/Settings/Enabled'):
            msg = f'{pid} is not enabled when it should be! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

        setpoint = client.odb_get(f'/Equipment/{pid}/Settings/target_setpoint')
        if setpoint != temperature:
            msg = f'{pid} setpoint ({setpoint:.1f}K) is not as it should be! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # wait for the temperature to drop
    wait_until_lessthan(self.devices['TS510'], temperature+0.1, log)
    wait_until_lessthan(self.devices['TS511'], temperature+0.1, log)
    wait_until_lessthan(self.devices['TS512'], temperature+0.1, log)
    wait_until_lessthan(self.devices['TS513'], temperature+0.1, log)

    log(f'System cooled to {temperature}K')

def start_circulation():

    # check purifier temperatures
    for ts in ['TS510', 'TS511', 'TS512', 'TS513']:
        if self.devices[ts].readback > 100:
            msg = f'{ts} temperature is too high ({self.devices[ts].readback}K). Wait until below 100 K. Exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check valve states. These should be closed:
    avlist = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
              'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
              'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
              'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
              'AV032', 'AV034', 'AV050', 'AV051']

    for av in avlist:
        if self.devices[av].is_open:
            msg = f'{av} is open when it should be closed! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check that pumps are off
    pumplist = ['BP001', 'BP002']
    for pump in pumplist:
        if self.devices[pump].is_open:
            msg = f'{pump} is on when it should be off! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # disable AV020 auto control
    self.devices['AV020'].disable_auto()

    # close MFC
    self.devices['MFC001'].close()

    # double check valves to atmosphere are closed
    if self.devices['AV032'].is_open:
        self.devices['AV032'].close()
    if self.devices['AV051'].is_open:
        self.devices['AV051'].close()

    # turn on MP002
    self.devices['AV014'].open()
    self.devices['AV017'].open()
    self.devices['AV015'].open()
    self.devices['MP002'].on()

    # do I wait for a pressure to drop? # TODO: Check this step
    time.sleep(5)
    self.devices['AV017'].close()
    self.devices['AV015'].close()

    # start MP001
    self.devices['AV019'].open()
    self.devices['AV020'].open()
    self.devices['MP001'].on()
    self.devices['AV012'].open()

    # connect pumps to rest of system
    self.devices['AV011'].open()
    self.devices['AV010'].open()
    self.devices['AV029'].open()
    self.devices['AV027'].open()

    # connect to purifier # TODO: check that these open as they should!
    self.devices['AV025'].open()
    self.devices['AV024'].open()

    # Finalize path
    self.devices['AV022'].open()
    self.devices['AV021'].open()

    # Start MFC001
    self.devices['MFC001'].set(0)
    self.devices['MFC001'].on()
    self.devices['MFC001'].set(30)
    time.sleep(5)
    log(f'MFC001 reads {self.devices["MFC001"].readback} {self.devices["MFC001"].readback_units} after initial open and setpoint {self.devices["MFC001"].setpoint} {self.devices["MFC001"].setpoint_units}')

    # start BP001
    self.devices['BP001'].on()

    # open MFC001
    self.devices['MFC001'].set(50)

    # enable auto control
    self.devices['AV020'].enable_auto()
    self.devices['AV021'].enable_auto()

    # double-check valve states. These should be closed:
    avlist = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV013',
              'AV015', 'AV017', 'AV018', 'AV023', 'AV024', 'AV026', 'AV028',
              'AV030', 'AV031', 'AV032', 'AV034', 'AV050', 'AV051']

    for av in avlist:
        if self.devices[av].is_open:
            msg = f'{av} is open when it should be closed! Closing to protect Isopure.'
            log(msg, True)
            self.devices[av].close()

    # double-check valve states. These should be open:
    avlist = ['AV010', 'AV011', 'AV012', 'AV014', 'AV016', 'AV019', 'AV020',
              'AV021', 'AV022', 'AV024', 'AV025', 'AV027', 'AV029']

    for av in avlist:
        if self.devices[av].is_closed:
            msg = f'{av} is closed when it should be open! Opening to protect bad pressure buildup.'
            log(msg, True)
            self.devices[av].open()


# RUN SCRIPT ==============================================================

with StopRegeneration as script:
    script.check_status()
    script.run(fm208_thresh = 0.25)

with StartCooling as script:
    script.check_status()
    script.run(temperature = 30)
