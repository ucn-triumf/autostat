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