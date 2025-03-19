# Automatic Control of Cryostat EPICS devices

You need write permissions for the required EPICS devices on your machine to run these.

Dependencies:

```
midas
pyepics
simple_pid
```

## AutoPurify

This runs the cryostat in heater-on mode. It uses a PID loop to control HTR204 in order to keep PT206 to some target pressure. To start run the `autopurify` program in the ODB Programs page

### Control logic

* Use the simple_pid package to get the setpoints
* Wait an extended duration between control operations
* If PT206 is above safety threshold, then open FPV201 to 100% for at least 30s to reduce pressure
* If PT206 is below threshold and FPV201 is 100% open, then reset FPV201 to the value prior to the script changing its value
* If at any point FPV201 or HTR204 are turned off, stop PID control
* If at any point HTR204 has changed by more than 1 mA between control operations, then stop PID control

### ODB settings (/Equipment/AutoPurify/Settings)
* `P`: proportional control value
* `I`: intregral control value
* `D`: differential control value
* `setpoint`: target for PT206 in mbar
* `time_step_s`: duration between control operations in seconds
* `pressure_high_thresh`: threshold pressure of PT206 in mbar, above which FPV201 opens
* `output_limit_low`: lower bound on possible setpoint of HTR204
* `output_limit_high`: upper bound on possible setpoint of HTR204
* `proportional_on_measurement`: Whether the proportional term should be calculated on the input directly rather than on the error (which is the traditional way). Using proportional-on-measurement avoids overshoot for some types of systems.
* `differential_on_measurement`: Whether the differential term should be calculated on the input directly rather than on the error (which is the traditional way).

When settings are changed in the ODB they are also changed for the control script, no restart required

