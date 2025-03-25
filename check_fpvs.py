#!/usr/bin/python3
# Jeff wrote this line.  Check FPVs is based on...
# Run the purification process using the cryostat
# Derek Fujimoto
# Mar 2025



"""
Checks FPVs to make sure they are in the correct pattern
"""

import midas
import midas.frontend
import epics
import time
import collections

# must be lower than this
FPV201_START_LIMIT = 30
    
# get epics readback variables to read and write
# by default uses the monitor backend (desired)
pv = {'setvar': epics.PV('UCN2:HE4:HTR204:CUR'), # set this variable
      'rdvar': epics.PV('UCN2:HE4:PT206:RDPRESS'), # control this variable to be at setpoint
      'htr204_staton': epics.PV('UCN2:HE4:HTR204:STATON'),
      'fpv201_pos': epics.PV('UCN2:HE4:FPV201:POS'),
      'fpv201_staton': epics.PV('UCN2:HE4:FPV201:STATON'),
      'fpv201_read': epics.PV('UCN2:HE4:FPV201:RDDACP'), # Jeff added the following so that we can check the status of all FPV's and AV203
      'fpv202_read': epics.PV('UCN2:HE4:FPV202:RDDACP'),
      'fpv203_read': epics.PV('UCN2:HE4:FPV203:RDDACP'),
      'fpv204_read': epics.PV('UCN2:HE4:FPV204:RDDACP'),
      'fpv205_read': epics.PV('UCN2:HE4:FPV205:RDDACP'),
      'fpv206_read': epics.PV('UCN2:HE4:FPV206:RDDACP'),
      'fpv207_read': epics.PV('UCN2:HE4:FPV207:RDDACP'),
      'fpv208_read': epics.PV('UCN2:HE4:FPV208:RDDACP'),
      'fpv209_read': epics.PV('UCN2:HE4:FPV209:RDDACP'),
      'fpv211_read': epics.PV('UCN2:HE4:FPV211:RDDACP'),
      'fpv212_read': epics.PV('UCN2:HE4:FPV212:RDDACP'),
      'av203_staton': epics.PV('UCN2:HE4:AV203:STATON'),
      'lvl203_read': epics.PV('UCN2:HE4:LVL203:RDLVL'),
}

print(f'FPV201 {pv["fpv201_read"].get():.1f}')
print(f'FPV202 {pv["fpv202_read"].get():.1f}')
print(f'FPV203 {pv["fpv203_read"].get():.1f}')
print(f'FPV204 {pv["fpv204_read"].get():.1f}')
print(f'FPV205 {pv["fpv205_read"].get():.1f}')
print(f'FPV206 {pv["fpv206_read"].get():.1f}')
print(f'FPV207 {pv["fpv207_read"].get():.1f}')
print(f'FPV208 {pv["fpv208_read"].get():.1f}')
print(f'FPV209 {pv["fpv209_read"].get():.1f}')
print(f'FPV211 {pv["fpv211_read"].get():.1f}')
print(f'FPV212 {pv["fpv212_read"].get():.1f}')
print(f' AV203 {pv["av203_staton"].get()}')
print(f'LVL203 {pv["lvl203_read"].get():.1f}')


# check to make sure that the pattern of FPV's and AV203 is correct
if (pv['fpv201_read'].get() > FPV201_START_LIMIT
    or pv['fpv202_read'].get() > FPV201_START_LIMIT
    or pv['fpv203_read'].get() < FPV201_START_LIMIT
    or pv['fpv204_read'].get() > FPV201_START_LIMIT
    or pv['fpv205_read'].get() > FPV201_START_LIMIT
    or pv['fpv206_read'].get() > FPV201_START_LIMIT
    or pv['fpv207_read'].get() > FPV201_START_LIMIT
    or pv['fpv208_read'].get() > FPV201_START_LIMIT
    or pv['fpv209_read'].get() < FPV201_START_LIMIT
    or pv['fpv211_read'].get() > FPV201_START_LIMIT
    or pv['fpv212_read'].get() > FPV201_START_LIMIT
    or pv['av203_staton'].get() == 1):
    print('Only FPV203 and FPV209 should be open.')
    print('Check all FPVs and AV203')
else:
    print('All FPVs and AV203 appear to be in the correct state.')
    print('Go ahead and start purifying.')


LVL203_LOWLOW = 10

# check to make sure that LVL203 is ok
if (pv['lvl203_read'].get() < LVL203_LOWLOW):
    print('Warning:  4K reservoir LVL203 is too low!  Save me!')
