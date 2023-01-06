import logging
from typing import List, Optional

import pyvisa

from .attributes import (
    BoolProperty,
    FlagProperty,
    FloatProperty,
    IntProperty,
    Property,
    LaserStateProperty,
)
from .enums import Alarm, Fault
from .exceptions import MPBCommandError, MPBKeyError


class MPBAmplifier:

    model = Property("Model", "MODEL")
    serial = Property("Serial", "SN")
    enabled = BoolProperty("Laser emission status", "LDenable")
    state = BoolProperty("State", "STATE")
    laser_state = LaserStateProperty("Laser state", "LASERSTATE")
    mode = IntProperty("Mode", "MODE", read_only=False)
    seed_current = FloatProperty("Seed current", "LDCURRENT 1", read_prefix="")
    preamp_current = FloatProperty("Preamp current", "LDCURRENT 2", read_prefix="")
    preamp_current_setpoint = FloatProperty("Preamp current setpoint", "LDCur 2")
    booster_current = FloatProperty("Booster current", "LDCURRENT 3", read_prefix="")
    booster_current_setpoint = FloatProperty(
        "Booster current setpoint",
        "LDCur 3",
        write_prefix="",
        read_only=False,
    )

    shg_temperature = FloatProperty("SHG Temperature", "TECTEMP 4", read_prefix="")
    shg_temperature_setpoint = FloatProperty(
        "SHG Temperature setpoint",
        "TECSETPT 4",
        read_only=False,
    )

    seed_power = FloatProperty("Seed Power", "POWER 3", read_prefix="")
    output_power = FloatProperty("Output Power", "POWER 0", read_prefix="")
    output_power_setpoint = FloatProperty(
        "Output power setpoint", "POWER 0", read_only=False
    )

    power_stabilization = BoolProperty(
        "Power stabilization",
        "POWERENABLE",
        read_prefix="GET",
        write_prefix="",
        read_only=False,
    )

    alarms = FlagProperty("Alarms", "ALR")
    faults = FlagProperty("Faults", "FLT")

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

    def _query(self, command: str) -> str:
        msg = self.instr.query(command).strip("D >").strip("F >")
        msg = self._message_error_handling(msg)
        return msg

    def _write(self, command: str) -> None:
        self.instr.write(command)
        msg = self._read()
        self._message_error_handling(msg)

    def _read(self) -> Optional[str]:
        return self.instr.read()

    def _message_error_handling(self, message: str) -> str:
        if "MISSING_ARGUMENT" in message:
            raise MPBCommandError("Missing argument(s)")
        elif "CAN_ONLY_BE_USED_FOR_TESTS" in message:
            raise MPBCommandError("Requires test environment")
        elif "DATA_CANNOT_BE_SET" in message:
            raise MPBCommandError("Cannot execute commanda")
        return message

    def enable_laser(self) -> None:
        try:
            self._write("setLDenable 1")
        except MPBCommandError as e:
            raise MPBKeyError()

    def disable_laser(self) -> None:
        self._write("setLDenable 0")

    def get_faults(self) -> List[Fault]:
        faults = self.faults
        return [Fault(idx) for idx, flag in enumerate(faults) if flag]

    def get_alarms(self) -> List[Alarm]:
        alarms = self.alarms
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
