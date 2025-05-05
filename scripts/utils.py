# Utility functions
# Derek Fujimoto
# May 2025

import time

# timeout error when turning stuff on/off
class TimeoutError(Exception): pass

def set_odb(client, path, value, log, timeout=10):
    """Set ODB variable

    Args:
        client (midas.client): client object
        path (str): odb path to variable which to set
        value: value to set
        log (handle): function(message is_error=False) which prints or sends logging messages
        timeout (int): timeout in seconds for setting the variable
    """
    t0 = time.time()
    while client.odb_get(path) != value:
        # timeout
        if time.time()-t0 > timeout:
            msg = f'Attempted to set {path} for {timeout} seconds, stuck at {client.odb_get(path)}'
            log(msg, True)
            raise TimeoutError(msg)

        client.odb_set(path, value)
        time.sleep(1)
    log(f'Set {path} to {value}')

def wait_until_greaterthan(device, thresh, log):
    """Block program execution until device readback is above the theshold

    Args:
        device (EpicsDevice): device which should be above threshold
        thresh (float): threshold
        log (handle): function(message is_error=False) which prints or sends logging messages
    """
    n = 0
    while device.readback < thresh:
        if n%15 == 0: # every 15 mins
            log(f'Waiting for {device.path} to rise above threshold {thresh} {device.readback_units}, currently {device.readback:.2f} {device.readback_units}')
        time.sleep(60)
        n += 1
    log(f'{device.path} ({device.readback:.2f} {device.readback_units}) satisfies threshold of {thresh} {device.readback_units}')

def wait_until_lessthan(device, thresh, log):
    """Block program execution until device readback is below the theshold

    Args:
        device (EpicsDevice): device which should be below threshold
        thresh (float): threshold
        log (handle): function(message is_error=False) which prints or sends logging messages
    """
    n = 0
    while device.readback > thresh:
        if n%15 == 0: # every 15 mins
            log(f'Waiting for {device.path} to drop below threshold {thresh} {device.readback_units}, currently {device.readback:.2f} {device.readback_units}')
        time.sleep(60)
        n += 1
    log(f'{device.path} ({device.readback:.2f} {device.readback_units}) satisfies threshold of {thresh} {device.readback_units}')

