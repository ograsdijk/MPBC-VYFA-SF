import logging
import re
from typing import List

import serial

from .attributes import (
    BoolProperty,
    FlagProperty,
    FloatProperty,
    IntProperty,
    LaserStateProperty,
    Property,
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

    def __init__(self, port: str, baud_rate: int = 9600, timeout: float = 2.0):
        self.instr = serial.Serial(port=port, baudrate=baud_rate, timeout=timeout)
        self._termination = b"\r"

    def close(self) -> None:
        self.instr.close()

    def __enter__(self) -> "MPBAmplifier":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _send(self, command: str) -> None:
        self.instr.write(command.encode("ascii") + self._termination)

    _PROMPT_PREFIX = re.compile(r"^\s*(?:[DF]\s*)?>\s*")

    def _query(self, command: str) -> str:
        self._send(command)
        msg = self._read_response()
        try:
            return self._message_error_handling(msg)
        except MPBCommandError as exc:
            raise self._command_error(command, msg, exc) from exc

    def _write(self, command: str) -> None:
        self._send(command)
        msg = self._read_response()
        try:
            self._message_error_handling(msg)
        except MPBCommandError as exc:
            raise self._command_error(command, msg, exc) from exc

    @staticmethod
    def _command_error(
        command: str, response: str, exc: MPBCommandError
    ) -> MPBCommandError:
        return MPBCommandError(
            f"command={command!r}, response={response!r}: {exc}"
        )

    def _read(self) -> str:
        msg = self.instr.read_until(self._termination)
        return msg.decode("ascii").rstrip("\r")

    def _read_response(self) -> str:
        last = ""
        for _ in range(8):
            msg = self._read()
            if not msg:
                return last
            last = self._normalize_response(msg)
            if last:
                self._drain_prompt()
                return last
        return last

    def _normalize_response(self, message: str) -> str:
        return self._PROMPT_PREFIX.sub("", message).strip()

    def _drain_prompt(self) -> None:
        if not int(getattr(self.instr, "in_waiting", 0) or 0):
            return
        self.instr.read(int(getattr(self.instr, "in_waiting", 0) or 0))

    def _message_error_handling(self, message: str) -> str:
        if "MISSING_ARGUMENT" in message:
            raise MPBCommandError("Missing argument(s)")
        elif "CAN_ONLY_BE_USED_FOR_TESTS" in message:
            raise MPBCommandError("Requires test environment")
        elif "DATA_CANNOT_BE_SET" in message:
            raise MPBCommandError("Cannot execute command")
        elif "UNKNOWN_COMMAND" in message:
            raise MPBCommandError("Unknown command")
        return message

    def enable_laser(self) -> None:
        try:
            self._write("setLDenable 1")
        except MPBCommandError:
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
        self._send("testeoa")
        for _ in range(3):
            line = self._normalize_response(self._read())
            if line:
                logging.info(line)
        self._drain_prompt()
        return

    def save_all(self) -> None:
        """Save settings to non-volatile memory"""
        self._write("SAVEALL")
