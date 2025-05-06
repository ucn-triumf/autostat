#!/usr/bin/python3
# run with "nohup ./he_purifier.py &" to keep the code running in the background even if disconnected
# Transition the He purifier from regeneration to cooling
# Derek Fujimoto
# May 2025

import time
from CryoScript import CryoScript

# TODO: Make elog entry on completion?
# TODO: stop_circulation should check for clogs

# make scripts ------------------------------------------------------------
class StartCooling(CryoScript):

    devices_closed = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
                   'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
                   'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
                   'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
                   'AV032', 'AV034', 'AV050', 'AV051']

    def run(self, temperature):

        # turn on heaters and set setpoints to zero
        for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
            self.devices[htr].set(0)
            self.devices[htr].on()

        # wait until pressure is low before turning on the pump
        self.wait_until_lessthan('PT050', 30)

        # turn on pump
        self.devices.CP101.on()

        # block until temps are low
        self.wait_until_lessthan('TS512', 300)
        self.wait_until_lessthan('TS513', 300)

        # turn on pump
        self.devices.CP001.on()

        # turn on autostat enable and change setpoints
        pids = ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']
        for pid in pids:
            self.set_odb(f'/Equipment/{pid}/Settings/target_setpoint', temperature)
            self.set_odb(f'/Equipment/{pid}/Settings/Enabled', True)

class StopCooling(CryoScript):
    devices_closed = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
                      'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
                      'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
                      'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
                      'AV032', 'AV034', 'AV050', 'AV051']
    devices_off = ['BP001', 'BP002']
    devices_on = ['HTR010', 'HTR012', 'HTR105', 'HTR107']

    def check_status(self):
        super().check_status()

        # check enable status of PID autostat
        for pid in ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']:
            if not self.get_odb(f'/Equipment/{pid}/Settings/Enabled'):
                msg = f'{pid} is not enabled when it should be! Undefined system state, exiting.'
                if self.dry_run:    self.log(f'[DRY RUN] {msg}')
                else:               raise RuntimeError(msg)

    def run(self, temperature):

        # check setpoints of PID autostat
        for pid in ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']:
            setpoint = self.get_odb(f'/Equipment/{pid}/Settings/target_setpoint')
            if setpoint != temperature:
                msg = f'{pid} setpoint ({setpoint:.1f}K) is not as it should be! Undefined system state, exiting.'
                if self.dry_run:    self.log(f'[DRY RUN] {msg}')
                else:               raise RuntimeError(msg)

        # wait for the temperature to drop
        self.wait_until_lessthan('TS510', temperature+0.1)
        self.wait_until_lessthan('TS511', temperature+0.1)
        self.wait_until_lessthan('TS512', temperature+0.1)
        self.wait_until_lessthan('TS513', temperature+0.1)

class StartCirculation(CryoScript):
    devices_closed = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
                      'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
                      'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
                      'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
                      'AV032', 'AV034', 'AV050', 'AV051', ]

    devices_off = ['BP001', 'BP002']

    devices_below = {'TS510': 100,
                     'TS511': 100,
                     'TS512': 100,
                     'TS513': 100}

    def run(self, mfc001_setpt=50):

        # disable AV020 auto control
        self.devices.AV020.disable_auto()

        # close MFC
        self.devices.MFC001.close()

        # double check valves to atmosphere are closed
        if self.devices.AV032.is_open:
            self.devices.AV032.close()
        if self.devices.AV051.is_open:
            self.devices.AV051.close()

        # turn on MP002
        self.devices.AV014.open()
        self.devices.AV017.open()
        self.devices.AV015.open()
        self.devices.MP002.on()

        # do I wait for a pressure to drop? # TODO: Check this step
        time.sleep(5)
        self.devices.AV017.close()
        self.devices.AV015.close()

        # start MP001
        self.devices.AV019.open()
        self.devices.AV020.open()
        self.devices.MP001.on()
        self.devices.AV012.open()

        # connect pumps to rest of system
        self.devices.AV011.open()
        self.devices.AV010.open()
        self.devices.AV029.open()
        self.devices.AV027.open()

        # connect to purifier # TODO: check that these open as they should!
        self.devices.AV025.open()
        self.devices.AV024.open()

        # Finalize path
        self.devices.AV022.open()
        self.devices.AV021.open()

        # Start MFC001
        self.devices.MFC001.set(0)
        self.devices.MFC001.on()
        self.devices.MFC001.set(30)
        time.sleep(5)
        self.log(f'MFC001 reads {self.devices["MFC001"].readback} {self.devices["MFC001"].readback_units} after initial open and setpoint {self.devices["MFC001"].setpoint} {self.devices["MFC001"].setpoint_units}')

        # start BP001
        self.devices.BP001.on()

        # open MFC001
        self.devices.MFC001.set(mfc001_setpt)

        # enable auto control
        self.devices.AV020.enable_auto()
        self.devices.AV021.enable_auto()

        # double-check valve states. These should be closed:
        avlist = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV013',
                  'AV015', 'AV017', 'AV018', 'AV023', 'AV024', 'AV026', 'AV028',
                  'AV030', 'AV031', 'AV032', 'AV034', 'AV050', 'AV051']

        for av in avlist:
            if self.devices[av].is_open:
                msg = f'{av} is open when it should be closed! Closing to protect Isopure.'
                self.log(msg, True)
                self.devices[av].close()

        # double-check valve states. These should be open:
        avlist = ['AV010', 'AV011', 'AV012', 'AV014', 'AV016', 'AV019', 'AV020',
                  'AV021', 'AV022', 'AV024', 'AV025', 'AV027', 'AV029']

        for av in avlist:
            if self.devices[av].is_closed:
                msg = f'{av} is closed when it should be open! Opening to protect bad pressure buildup.'
                self.log(msg, True)
                self.devices[av].open()

class StartRecovery(CryoScript):
    devices_open = ['AV010', 'AV011', 'AV012', 'AV014', 'AV019', 'AV020', 'AV021',
                    'AV022', 'AV024', 'AV025', 'AV027', 'AV029', ]

    devices_closed = ['AV008', 'AV009', 'AV013', 'AV015', 'AV016', 'AV017', 'AV018',
                      'AV023', 'AV026', 'AV028', 'AV030', 'AV031', 'AV032', 'AV034',
                      'AV050', 'AV051']

    devices_off = ['BP002']

    devices_on =  [ 'BP001', 'CP001', 'CP101', 'MP001', 'MP002', 'MFC001', 'HTR010',
                    'HTR012', 'HTR105', 'HTR107']

    def check_status(self):
        super().check_status()

        # dry run prefix
        if self.dry_run: prefix = '[DRY RUN] '
        else:            prefix = ''

        # check AV autocontrol status
        for av in ['AV020', 'AV021']:
            if not self.devices[av].is_autoenable:
                msg = f'{prefix}{av} autocontrol is disabled when it should be enabled'
                if self.dry_run:
                    self.log(msg)
                else:
                    raise RuntimeError(msg)

    def run(self):

        # av autocontrol off
        for av in ['AV020', 'AV021']:
            self.devices[av].disable_auto()

        # heater autocontrol off and setpoints to zero
        for pid in ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']:
            self.set_odb(f'/Equipment/{pid}/Settings/Enabled', False)

        for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
            self.devices[htr].set(0)

        # valves
        self.devices.AV021.close()
        self.devices.AV022.close()
        self.devices.AV023.open()
        self.devices.AV008.open()
        self.devices.AV026.open()

class StopRecovery(CryoScript):
    devices_open = ['AV008', 'AV010', 'AV011', 'AV012', 'AV014', 'AV019', 'AV020',
                    'AV023', 'AV024', 'AV025', 'AV026', 'AV027', 'AV029', ]

    devices_closed = ['AV007', 'AV009', 'AV013', 'AV015', 'AV016', 'AV017', 'AV018',
                      'AV021', 'AV022', 'AV028', 'AV030', 'AV031',
                      'AV032', 'AV034',]

    devices_off = ['BP002']

    devices_on =  [ 'BP001', 'CP001', 'CP101', 'MP001', 'MP002', 'MFC001', 'HTR010',
                    'HTR012', 'HTR105', 'HTR107']

    def check_status(self):
        super().check_status()

        # dry run prefix
        if self.dry_run: prefix = '[DRY RUN] '
        else:            prefix = ''

        # check AV autocontrol status
        for av in ['AV020', 'AV021']:
            if self.devices[av].is_autoenable:
                msg = f'{prefix}{av} autocontrol is enabled when it should be disabled'
                if self.dry_run:
                    self.log(msg)
                else:
                    raise RuntimeError(msg)

        # check autostat enable (should be off)
        for pid in ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']:
            if self.get_odb(f'/Equipment/{pid}/Settings/Enabled'):
                msg = f'{prefix}{pid} is enabled when it should be disabled'
                if self.dry_run:
                    self.log(msg)
                else:
                    raise RuntimeError(msg)

        # check that heaters are zero
        for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
            if self.devices[htr].readback != 0:
                msg = f'{prefix}{htr} should have setpoint zero, but is {self.devices[htr].readback} {self.devices[htr].readback_units}'
                if self.dry_run:
                    self.log(msg)
                else:
                    raise RuntimeError(msg)

    def run(self, pt_thresh=3):

        self.wait_until_lessthan('PT004', pt_thresh)
        self.wait_until_lessthan('PT005', pt_thresh)

        self.devices.BP001.off()
        self.devices.AV024.close()
        self.devices.AV025.close()

class StartRegeneration(CryoScript):

    devices_open = ['AV008', 'AV010', 'AV011', 'AV012', 'AV014', 'AV019', 'AV020',
                    'AV023', 'AV026', 'AV027', 'AV029', ]

    devices_closed = ['AV007', 'AV009', 'AV013', 'AV015', 'AV016', 'AV017', 'AV018',
                      'AV021', 'AV022', 'AV024', 'AV025', 'AV028', 'AV030',
                      'AV031', 'AV032', 'AV034',]

    devices_off = ['BP001', 'BP002']

    devices_on =  [ 'CP001', 'CP101', 'MP001', 'MP002', 'MFC001', 'HTR010',
                    'HTR012', 'HTR105', 'HTR107']

    def exit(self):
        if self.run_state == 'startup':
            self.devices.BP002.off()
            self.devices.CP001.on()
            self.devices.CP101.on()

    def run(self, temperature=180, fm208_at_least=5):

        self.run_state = 'startup'
        self.devices.BP002.on()
        self.devices.CP001.off()
        self.devices.CP101.off()
        self.wait_until_lessthan('CG003', 0.2)

        # double check that security valves are still closed
        for av in ['AV025', 'AV024', 'AV032']:
            if self.devices[av].is_open:
                msg = f'{av} is open when it should be closed'
                if self.dry_run:
                    self.log('[DRY RUN] ' + msg)
                else:
                    raise RuntimeError(msg)
            elif self.dry_run:
                self.log(f'[DRY RUN] {av} is closed as it should')

        # open purifier to atmosphere
        self.run_state = None   # safe operating mode, disable exit strategy
        self.devices.AV050.open()
        self.devices.AV051.open()

        # turn off pumps
        self.devices.MP001.off()
        self.devices.MP002.off()

        # close other valves in the panel
        for av in ['AV008', 'AV010', 'AV011', 'AV012', 'AV014', 'AV019', 'AV020',
                   'AV023', 'AV027', 'AV029']:
            self.devices[av].close()

        # set heaters
        for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
            self.devices[htr].set(0)

            # double check on status - if it fails no risk to system, but will be slow
            if self.devices[htr].is_off:
                raise RuntimeError(f'{htr} is off!')

        # enable autostat control
        for pid in ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']:
            self.set_odb(f'/Equipment/{pid}/Settings/target_setpoint', temperature)
            self.set_odb(f'/Equipment/{pid}/Settings/Enabled', True)

        # wait for FM208 to start increasing
        self.wait_until_greaterthan('FM208', fm208_at_least)

class StopRegeneration(CryoScript):
    devices_closed = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
                      'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
                      'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
                      'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
                      'AV032']
    devices_off = ['AV034', 'BP001']

    devices_on = ['HTR010', 'HTR012', 'HTR105', 'HTR107']

    def run(self, fm208_thresh):

        # Block execution until FM208 is below threshold
        self.wait_until_lessthan('FM208', fm208_thresh)

        # turn off autostat enable
        pids = ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']
        for pid in pids:
            self.set_odb(f'/Equipment/{pid}/Settings/Enabled', False)

        # set heater setpoints to zero
        for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
            self.devices[htr].set(0)

        # Close valves to atmosphere
        self.devices.AV050.close()
        self.devices.AV051.close()

        # turn off pump
        self.devices.BP002.off()

# RUN SCRIPT ==============================================================
# For best protections of cryostat on error, run inside of "with" statement

# with StartRecovery(dry_run=True) as script:
#    script()

# with StopRecovery(dry_run=True) as script:
#    script(pt_thresh=3)

# with StartRegeneration(dry_run=True) as script:
#    script(temperature=180)

# with StopRegeneration(dry_run=True) as script:
#     script(fm208_thresh = 0.25)

# with StartCooling(dry_run=True) as script:
#     script(temperature = 45)

# with StopCooling(dry_run=True) as script:
#     script(temperature = 45)