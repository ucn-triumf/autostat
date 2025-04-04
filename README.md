# Automatic Control of Cryostat EPICS devices

You need write permissions for the required EPICS devices on your machine to run these.

Dependencies:

```
midas
pyepics
simple_pid
```

## List of PID Loops

| Program Name | Control Variable | Target Variable |
| --- | --- | --- |
| [PID_4KPressure (autopurify)](#autopurify) | HTR204 | PT206 |
| PID_20KShield | FPV205 | TS505 |
| PID_100KShield | FPV207 | TS508 |
| PID_TransLineTemp | FPV212 | TS245 |
| PID_Wall2Temp | FPV209 | TS351 |
| PID_ECollar | FPV206 | TS525 |
| PID\_PUR\_HE70K | HTR105 | TS510 |
| PID\_PUR\_ISO70K | HTR010 | TS512 |
| PID\_PUR\_HE20K | HTR107 | TS511 |
| PID\_PUR\_ISO20K | HTR012 | TS513 |


## ODB settings (/Equipment/AutoPurify/Settings)
* `P`: proportional control value
* `I`: intregral control value
* `D`: differential control value
* `target_setpoint`: target for PT206 in mbar
* `inverted_output`: if True, multiply PID by -1 before setting. Used when increasing the control variable should result in decreasing the target variable (e.g. when cooling with a flow meter).
* `time_step_s`: duration between control operations in seconds
* `pressure_high_thresh`: threshold pressure of PT206 in mbar, above which FPV201 opens
* `output_limit_low`: lower bound on possible setpoint of HTR204
* `output_limit_high`: upper bound on possible setpoint of HTR204
* `proportional_on_measurement`: Whether the proportional term should be calculated on the input directly rather than on the error (which is the traditional way). Using proportional-on-measurement avoids overshoot for some types of systems.
* `differential_on_measurement`: Whether the differential term should be calculated on the input directly rather than on the error (which is the traditional way).
* `control_pv`: variable under direct control by the PID loop. Changing this value does not affect the program in any way.
* `target_pv`: variable which we are trying to set to the setpoint. Changing this value does not affect the program in any way.

When settings are changed in the ODB they are also changed for the control script, no restart required

## Adding PID Loops

1. Get write-access for the `ucn` user on `daq01.ucn.triumf.ca` to the specific device you want to control. Note that each physical device may have multiple devices in EPICS for the various readbacks or control features. In EPICS, middle click and drag to see the path of each EPICS device (e.g. on the green part of a slider bar). Be extremely specific in your communication with controls group and be sure to send them the full string of each device. 
2. Check that write-access is enabled. On `ucn@daq01.ucn.triumf.ca`, run the command `cainfo <device name>`.
3. Write a new PID loop controller. The base classes `PIDControllerBase` and `PIDControllerBase_ZeroOnDisable` (found in `PIDControllerBase.py`) both exist to help facilitate this. Ideally you will only need to import and inherit from one of these two classes. See `PIDCtrlPurify.py` or `PIDCtrlEquipment.py` for two collections of these PID loop classes. See class `PIDCtrl_HTR204_PT206` in `PIDCtrlEquipment.py` for an example of a more complicated implementation. 
4. Add your class to `fe_autostat.py` by adding a `add_equipment` line, as is done with the other equipments. 
5. Stop and restart the autostat program in MIDAS. The equipment will be automatically generated in the ODB. 
6. Add a table row in `autostat.html` so the user can set and track the enable status of your new PID loop. See other table rows and copy/paste as needed. Please try to keep this table nicely organized. Updates to the html file are implemented instantaneously, so you can refresh the page to check that it worked. 
7. Update the github repository with your new changes. 
8. Update the controls and interlocks document with your new changes. 

## Removing PID Loops

1. Delete or comment-out the relevant `add_equipment` line in `fe_autostat.py`
2. Delete or comment-out the relevant table rows in `autostat.html`. Updates to the html file are implemented instantaneously, so you can refresh the page to check that it worked. 
3. Stop and restart the autostat program in MIDAS. 
4. Delete the relevant equipment ODB keys. Navigate to `/equipment` then right-click on the equipment you want to get rid of, and select "delete key"
5. Let controls know to remove write-access for any variables no longer being controlled by the PID loop controller. 
6. Check that write-access is disabled. On `ucn@daq01.ucn.triumf.ca`, run the command `cainfo <device name>`.
7. Update the github repository with your new changes. 
8. Update the controls and interlocks document with your new changes. 

## AutoPurify

This runs the cryostat in heater-on mode. It uses a PID loop to control HTR204 in order to keep PT206 to some target pressure.

**Control logic**

* Use the simple_pid package to get the setpoints
* Wait an extended duration between control operations
* If PT206 is above safety threshold, then open FPV201 to 100% for at least 30s to reduce pressure
* If PT206 is below threshold and FPV201 is 100% open, then reset FPV201 to the value prior to the script changing its value
* If at any point FPV201 or HTR204 are turned off, stop PID control
* If at any point HTR204 has changed by more than 1 mA between control operations, then stop PID control
* Added by Jeff:  If FPV203 and FPV209 are above 40% and all others below 40%, run.  Otherwise exit (both when starting autopurify and while running).
