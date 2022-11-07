import csv
import logging
import random
import time
import tkinter as tk
from pathlib import Path
from threading import Thread
from typing import Optional

import pyvisa
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.axes import Axes

# from .amplifier import MPBAmplifier


class Amplifier(Thread):
    def __init__(self):
        super(Amplifier, self).__init__()
        self.device = None
        self.start_temperature = None
        self.stop_temperature = None
        self.temperature_step = 0.1
        self.time_wait = 1

        self.temperatures = []
        self.powers = []

        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.ax: Optional[Axes] = None

        # deamon = True ensures this thread terminates when the main threads are
        # terminated
        self.daemon = True

        # flags
        self.scan_run = False

    def connect(self, resource_name: str) -> None:
        self.device = resource_name
        print(f"Connected to {resource_name}")
        # if self.device is not None:
        #     self.device.__exit__()
        # self.device = MPBAmplifier(resource_name)

    def run(self):
        self.scan_run = False
        self.temperatures = []
        self.powers = []
        temperature = self.start_temperature
        while temperature <= self.stop_temperature:
            self.temperatures.append(temperature)
            self.powers.append(random.random())
            temperature += self.temperature_step
            ax.clear()
            ax.plot(self.temperatures, self.powers)
            ax.grid(True)
            ax.set_xlabel("temperature [C]")
            ax.set_ylabel("power [mW]")
            self.canvas.draw()
            time.sleep(self.time_wait)
        self.scan_run = True
        return

    def save_scan(self, filename):
        if self.scan_run:

            header = ["temperature [C]", "power [mW]"]
            cwd = Path.cwd()
            with open(cwd / filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for t, p in zip(self.temperatures, self.powers):
                    writer.writerow([t, p])
        else:
            logging.error("Scan not completed, no data to save")


def run_temperature_scan(
    amplifier: Amplifier, start_temperature: float, stop_temperature: float, canvas, ax
) -> None:
    amplifier.start_temperature = start_temperature
    amplifier.stop_temperature = stop_temperature
    amplifier.canvas = canvas
    amplifier.ax = ax
    amplifier.start()
    return


amp = Amplifier()

rm = pyvisa.ResourceManager()
resources = rm.list_resources()
rm.close()

# setup figure
fig = Figure(figsize=(5, 4), dpi=100)
ax = fig.add_subplot(111)
ax.set_xlabel("temperature [C]")
ax.set_ylabel("power [mW]")

root = tk.Tk()

# setup figure canvas
canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().grid(row=2, column=0, columnspan=6)

clicked = tk.StringVar()
clicked.set(resources[0])
resource_name = tk.OptionMenu(root, clicked, *resources)
resource_name.grid(row=0, column=0)
connect = tk.Button(root, text="Connect", command=lambda: amp.connect(clicked.get()))
connect.grid(row=0, column=1)
start_temperature_label = tk.Label(root, text="Temperature start")
start_temperature_label.grid(row=1, column=0)
start_temperature = tk.Entry(root)
start_temperature.grid(row=1, column=1)
stop_temperature_label = tk.Label(root, text="stop")
stop_temperature_label.grid(row=1, column=2)
stop_temperature = tk.Entry(root)
stop_temperature.grid(row=1, column=3)
scan = tk.Button(
    root,
    text="Scan",
    command=lambda: run_temperature_scan(
        amp, float(start_temperature.get()), float(stop_temperature.get()), canvas, ax
    ),
)
scan.grid(row=1, column=5)


file_label = tk.Label(root, text="filename")
file_label.grid(row=3, column=0)
filename = tk.StringVar()
filename.set("SHG_temperature_scan.csv")
filename_entry = tk.Entry(root, textvariable=filename)
filename_entry.grid(row=3, column=1)
save_button = tk.Button(
    root, text="Save to csv", command=lambda: amp.save_scan(filename.get())
)
save_button.grid(row=3, column=2)
root.mainloop()
