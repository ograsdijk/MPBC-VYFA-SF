from collections import deque

import pytest

from mpbc_vyfa_sf import MPBAmplifier


class FakeSerial:
    """In-memory stand-in for ``serial.Serial`` used by ``MPBAmplifier``.

    Records every chunk written to ``written`` and returns queued replies from
    ``read_until``. An empty queue yields ``b""`` to mimic a serial read timeout.
    """

    def __init__(self):
        self.port = None
        self.baudrate = None
        self.timeout = None
        self.written: list[bytes] = []
        self.closed = False
        self._responses: deque[str] = deque()

    def queue(self, *replies: str) -> None:
        """Queue one or more replies (without terminator) to be read back."""
        self._responses.extend(replies)

    def write(self, data: bytes) -> int:
        self.written.append(data)
        return len(data)

    def read_until(self, terminator: bytes = b"\r", size=None) -> bytes:
        if self._responses:
            return self._responses.popleft().encode("ascii") + terminator
        return b""

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_serial(monkeypatch):
    """Patch ``serial.Serial`` so ``MPBAmplifier`` opens a ``FakeSerial``."""
    fake = FakeSerial()

    def factory(*args, port=None, baudrate=None, timeout=None, **kwargs):
        fake.port = port if port is not None else (args[0] if args else None)
        fake.baudrate = baudrate
        fake.timeout = timeout
        return fake

    monkeypatch.setattr("mpbc_vyfa_sf.amplifier.serial.Serial", factory)
    return fake


@pytest.fixture
def amp(fake_serial):
    """An ``MPBAmplifier`` wired to the ``FakeSerial`` from ``fake_serial``.

    Returns ``(amplifier, fake_serial)`` so tests can queue replies and assert on
    the bytes written.
    """
    instrument = MPBAmplifier(port="COM_TEST")
    return instrument, fake_serial
