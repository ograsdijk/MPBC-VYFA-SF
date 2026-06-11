import pytest

from mpbc_vyfa_sf import LaserState


def test_string_property_get(amp):
    instrument, fake = amp
    fake.queue("VYFA-SF")
    assert instrument.model == "VYFA-SF"
    assert fake.written[-1] == b"GETMODEL\r"


def test_float_property_get_parses_float(amp):
    instrument, fake = amp
    fake.queue("123.4")
    value = instrument.seed_current
    assert value == 123.4
    assert isinstance(value, float)
    assert fake.written[-1] == b"LDCURRENT 1\r"


def test_int_property_get_parses_int(amp):
    instrument, fake = amp
    fake.queue("2")
    value = instrument.mode
    assert value == 2
    assert isinstance(value, int)
    assert fake.written[-1] == b"GETMODE\r"


def test_int_property_set(amp):
    instrument, fake = amp
    fake.queue("")  # readback after the write
    instrument.mode = 3
    assert fake.written[-1] == b"SETMODE 3\r"


@pytest.mark.parametrize("response,expected", [("1", True), ("0", False)])
def test_bool_property_get(amp, response, expected):
    instrument, fake = amp
    fake.queue(response)
    value = instrument.enabled
    assert value is expected
    assert fake.written[-1] == b"GETLDenable\r"


def test_bool_property_set(amp):
    instrument, fake = amp
    fake.queue("")
    instrument.power_stabilization = True
    assert fake.written[-1] == b"POWERENABLE 1\r"


def test_float_property_set_empty_write_prefix(amp):
    instrument, fake = amp
    fake.queue("")
    instrument.booster_current_setpoint = 10.5
    assert fake.written[-1] == b"LDCur 3 10.5\r"


def test_flag_property_get(amp):
    instrument, fake = amp
    fake.queue("1 0 1 0 0")
    assert instrument.alarms == [True, False, True, False, False]
    assert fake.written[-1] == b"GETALR\r"


def test_laser_state_property_get(amp):
    instrument, fake = amp
    fake.queue("52")
    assert instrument.laser_state == LaserState.BOOSTER_ON
    assert fake.written[-1] == b"GETLASERSTATE\r"


def test_read_only_property_set_raises(amp):
    instrument, _ = amp
    with pytest.raises(ValueError):
        instrument.model = "x"
