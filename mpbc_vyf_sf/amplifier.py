import logging
from typing import List, Optional

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

    model = Property("Model", "MODEL")
    serial = Property("Serial", "SN")
    enabled = BoolProperty("Enable Emission", "LDenable", read_only=True)
    state = BoolProperty("State", "STATE")
    laserState = IntProperty("Laser state", "LASERSTATE 0")

    seed_current = FloatProperty("Seed current", "LDCURRENT 1", read_prefix="")
    seed_current_setpoint = FloatProperty("Seed current setpoint", "LDCURRENT 1")
    preamp_current = FloatProperty("Preamp current", "LDCURRENT 2", read_prefix="")
    preamp_current_setpoint = FloatProperty("Preamp current setpoint", "LDCURRENT 2")
    booster_current = FloatProperty("Booster current", "LDCURRENT 3", read_prefix="")
    booster_current_setpoint = FloatProperty(
        "Booster current setpoint",
        "LDCur 3",
        read_prefix="",
        write_prefix="",
        read_only=False,
    )

    shg_temperature = FloatProperty(
        "SHG Temperature", "TECTEMP 4", write_command="TECSETPT 4"
    )
    shg_temperature_setpoint = FloatProperty(
        "SHG Temperature setpoint",
        "TECSETPT 4",
        read_prefix="",
        write_prefix="",
        read_only=False,
    )

    seed_power = FloatProperty("Seed Power", "POWER 1", read_prefix="")
    output_power = FloatProperty("Output Power", "POWER 0", read_prefix="")

    power_stabilization = BoolProperty(
        "Power stabilization",
        "POWERENABLE",
        read_prefix="",
        write_prefix="",
        read_only=False,
    )

    alarms = FlagProperty("Alarms", "ALR")
    faults = FlagProperty("Faults", "FLT")
    # laser_state = FlagProperty("Laser state", "LASERSTATE 0", read_prefix="")

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

    def get_faults(self) -> List[Fault]:
        faults = self.faults
        return [Fault(idx) for idx, flag in enumerate(faults) if flag]

    def get_alarms(self) -> List[Alarm]:
        alarms = self.alarms
        return [Alarm(idx) for idx, flag in enumerate(alarms) if flag]

    def get_laser_state(self) -> List[LaserState]:
        laser_state = self.laser_state
        return [LaserState(idx) for idx, flag in enumerate(laser_state) if flag]

    def enter_test_environment(self) -> None:
        logging.info("Entering the test environment")
        logging.info(self._query("testeoa"))
        logging.info(self._read())
        logging.info(self._read())
        return

    def save_all(self) -> None:
        """Save settings to non-volatile memory"""
        self._write("SAVEALL")
