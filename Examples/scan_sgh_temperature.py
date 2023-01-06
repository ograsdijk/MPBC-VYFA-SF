from mpbc_vyfa_sf import MPBAmplifier, LaserState

import matplotlib.pyplot as plt
import numpy as np
import time
import csv
from rich.progress import track
from rich.console import Console

com_port = "COM4"
scan_range = 3  # scan range in celcius to scan around the current setpoint
dt = 2
points = 31

console = Console()

amp = MPBAmplifier(com_port)

current_temperature_setpoint = amp.shg_temperature_setpoint

# check if power stabilization is enabled and disable if it is
power_stabilization = amp.power_stabilization
if power_stabilization:
    amp.power_stabilization = False

# enter test environment to be allowed to change the SHG temperature setpoint
amp.enter_test_environment()

console.print("Enabling the laser", end="\r")
amp.enable_laser()

with console.status("Starting laser") as status:
    while True:
        time.sleep(0.2)
        status.update(
            f"Starting laser: {amp.laser_state.name}, booster current = {amp.booster_current:.1f}"
            f", setpoint = {amp.booster_current_setpoint:.1f}"
        )
        if (amp.laser_state == LaserState(52)) & (
            abs(amp.booster_current - amp.booster_current_setpoint) <= 10
        ):
            tstart = time.time()
            while (time.time() - tstart) < 2:
                status.update(
                    f"Starting laser: {amp.laser_state.name}, booster current = {amp.booster_current:.1f}, "
                    f"setpoint = {amp.booster_current_setpoint:.1f}"
                )
                time.sleep(0.1)
            console.print(
                f"{amp.laser_state.name}: booster current = {amp.booster_current:.1f}, "
                f"setpoint = {amp.booster_current_setpoint:.1f}",
            )
            break

# give the amplifier some time to finish starting up and going to the first temperature
with console.status("Setting the first temperature point and waiting 10s to stabilize"):
    amp.shg_temperature_setpoint = current_temperature_setpoint - scan_range / 2
    time.sleep(10)

data = []
for T in track(
    np.linspace(
        current_temperature_setpoint - scan_range / 2,
        current_temperature_setpoint + scan_range / 2,
        points,
    ),
    description="Scanning SHG temperature",
):
    amp.shg_temperature_setpoint = T
    time.sleep(dt)
    data.append((T, amp.shg_temperature, amp.output_power))

amp.disable_laser()

amp.shg_temperature_setpoint = current_temperature_setpoint
amp.power_stabilization = power_stabilization

xsetpoint, x, y = zip(*data)

# write data to csv
with open("shg_temperature_scan.csv", "w", newline="") as csv_file:
    writer = csv.writer(csv_file, delimiter=",")
    writer.writerow(
        ["SHG temperature setpoint [C]", "SHG temperature [C]", "output power [mW]"]
    )
    for d in data:
        writer.writerow(d)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x, y, ".-", lw=2, ms=12)
ax.set_xlabel("temperature [C]")
ax.set_ylabel("power [mW]")
ax.grid(True)

plt.show()
