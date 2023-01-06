from enum import IntEnum


class Alarm(IntEnum):
    SHG_TEMPERATURE = 0
    TEC_TEMPERATURE = 1
    PUMP_BIAS = 2
    LOSS_OF_OUTPUT = 3
    CASE_TEMPERATURE = 4


class Fault(IntEnum):
    SHG_TEMPERATURE = 0
    TEC_TEMPERATURE = 1
    LASER_DIODE_CURRENT = 2
    WATCHDOG_TIMEOUT = 3
    CASE_TEMPERATURE = 4


class LaserState(IntEnum):
    OFF = 0
    # The keylock only triggers after the interlock is triggered and the key has to be
    # reset to return the amplifier to normal operation.
    # Not sure how to read out the current key state.
    KEYLOCK = 6
    INTERLOCK = 7
    FAULT = 8
    LOS = 9
    STARTUP = 20
    MANUAL_TURNING_ON = 31
    MANUAL_ON = 41
    SEED_ON = 43
    SEED_OK = 44
    PREAMP_TURN_ON = 45
    PREAMP_TURN_OFF = 46
    PREAMP_ON = 47
    PREAMP_OK = 48
    BOOSTER_TURN_ON = 50
    BOOSTER_TURN_OFF = 51
    BOOSTER_ON = 52
    BOOSTER_OK = 53
