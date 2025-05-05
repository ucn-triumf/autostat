#!/usr/bin/python3
# run with "nohup ./he_purifier.py &" to keep the code running in the background even if disconnected
# Transition the He purifier from regeneration to cooling
# Derek Fujimoto
# May 2025

import epics
import midas, midas.client
import time, datetime
import sys, time, logging
from logging.handlers import RotatingFileHandler
from EpicsDevice import get_device
from utils import wait_until_lessthan, set_odb

# TODO: Make elog entry on completion?
# TODO: stop_circulation should check for clogs
# TODO: cleaner management of scripts and logging

# setup logging
logger = logging.getLogger('root')
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

# setup file handler with rotating file handling
rfile_handler = RotatingFileHandler('he_purifier.log', mode='a',
                                    maxBytes=5*1024*1024, backupCount=1,
                                    encoding=None, delay=False)
rfile_handler.setFormatter(log_formatter)
rfile_handler.setLevel(logging.INFO)
logger.addHandler(rfile_handler)

# setup file handler for messages from this execution
file_handler = logging.FileHandler('thishe_purifier.log', mode='w',
                                   encoding=None, delay=False)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

# connect to midas client
client = midas.client.MidasClient("he_purifier")

# setup logging/messaging functions
def log(msg, is_error=False):
    if is_error:
        logger.error(msg)
        client.trigger_internal_alarm('he_purifier', msg,
                                      default_alarm_class='Alarm')
    else:
        logger.info(msg)
    client.msg(msg, is_error=is_error)

# start
log('Started he_purifier')

# setup epics devices to read/write from
device_names = ['UCN2:CRY:TS512',
                'UCN2:CRY:TS513',
                'UCN2:HE3:CP101',
                'UCN2:HE3:HTR105',
                'UCN2:HE3:HTR107',
                'UCN2:HE4:FM208',
                'UCN2:ISO:AV001',
                'UCN2:ISO:AV003',
                'UCN2:ISO:AV004',
                'UCN2:ISO:AV007',
                'UCN2:ISO:AV008',
                'UCN2:ISO:AV009',
                'UCN2:ISO:AV010',
                'UCN2:ISO:AV011',
                'UCN2:ISO:AV012',
                'UCN2:ISO:AV013',
                'UCN2:ISO:AV014',
                'UCN2:ISO:AV015',
                'UCN2:ISO:AV016',
                'UCN2:ISO:AV017',
                'UCN2:ISO:AV018',
                'UCN2:ISO:AV019',
                'UCN2:ISO:AV020',
                'UCN2:ISO:AV021',
                'UCN2:ISO:AV022',
                'UCN2:ISO:AV023',
                'UCN2:ISO:AV024',
                'UCN2:ISO:AV025',
                'UCN2:ISO:AV026',
                'UCN2:ISO:AV027',
                'UCN2:ISO:AV028',
                'UCN2:ISO:AV029',
                'UCN2:ISO:AV030',
                'UCN2:ISO:AV031',
                'UCN2:ISO:AV032',
                'UCN2:ISO:AV034',
                'UCN2:ISO:AV050',
                'UCN2:ISO:AV051',
                'UCN2:ISO:CP001',
                'UCN2:ISO:BP001',
                'UCN2:ISO:BP002',
                'UCN2:ISO:HTR010',
                'UCN2:ISO:HTR012',
                'UCN2:ISO:MFC001',
                'UCN2:ISO:MP001',
                'UCN2:ISO:MP002',
                'UCN2:ISO:PT050',
            ]

# create epics devices to monitor
device = {name.split(':')[2]:get_device(name, log) for name in device_names}
log('Connected to all requested EPICS devices')

# DEFINE PROCEDURE FOR EACH STAGE
def start_cooling(temperature=70):

    # check valve states. These should be closed:
    avlist = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
              'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
              'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
              'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
              'AV032', 'AV034', 'AV050', 'AV051']

    for av in avlist:
        if device[av].is_open:
            msg = f'{av} is open when it should be closed! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check that pumps are off
    pumplist = ['BP001', 'BP002']
    for pump in pumplist:
        if device[pump].is_open:
            msg = f'{pump} is on when it should be off! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # turn on heaters and set setpoints to zero
    for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
        device[htr].set(0)
        # device[htr].on() # TODO: Uncomment this line once permissions are given

    # wait until pressure is low before turning on the pump
    wait_until_lessthan(device['PT050'], 30, log)

    # turn on pump
    device['CP101'].on()

    # block until temps are low
    wait_until_lessthan(device['TS512'], 300, log)
    wait_until_lessthan(device['TS513'], 300, log)

    # turn on pump
    device['CP001'].on()

    # turn on autostat enable and change setpoints
    pids = ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']
    for pid in pids:
        set_odb(client, f'/Equipment/{pid}/Settings/target_setpoint', temperature, log)
        set_odb(client, f'/Equipment/{pid}/Settings/Enabled', True, log)

    # you are now cooling!
    log(f'System is now cooling to {temperature}')

def stop_cooling(temperature=70):
    """Block execution until cold"""


    # check valve states. These should be closed:
    avlist = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
              'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
              'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
              'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
              'AV032', 'AV034', 'AV050', 'AV051']

    for av in avlist:
        if device[av].is_open:
            msg = f'{av} is open when it should be closed! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check that pumps are off
    pumplist = ['BP001', 'BP002']
    for pump in pumplist:
        if device[pump].is_open:
            msg = f'{pump} is on when it should be off! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check that heaters are on and setpoints are properly set
    for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
        if device[htr].is_off:
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
    wait_until_lessthan(device['TS510'], temperature+0.1, log)
    wait_until_lessthan(device['TS511'], temperature+0.1, log)
    wait_until_lessthan(device['TS512'], temperature+0.1, log)
    wait_until_lessthan(device['TS513'], temperature+0.1, log)

    log(f'System cooled to {temperature}K')

def start_circulation():

    # check purifier temperatures
    for ts in ['TS510', 'TS511', 'TS512', 'TS513']:
        if device[ts].readback > 100:
            msg = f'{ts} temperature is too high ({device[ts].readback}K). Wait until below 100 K. Exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check valve states. These should be closed:
    avlist = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
              'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
              'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
              'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
              'AV032', 'AV034', 'AV050', 'AV051']

    for av in avlist:
        if device[av].is_open:
            msg = f'{av} is open when it should be closed! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check that pumps are off
    pumplist = ['BP001', 'BP002']
    for pump in pumplist:
        if device[pump].is_open:
            msg = f'{pump} is on when it should be off! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # disable AV020 auto control
    device['AV020'].disable_auto()

    # close MFC
    device['MFC001'].close()

    # double check valves to atmosphere are closed
    if device['AV032'].is_open:
        device['AV032'].close()
    if device['AV051'].is_open:
        device['AV051'].close()

    # turn on MP002
    device['AV014'].open()
    device['AV017'].open()
    device['AV015'].open()
    device['MP002'].on()

    # do I wait for a pressure to drop? # TODO: Check this step
    time.sleep(5)
    device['AV017'].close()
    device['AV015'].close()

    # start MP001
    device['AV019'].open()
    device['AV020'].open()
    device['MP001'].on()
    device['AV012'].open()

    # connect pumps to rest of system
    device['AV011'].open()
    device['AV010'].open()
    device['AV029'].open()
    device['AV027'].open()

    # connect to purifier # TODO: check that these open as they should!
    device['AV025'].open()
    device['AV024'].open()

    # Finalize path
    device['AV022'].open()
    device['AV021'].open()

    # Start MFC001
    device['MFC001'].set(0)
    device['MFC001'].on()
    device['MFC001'].set(30)
    time.sleep(5)
    log(f'MFC001 reads {device["MFC001"].readback} {device["MFC001"].readback_units} after initial open and setpoint {device["MFC001"].setpoint} {device["MFC001"].setpoint_units}')

    # start BP001
    device['BP001'].on()

    # open MFC001
    device['MFC001'].set(50)

    # enable auto control
    device['AV020'].enable_auto()
    device['AV021'].enable_auto()

    # double-check valve states. These should be closed:
    avlist = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV013',
              'AV015', 'AV017', 'AV018', 'AV023', 'AV024', 'AV026', 'AV028',
              'AV030', 'AV031', 'AV032', 'AV034', 'AV050', 'AV051']

    for av in avlist:
        if device[av].is_open:
            msg = f'{av} is open when it should be closed! Closing to protect Isopure.'
            log(msg, True)
            device[av].close()

    # double-check valve states. These should be open:
    avlist = ['AV010', 'AV011', 'AV012', 'AV014', 'AV016', 'AV019', 'AV020',
              'AV021', 'AV022', 'AV024', 'AV025', 'AV027', 'AV029']

    for av in avlist:
        if device[av].is_closed:
            msg = f'{av} is closed when it should be open! Opening to protect bad pressure buildup.'
            log(msg, True)
            device[av].open()

def stop_circulation(hours=None, volume=None):
    pass

def start_recovery():
    pass

def stop_recovery():
    pass

def start_regeneration():
    pass

def stop_regeneration():

    # check valve states. These should be closed:
    avlist = ['AV001', 'AV003', 'AV004', 'AV007', 'AV008', 'AV009', 'AV010',
              'AV011', 'AV012', 'AV013', 'AV014', 'AV015', 'AV016', 'AV017',
              'AV018', 'AV019', 'AV020', 'AV021', 'AV022', 'AV023', 'AV024',
              'AV025', 'AV026', 'AV027', 'AV028', 'AV029', 'AV030', 'AV031',
              'AV032', 'AV034']

    for av in avlist:
        if device[av].is_open:
            msg = f'{av} is open when it should be closed! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check that pumps are off
    pumplist = ['BP001']
    for pump in pumplist:
        if device[pump].is_on:
            msg = f'{pump} is on when it should be off! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # check that heaters are on
    for htr in ['HTR010', 'HTR012', 'HTR105', 'HTR107']:
        if device[htr].is_off:
            msg = f'{htr} is off when it should be on! Undefined system state, exiting.'
            log(msg, True)
            raise RuntimeError(msg)

    # Block execution until FM208 is below threshold
    wait_until_lessthan(device['FM208'], 0.25, log)

    # turn off autostat enable
    pids = ['PID_PUR_ISO70K', 'PID_PUR_ISO20K', 'PID_PUR_HE20K', 'PID_PUR_HE70K']
    for pid in pids:
        set_odb(client, f'/Equipment/{pid}/Settings/Enabled', False, log)

    # set heater setpoints to zero
    htrs = ['HTR010', 'HTR012', 'HTR105', 'HTR107']
    for htr in htrs:
        device[htr].set(0)

    # Close valves to atmosphere
    device['AV050'].close()
    device['AV051'].close()

    # turn off pump
    device['BP002'].off()

    # done
    log(f'System has finished regenerating')

# RUN SCRIPT ==============================================================

# connect to midas as a one-time client
try:

    # wait for FM208 to rise - ensure that something is regenerated
    #wait_until_greaterthan(device['FM208'], 1, log)

    stop_regeneration()
    start_cooling(temperature=40)
    # stop_cooling(temperature=70)
    # start_circulation()
    # stop_circulation(hours=2)
    # start_recovery()
    # stop_recovery()
    # start_regeneration()

    # end
    log('Finished he_purifier')

finally:
    client.disconnect()
