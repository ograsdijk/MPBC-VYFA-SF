import logging
from typing import Optional

import pyvisa

from .attributes import (
    BoolProperty,
    FlagProperty,
    FloatProperty,
    FloatPropertyNGet,
    IntProperty,
    Property,
)
from .enums import Alarm, Fault, LaserState


class MPBAmplifier:

    Model = Property("Model", "MODEL")
    Serial = Property("Serial", "SN")
    Enabled = BoolProperty("Enable Emission", "LDenable", read_only=True)
    State = BoolProperty("State", "STATE")
    LaserState = IntProperty("Laser state", "LASERSTATE")

    SHGTemperatureSetpoint = FloatProperty(
        "SHG Temperature Setpoint", "TECSETPT 4", read_only=False
    )
    SeedCurrent = FloatPropertyNGet("Seed Current", "LDCURRENT 1")
    PreampCurrent = FloatPropertyNGet("Preamp Current", "LDCURRENT 2")
    BoosterCurrent = FloatPropertyNGet(
        "Booster Current", "LDCURRENT 3", read_only=False
    )
    BoosterCurrentSetpoint = FloatProperty(
        "Booster Current Setpoint", "LDCur 3", read_only=False
    )
    SHGTemperature = FloatProperty("SHG Temperature", "TECTEMP 4")

    SeedPower = FloatPropertyNGet("Seed Power", "POWER 1")
    OutputPower = FloatPropertyNGet("Output Power", "POWER 0")

    Alarms = FlagProperty("Alarms", "ALR")
    Faults = FlagProperty("Faults", "FLT")

    def __init__(self, resource_name: str, baud_rate: int = 9600):
        self.rm = pyvisa.ResourceManager()

        # translate com port to visa port
        if "COM" in resource_name:
            resource_name = f"ASRL{resource_name.strip('COM')}::INSTR"

        self.instr = self.rm.open_resource(
            resource_name,
            baud_rate=baud_rate,
            read_termination="\r",
            write_termination="\r",
        )

    def __exit__(self):
        self.instr.close()
        self.rm.close()

    def _query(self, command: str) -> Optional[str]:
        return self.instr.query(command).strip("D >")

    def _write(self, command: str) -> None:
        self.instr.write(command)

    def _read(self) -> Optional[str]:
        return self.instr.read()

    def enable_laser(self) -> None:
        self._write("setLDenable 1")

    def disable_laser(self) -> None:
        self._write("setLDenable 0")

    def get_faults(self) -> list[Fault]:
        faults = self.Faults
        return [Fault(idx) for idx, flag in enumerate(faults) if flag]

    def get_alarms(self) -> list[Alarm]:
        alarms = self.Alarms
        return [Alarm(idx) for idx, flag in enumerate(alarms) if flag]

    def enter_test_environment(self) -> None:
        logging.info("Entering the test environment")
        logging.info(self._query("testeoa"))
        logging.info(self._read())
        logging.info(self._read())
        return

    def save_all(self) -> None:
        """Save settings to non-volatile memory"""
        self._write("SAVEALL")
