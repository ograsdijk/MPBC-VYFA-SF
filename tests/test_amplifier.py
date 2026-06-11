import pytest

from mpbc_vyfa_sf import MPBAmplifier
from mpbc_vyfa_sf.enums import Alarm, Fault
from mpbc_vyfa_sf.exceptions import MPBCommandError, MPBKeyError


def test_constructor_forwards_serial_options(fake_serial):
    MPBAmplifier(port="COM4", baud_rate=115200, timeout=1.5)
    assert fake_serial.port == "COM4"
    assert fake_serial.baudrate == 115200
    assert fake_serial.timeout == 1.5


def test_constructor_does_not_translate_com_port(fake_serial):
    # pyserial takes the COM port verbatim; no ASRL/VISA translation anymore.
    MPBAmplifier(port="COM30")
    assert fake_serial.port == "COM30"


def test_default_baud_and_timeout(fake_serial):
    MPBAmplifier(port="COM1")
    assert fake_serial.baudrate == 9600
    assert fake_serial.timeout == 2.0


def test_send_encodes_and_appends_terminator(amp):
    instrument, fake = amp
    instrument._send("HELLO")
    assert fake.written[-1] == b"HELLO\r"


def test_read_decodes_and_strips_terminator(amp):
    instrument, fake = amp
    fake.queue("RESPONSE")
    assert instrument._read() == "RESPONSE"


def test_read_returns_empty_on_timeout(amp):
    instrument, fake = amp
    # Nothing queued -> read_until returns b"" (timeout).
    assert instrument._read() == ""


@pytest.mark.parametrize("reply", ["D > 1530", "F > 1530", "D >1530", "1530"])
def test_query_strips_prompt_prefix(amp, reply):
    instrument, fake = amp
    fake.queue(reply)
    assert instrument._query("GETMODEL") == "1530"
    assert fake.written[-1] == b"GETMODEL\r"


def test_query_only_strips_leading_prompt_not_payload(amp):
    # A payload that happens to start with "D"/end with "F" must survive intact.
    instrument, fake = amp
    fake.queue("D > VYFA-SF")
    assert instrument._query("GETMODEL") == "VYFA-SF"


ERROR_RESPONSES = [
    "MISSING_ARGUMENT",
    "CAN_ONLY_BE_USED_FOR_TESTS",
    "DATA_CANNOT_BE_SET",
]


@pytest.mark.parametrize("response", ERROR_RESPONSES)
def test_write_raises_on_error_response(amp, response):
    instrument, fake = amp
    fake.queue(response)
    with pytest.raises(MPBCommandError):
        instrument._write("SETMODE 1")


@pytest.mark.parametrize("response", ERROR_RESPONSES)
def test_query_raises_on_error_response(amp, response):
    instrument, fake = amp
    fake.queue(response)
    with pytest.raises(MPBCommandError):
        instrument._query("GETMODEL")


def test_enable_laser_sends_command(amp):
    instrument, fake = amp
    fake.queue("")  # readback after the write
    instrument.enable_laser()
    assert fake.written[-1] == b"setLDenable 1\r"


def test_enable_laser_raises_keyerror_on_command_error(amp):
    instrument, fake = amp
    fake.queue("MISSING_ARGUMENT")
    with pytest.raises(MPBKeyError):
        instrument.enable_laser()


def test_disable_laser_sends_command(amp):
    instrument, fake = amp
    fake.queue("")
    instrument.disable_laser()
    assert fake.written[-1] == b"setLDenable 0\r"


def test_save_all_sends_command(amp):
    instrument, fake = amp
    fake.queue("")
    instrument.save_all()
    assert fake.written[-1] == b"SAVEALL\r"


def test_close_closes_port(amp):
    instrument, fake = amp
    instrument.close()
    assert fake.closed is True


def test_context_manager_closes_port(fake_serial):
    with MPBAmplifier(port="COM_TEST") as instrument:
        assert isinstance(instrument, MPBAmplifier)
    assert fake_serial.closed is True


def test_get_faults_parses_flags(amp):
    instrument, fake = amp
    fake.queue("0 0 1 0 1")
    assert instrument.get_faults() == [
        Fault.LASER_DIODE_CURRENT,
        Fault.CASE_TEMPERATURE,
    ]
    assert fake.written[-1] == b"GETFLT\r"


def test_get_alarms_parses_flags(amp):
    instrument, fake = amp
    fake.queue("1 0 0 0 1")
    assert instrument.get_alarms() == [
        Alarm.SHG_TEMPERATURE,
        Alarm.CASE_TEMPERATURE,
    ]
    assert fake.written[-1] == b"GETALR\r"
