# Run the purification process using the cryostat
# Holds PV206 to some target value below threshold of 1500 mbar by running HTR204
# Derek Fujimoto
# Mar 2025

import epics
from simple_pid import PID
import time
from tqdm import tqdm
import tkinter
from datetime import datetime

# settings
dt = 60 # timestep between control operations in seconds
panic_threshold = 1480 # above this use FPV201 to reduce the pressure

# get epics readback variables to read and write
# by default uses the monitor backend (desired)
htr204_cur = epics.PV('UCN2:HE4:HTR204:CUR')
htr204_staton = epics.PV('UCN2:HE4:HTR204:STATON')
fpv201_pos = epics.PV('UCN2:HE4:FPV201:POS')
fpv201_staton = epics.PV('UCN2:HE4:FPV201:STATON')
pt206_rdpress = epics.PV('UCN2:HE4:PT206:RDPRESS')

# setup PID controller
# see https://simple-pid.readthedocs.io/en/latest/reference.html
pid = PID(Kp = 1,                               # P
          Ki = 0,                               # I
          Kd = 0,                               # D
          setpoint = 1400,                      # target pressure
          output_limits = (0, 1000),            # HTR204 setpoint limits
          proportional_on_measurement = False,  # Whether the proportional term should be calculated on the
                                                # input directly rather than on the error.  Using
                                                # proportional-on-measurement avoids overshoot for some
                                                # types of systems.
          differential_on_measurement = False,  # Whether the differential term should be calculated on
                                                # the input directly rather than on the error
          starting_output = htr204_cur.get()    # The starting point for the PID’s output.
          )

# print startup message
print(f"""Starting autopurify.py

    Control PV: {htr204_cur.pvname}
    Monitor PV: {pt206_rdpress.pvname}

    Setpoint: {pid.setpoint}
    P:        {pid.tunings[0]}
    I:        {pid.tunings[1]}
    D:        {pid.tunings[2]}

    Output limited to {pid.output_limits}
    proportional_on_measurement: {pid.proportional_on_measurement}
    differential_on_measurement: {pid.differential_on_measurement}
""")

# setup start of run values
t0 = time.time()
htr204_t0 = htr204_cur.get()
t_panic = 0

# make progress bar
bar = tqdm(desc='autopurify',
           total=dt,
           leave=True,
           )

# RUN
while True:

    # check that controls are active
    if htr204_staton.get() != 1:
        tkinter.messagebox.showerror('Error: HTR204 is not on',
            f'HTR204 is not on - stopping control loop\n\n({datetime.now()})')
        break

    if fpv201_staton.get() != 1:
        tkinter.messagebox.showerror('Error: FPV201 is not on',
            f'FPV201 is not on - stopping control loop\n\n({datetime.now()})')
        break

    # check if htr setpoint changed significantly between calls
    if abs(htr204_cur.get() - htr204_t0) > 1:
        tkinter.messagebox.showerror('Error: HTR204 setpoint mismatch',
            f'HTR204: Setpoint does not match previously set value - stopping control loop\n\n({datetime.now()})')
        break

    # get time and iterate progress bar
    t1 = time.time()
    bar.update(t1-t0)

    # check if panic state
    if pt206_rdpress.get() > panic_threshold:
        fpv201_pos.put(100)
        t_panic = time.time()
        tkinter.messagebox.showwarning('PT206 Pressure high',
            f'PT206: Pressure too high! Opening FPV201 to 100%\n\n({datetime.now()})')

    # panicking: wait at least 30 s for the pressure to go down
    elif fpv201_pos.get() > 0 and (t1 - t_panic) > 30:
        fpv201_pos.put(0)

    # new control value
    if t1-t0 >= dt:

        # apply control operation
        htr204_cur.put(pid(pt206_rdpress.get()))

        # reset progress bar
        bar.reset()

        # new t0 and htr setpoint value to check against
        t0 = t1
        htr204_t0 = htr204_cur.get()