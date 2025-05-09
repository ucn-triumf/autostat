#!/usr/bin/python3
# run with "nohup ./he_purifier.py &" to keep the code running in the background even if disconnected
# Transition the He purifier from regeneration to cooling
# Derek Fujimoto
# May 2025

import time
from CryoScript import CryoScript
from collections.abc import Iterable

# make scripts ------------------------------------------------------------
class StartCooling(CryoScript):
    """Start cooling to target temperature"""

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
    """Pause execution until target temperature is reached"""

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
                if self.dry_run:    self.log(msg)
                else:               raise RuntimeError(msg)

            elif self.dry_run:
                self.log(f'{pid} is enabled')

    def run(self, temperature):

        # check setpoints of PID autostat
        for pid in ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']:
            setpoint = self.get_odb(f'/Equipment/{pid}/Settings/target_setpoint')
            if setpoint != temperature:
                msg = f'{pid} setpoint ({setpoint:.1f}K) is not as it should be! Undefined system state, exiting.'
                if self.dry_run:    self.log(msg)
                else:               raise RuntimeError(msg)
            elif self.dry_run:
                self.log(f'{pid} setpoint is {setpoint:.1f}K')

        # wait for the temperature to drop
        self.wait_until_lessthan('TS511', temperature+0.1)
        self.wait_until_lessthan('TS513', temperature+0.1)

class StartCirculation(CryoScript):
    """Start the circulation of isopure"""

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
        # self.devices.AV020.disable_auto()

        # close MFC
        self.devices.MFC001.close()

        # double check valves to atmosphere are closed
        self.devices.AV032.close()
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

        # connect to purifier
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
        # self.devices.AV020.enable_auto()
        # self.devices.AV021.enable_auto()

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

class StopCirculation(CryoScript):
    """Wait until integrated volume rises above threshold, if clog detected, close AV021 and AV022"""

    devices_open = ['AV025', 'AV027', 'AV029', 'AV010', 'AV011', 'AV012',
                    'AV014', 'AV019', 'AV020', 'AV021', 'AV022', 'AV024']
    devices_closed=['AV026', 'AV023', 'AV030', 'AV028', 'AV009', 'AV032',
                    'AV013', 'AV017', 'AV016', 'AV050', 'AV051']

    devices_on = ['MP001', 'MP002', 'MFC001', 'CP001', 'CP101', 'BP001',
                  'HTR010', 'HTR012', 'HTR105', 'HTR107', ]
    devices_off = ['BP002']

    def exit(self):
        if self.run_state is None:
            return

        elif self.run_state == 'circulating':
            self.devices.AV021.close()
            self.devices.AV022.close()
            self.devices.MP001.off()
            self.devices.MP002.off()

    def run(self, volume_SL, pt009_thresh, pt001_thresh, pt_overtime_s=180, mfc_nonzero_thresh=0.5, print_dt=900):
        """ Integrate flow through MFC001
        Args:
            volume_SL (float): volume at which to stop circulation in SL
            pt009_thresh (tuple): (low, high) bounds for pt009 in mbar(a). If exceeded, close AV021 and AV020
            pt001_thresh (tuple): (low, high) bounds for pt001 in mbar(a). If exceeded, close AV021 and AV020
            pt_overtime_s (float): duration in seconds for how long pressure threshold exceeded before closing AV021 and AV020
            mfc_nonzero_thresh (float): ignore mfc readback less than this value in SL/min (background)
            print_df (float): duration in seconds between print statements of how much volume was flowed
        """

        MFC001 = self.devices.MFC001
        PT005 = self.devices.PT005

        # check inputs
        if not isinstance(pt009_thresh, Iterable) or len(pt009_thresh) != 2:
            raise RuntimeError(f'Bad pt009_thresh input. Must be iterable of length 2')
        if not isinstance(pt001_thresh, Iterable) or len(pt001_thresh) != 2:
            raise RuntimeError(f'Bad pt001_thresh input. Must be iterable of length 2')

        self.run_state = 'circulating'

        # calculate volume circuated from readback of MFC001, pause execution until exceeded
        volume = 0
        t0 = time.time()
        t0_print = time.time()
        t0_overpressure = time.time()
        last_updated = 0
        while volume < volume_SL and volume_SL > 0:

            # check for clogs - if true, end early
            if MFC001.setpoint > 30 and MFC001.readback < 5 and PT005.readback < 200 and not self.dry_run:
                self.log(f'Purifier clog detected! MFC readback is {MFC001.readback:.2f} {MFC001.readback_units} and PT005 readback is {PT005.readback:.2f} {PT005.readback_units}, even though MFC001 is set to {MFC001.setpoint:.2f}{MFC001.setpoint_units}')
                self.devices.AV021.close()
                self.devices.AV022.close()
                break

            # check for overpressure
            pt001 = self.devices.PT001.readback
            pt009 = self.devices.PT009.readback

            if (pt001_thresh[0] < pt001 < pt001_thresh[1]) and (pt009_thresh[0] < pt009 < pt009_thresh[1]):
                t0_overpressure = time.time()

            # check for overpressure too long, protect AV020 and AV021
            t1_overpressure = time.time()
            if t1_overpressure-t0_overpressure > pt_overtime_s:
                msg = f'PT009 or PT001 out of bounds for {t1_overpressure-t0_overpressure:.1f} seconds! Exiting after circulating {volume:.0f} SL'
                self.log(msg, True)
                self.exit()
                raise RuntimeError(msg)

            # flow rate in SL/s
            rate = MFC001.readback / 60
            t1 = time.time()

            # check if epics variable updated
            tupdated = MFC001.pv[MFC001.readback_name].timestamp
            if tupdated == last_updated:
                continue
            last_updated = tupdated

            # check if MFC001 is above threshold and update total volume
            if MFC001.readback > mfc_nonzero_thresh:
                volume += rate * (t1-t0)
            t0 = t1

            # print volume circulated
            if (time.time()-t0_print) > print_dt:
                t0_print = time.time()
                self.log(f'Circulated {volume:.0f} SL')

            # sleep
            time.sleep(1)

            # dry run
            if self.dry_run:
                break

        # if ended early still print volume
        if volume < volume_SL:
            self.log(f'Circulated {volume:.0f} SL')

class StartRecovery(CryoScript):
    """Start the isopure recovery process: pump out the pipes before regeneration"""

    devices_open = ['AV010', 'AV011', 'AV012', 'AV014', 'AV019', 'AV020',
                    'AV024', 'AV025', 'AV027', 'AV029', ]

    devices_closed = ['AV026', 'AV023', 'AV030', 'AV028', 'AV009', 'AV032',
                      'AV013', 'AV017', 'AV016', 'AV050', 'AV051']

    devices_off = ['BP002']

    devices_on =  [ 'BP001', 'CP001', 'CP101', 'MP001', 'MP002', 'MFC001',
                    'HTR010', 'HTR012', 'HTR105', 'HTR107']

    def exit(self):
        # if self.run_state == 'av auto disabled':
        #     for av in ['AV020', 'AV021']:
        #         self.devices[av].enable_auto()
        return

    def run(self, temperature=30):

        # av autocontrol off
        # self.run_state = 'av auto disabled'
        # for av in ['AV020', 'AV021']:
        #     self.devices[av].disable_auto()

        # heater autocontrol set to 30K
        for pid in ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']:
            self.set_odb(f'/Equipment/{pid}/Settings/target_setpoint', temperature)

        # valves
        self.devices.AV021.close()
        self.devices.AV022.close()
        self.devices.AV023.open()
        self.devices.AV008.open()
        self.devices.AV026.open()

class StopRecovery(CryoScript):
    """Wait until pressure is low, isopure is pumped out. Then close AV024, AV025 and turn off BP001"""

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

        # check AV autocontrol status
        # for av in ['AV020', 'AV021']:
        #     if self.devices[av].is_autoenable:
        #         msg = f'{av} autocontrol is enabled when it should be disabled'
        #         if self.dry_run:
        #             self.log(msg)
        #         else:
                    # raise RuntimeError(msg)

        # check autostat enable (should be off)
        for pid in ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']:
            if self.get_odb(f'/Equipment/{pid}/Settings/Enabled'):
                msg = f'{pid} is enabled when it should be disabled'
                if self.dry_run:
                    self.log(msg)
                else:
                    raise RuntimeError(msg)

        # check that heaters are zero
        for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
            if self.devices[htr].readback != 0:
                msg = f'{htr} should have setpoint zero, but is {self.devices[htr].readback} {self.devices[htr].readback_units}'
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
    """Start the regeneration process, then wait for flow to appear on FM208"""

    devices_open = ['AV008', 'AV010', 'AV011', 'AV012', 'AV014', 'AV019', 'AV020',
                    'AV023', 'AV026', 'AV027', 'AV029', ]

    devices_closed = ['AV007', 'AV009', 'AV013', 'AV015', 'AV016', 'AV017', 'AV018',
                      'AV021', 'AV022', 'AV024', 'AV025', 'AV028', 'AV030',
                      'AV031', 'AV032', 'AV034',]

    devices_off = ['BP001', 'BP002']

    devices_on =  [ 'CP001', 'CP101', 'MP001', 'MP002', 'MFC001', 'HTR010',
                    'HTR012', 'HTR105', 'HTR107']

    def exit(self):

        if self.run_state is None:
            return

        elif 'startup' in self.run_state:
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
                    self.log(msg)
                else:
                    raise RuntimeError(msg)
            elif self.dry_run:
                self.log(f'{av} is closed as it should')

        # turn off pumps
        self.devices.MP002.off()
        self.devices.MP001.off()

        # close other valves in the panel
        for av in ['AV008', 'AV010', 'AV011', 'AV012', 'AV014', 'AV019', 'AV020',
                   'AV023', 'AV027', 'AV026', 'AV029']:
            self.devices[av].close()

        # open purifier to atmosphere
        self.run_state = None   # safe operating mode, disable exit strategy
        self.devices.AV050.open()
        self.devices.AV051.open()

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

        # time delay to skip that spike
        self.log('Waiting a grace period of 30 s')
        if not self.dry_run:
            time.sleep(30)

        # wait for FM208 to start increasing or the temperature to hit half the target
        def wait_condition():
            if self.devices.FM208.readback > fm208_at_least:
                return True

            TSlist = ['TS512', 'TS510', 'TS511', 'TS513']
            if any([self.devices[ts].readback > temperature/2 for ts in TSlist]):
                return True

            return False

        # print a nice message during wait times
        def wait_message():
            FM208 = self.devices.FM208
            TS510 = self.devices.TS510
            return f'{FM208.path} is {FM208.readback:.3f} {FM208.readback_units}, and {TS510.path} is {TS510.readback:.3f} {TS510.readback_units}. Waiting...'

        # run the wait procedure
        FM208 = self.devices.FM208
        if FM208.readback < fm208_at_least:
            self.log(f'Waiting for {FM208.path} to rise above {fm208_at_least} {FM208.readback_units}, currently {FM208.readback:.3f} {FM208.readback_units}')

            self.wait(wait_condition, wait_message)

        self.log(f'{FM208.path} readback ({FM208.readback:.2f} {FM208.readback_units}) is greater than {fm208_at_least} {FM208.readback_units}')

class StopRegeneration(CryoScript):
    """Wait until FM208 drops below threshold and the trap is at tempertaure then stop the regeneration processs"""

    devices_closed = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
                      'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
                      'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
                      'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
                      'AV032']
    devices_off = ['AV034', 'BP001']

    devices_on = ['HTR010', 'HTR012', 'HTR105', 'HTR107']

    def run(self, temperature, fm208_thresh):

        # block until at temperature
        self.wait_until_greaterthan('TS512', temperature-0.1)
        self.wait_until_greaterthan('TS510', temperature-0.1)
        self.wait_until_greaterthan('TS511', temperature-0.1)
        self.wait_until_greaterthan('TS513', temperature-0.1)

        # block until FM208 is below threshold
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

if __name__ == "__main__":

    # THESE SCRIPTS ARE WORKING
    # Comment out steps to not run that step

    with StopCirculation() as script:
        script(volume_SL=0) # 0 to disable

    with StartRecovery() as script: # does not toggle or check AV020 and AV021 autocontrol
       script(temperature=30)

    with StopRecovery() as script:
       script(pt_thresh=4.25)

    with StartRegeneration() as script:
       script(temperature=180, fm208_at_least=1)

    with StopRegeneration() as script:
        script(temperature=180, fm208_thresh = 0.25)

    with StartCooling() as script:
        script(temperature = 30)

    with StopCooling() as script:
        script(temperature = 30)

    # BELOW THIS POINT IS DRY_RUN ONLY (UNIMPLEMENTED)

