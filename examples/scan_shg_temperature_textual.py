import csv
import datetime
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyvisa
from rich.status import Status
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    Switch,
)
from textual_plotext import PlotextPlot

from mpbc_vyfa_sf import LaserState, MPBAmplifier


def save_scan_to_csv(
    fname: Path, column_names: list[str], data: list[tuple[float, ...]]
) -> None:
    with open(fname, "w", newline="") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(column_names)
        writer.writerows(data)


class StatusWidget(Static):
    def __init__(self, message: str):
        super().__init__()
        self._status = Status(message)

    def on_mount(self) -> None:
        self.update_render = self.set_interval(1 / 60, self.update_status)

    def update_status(self) -> None:
        self.update(self._status)

    def update_message(self, message: str) -> None:
        self._status.update(message)

    def stop(self) -> None:
        self._status.stop()
        self.update_render.pause()

    def start(self) -> None:
        self._status.start()
        self.update_render.resume()


class MPBCAmpSHGApp(App[None]):
    CSS_PATH = "MPBCAmpSHGApp.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Select(prompt="Select COM port", options=[("COM0", 0)], id="COM"),
            Button("connect", id="connect"),
            StatusWidget(""),
            id="amp_connect",
        )
        yield Horizontal(
            Vertical(Label("enable"), Switch(id="enable")),
            Vertical(Label("power stabilization"), Switch(id="power_stabilization")),
            Vertical(Label("test environment"), Switch(id="test_environmentc")),
            Vertical(
                Label("Booster current [mA]"),
                Input(type="number", id="booster_current"),
            ),
            Vertical(Label(), Button("set", id="booster_current_set")),
        )
        yield Horizontal(
            Vertical(
                Label("SHG temperature [C]"),
                Input(
                    placeholder="shg temperature",
                    type="number",
                    id="shg_temperature",
                    max_length=5,
                ),
            ),
            Vertical(
                Label("SHG scan range [C]"),
                Input(
                    placeholder="shg scan range",
                    type="number",
                    id="shg_scan_range",
                    max_length=5,
                ),
            ),
            Vertical(
                Label("SHG scan steps"),
                Input(
                    placeholder="shg scan steps",
                    type="integer",
                    id="shg_scan_steps",
                    max_length=5,
                ),
            ),
            Vertical(
                Label("dt [s]"),
                Input(
                    placeholder="shg scan dt",
                    type="number",
                    id="shg_dt",
                    max_length=5,
                    value="2.0",
                ),
            ),
            Vertical(
                Label(),
                Button("scan", id="scan"),
            ),
        )
        yield DataTable(show_cursor=False)
        yield PlotextPlot()
        yield Footer()

    def on_mount(self) -> None:
        self.title = "MPB Communications VYFA-SF"
        com = self.query_one("#COM", Select)
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        com.set_options([(resource, idr) for idr, resource in enumerate(resources)])
        self.resources = resources

        table = self.query_one(DataTable)
        table.add_columns(
            *[
                "output power [mW]",
                "seed power [mW]",
                "current [mA]",
                "current setpoint [mA]",
                "SHG temperature [C]",
                "SHG temperature setpoint [C]",
            ]
        )

        self.query_one(StatusWidget).stop()

        plt = self.query_one(PlotextPlot).plt
        plt.xlabel("temperature [C]")
        plt.ylabel("power [mW]")

    @on(Button.Pressed, "#connect")
    def connect_amplifier(self) -> None:
        com_idx = self.query_one("#COM", Select).value
        if com_idx == Select.BLANK:
            self.notify("no com port selected", title="COM port", severity="error")
            return
        self.notify(str(self.resources[com_idx]))

        self.mpb = MPBAmplifier(self.resources[com_idx])

        # enable = self.query_one("#enable", Switch)
        # enable.value = self.mpb.enabled

        # power_stabilization = self.query_one("#power_stabilization", Switch)
        # power_stabilization.value = self.mpb.power_stabilization

    @on(Switch.Changed, "#enable")
    def enable(self) -> None:
        switch = self.query_one("#enable", Switch)
        status = self.query_one(StatusWidget)

        if switch.value:
            status.update(
                f"Starting amplifier: {self.mpb.laser_state.name}, booster current ="
                f" {self.mpb.booster_current:.1f}, setpoint = {self.mpb.booster_current_setpoint:.1f}"
            )
            status.start()

            self.notify("amplifier enabled", title="Enable")
            self.mpb.enable_laser()
            while True:
                if (self.mpb.laser_state == LaserState(52)) & (
                    abs(self.mpb.booster_current - self.mpb.booster_current_setpoint)
                    <= 10
                ):
                    tstart = time.time()
                    while (time.time() - tstart) < 2:
                        status.update(
                            f"Starting amplifier: {self.mpb.laser_state.name}, booster current ="
                            f" {self.mpb.booster_current:.1f}, setpoint ="
                            f" {self.mpb.booster_current_setpoint:.1f}"
                        )
                        time.sleep(0.1)
                    break
            status.update("Started amplifier")
            status.stop()

        else:
            self.notify("amplifier disabled", title="Enable")
            # self.mpb.disable_laser()

    @on(Switch.Changed, "#power_stabilization")
    def power_stabilization(self) -> None:
        switch = self.query_one("#power_stabilization", Switch)
        if switch.value:
            self.notify("power stabilization enabled", title="Power Stabilization")
            # self.mpb.power_stabilization = True
        else:
            self.notify("power stabilization disabled", title="Enable")
            # self.mpb.power_stabilization = False

    @on(Button.Pressed, "#booster_current_set")
    def set_current(self) -> None:
        current = self.query_one("#booster_current", Input)
        if len(current.value) == 0:
            self.notify("no current input", title="Current", severity="error")
            return
        self.notify(f"set current to {float(current.value)} mA")
        # self.mpb.booster_current_setpoint = current

    @on(Button.Pressed, "#scan")
    def scan_shg_temperature(self) -> None:
        temperature_setpoint = self.query_one("#shg_temperature", Input)
        if len(temperature_setpoint.value) == 0:
            self.notify("set SHG temperature", title="Scan", severity="error")
            return
        scan_range = self.query_one("#shg_scan_range", Input)
        if len(scan_range.value) == 0:
            self.notify("set SHG scan range", title="Scan", severity="error")
            return
        scan_steps = self.query_one("#shg_scan_steps", Input)
        if len(scan_steps.value) == 0:
            self.notify("set SHG scan steps", title="Scan", severity="error")
            return
        shg_dt = self.query_one("#shg_dt", Input)
        if len(shg_dt.value) == 0:
            self.notify("set SHG dt", title="Scan", severity="error")
            return

        self.run_scan(
            float(temperature_setpoint.value),
            float(scan_range.value),
            int(scan_steps.value),
            float(shg_dt.value),
        )
        return

    @dataclass
    class ScanData(Message):
        temperature_setpoint: list[float]
        temperature: list[float]
        power: list[float]

    @work(exclusive=True, thread=True)
    def run_scan(
        self, shg_temperature: float, scan_range: float, scan_steps: int, dt: float
    ) -> None:
        status = self.query_one(StatusWidget)
        self.call_from_thread(status.update_message, "Scanning SHG temperature")
        self.call_from_thread(status.start)
        data = []
        for setpoint in np.linspace(
            shg_temperature - scan_range / 2,
            shg_temperature + scan_range / 2,
            scan_steps,
        ):
            # self.mpb.temperature_setpoint = setpoint
            time.sleep(dt)
            data.append(
                [
                    setpoint,
                    np.random.random(),
                    np.random.random(),
                    np.random.random(),
                    np.random.random(),
                ]
            )
            self.call_from_thread(
                status.update_message, f"Scanning SHG temperature : {setpoint:<5.2f} C"
            )

            x, y, _, _, _ = list(zip(*data))
            self.post_message(self.ScanData(x, x, y))

        fname = (
            datetime.datetime.now()
            .isoformat(timespec="seconds")
            .replace("-", "_")
            .replace(":", "_")
        )
        fname += "_shg_scan.csv"

        save_scan_to_csv(
            Path(__file__).parent / fname,
            [
                "shg temperature setpoint [C]",
                "shg temperature [C]",
                "power [mW]",
                "booster curent [mW]",
                "input power [mW]",
            ],
            data,
        )

        self.call_from_thread(status.update_message, "SHG temperature scan done")
        self.call_from_thread(status.stop)

    @on(ScanData)
    def populate_plots(self, event: ScanData) -> None:
        plt = self.query_one(PlotextPlot).plt

        plt.clear_data()
        plt.scatter(event.temperature, event.power)
        self.query_one(PlotextPlot).refresh()

        datatable = self.query_one(DataTable)
        datatable.clear()
        datatable.add_row(
            *[
                event.power[-1],
                0,
                0,
                0,
                event.temperature[-1],
                event.temperature_setpoint[-1],
            ]
        )
        datatable.refresh()


if __name__ == "__main__":
    MPBCAmpSHGApp().run()
