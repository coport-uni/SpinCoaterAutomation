"""Tests for the transmit gate and port handling of SerialTransport."""

from collections.abc import Callable

import pytest
import serial

from laurell import safety, transport
from laurell.errors import TransmitBlockedError, TransportError
from laurell.transport import SerialTransport

test_port = "COM_TEST"
test_baudrate = 9600
sample_frame = b"\r"
received_bytes = b"\x02OK\x03"
rejected_env_values = ["", "0", "true", "yes", " 1"]


class FakeSerial:
    """Stand-in for ``serial.Serial`` that records control-line changes."""

    def __init__(self) -> None:
        self.port: str | None = None
        self.baudrate: int | None = None
        self.bytesize: int | None = None
        self.parity: str | None = None
        self.stopbits: float | None = None
        self.timeout: float | None = None
        self.xonxoff = True
        self.rtscts = True
        self.dsrdtr = True
        self.is_open = False
        # pyserial starts with both lines asserted.
        self._dtr = True
        self._rts = True
        self.line_events: list[tuple[str, bool, bool]] = []
        self.written: list[bytes] = []
        self.rx_buffer = b""

    @property
    def dtr(self) -> bool:
        return self._dtr

    @dtr.setter
    def dtr(self, value: bool) -> None:
        self._dtr = value
        self.line_events.append(("dtr", value, self.is_open))

    @property
    def rts(self) -> bool:
        return self._rts

    @rts.setter
    def rts(self, value: bool) -> None:
        self._rts = value
        self.line_events.append(("rts", value, self.is_open))

    @property
    def in_waiting(self) -> int:
        return len(self.rx_buffer)

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def read(self, size: int) -> bytes:
        chunk, self.rx_buffer = self.rx_buffer[:size], self.rx_buffer[size:]
        return chunk

    def write(self, data: bytes) -> int:
        self.written.append(data)
        return len(data)


class BusySerial(FakeSerial):
    """Fake port that fails to open, as when another process holds it."""

    def open(self) -> None:
        raise serial.SerialException("Access is denied.")


def install_fake(
    monkeypatch: pytest.MonkeyPatch, factory: type[FakeSerial]
) -> list[FakeSerial]:
    """Replace ``serial.Serial`` in the transport module with a fake."""
    created: list[FakeSerial] = []

    def make() -> FakeSerial:
        link = factory()
        created.append(link)
        return link

    monkeypatch.setattr(transport.serial, "Serial", make)
    return created


@pytest.fixture(autouse=True)
def closed_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start every test with the environment gate unset."""
    monkeypatch.delenv(safety.tx_enabled_variable, raising=False)


@pytest.fixture
def fake_ports(monkeypatch: pytest.MonkeyPatch) -> list[FakeSerial]:
    """Patch pyserial with a recording fake and return created ports."""
    return install_fake(monkeypatch, FakeSerial)


@pytest.fixture
def open_gate(monkeypatch: pytest.MonkeyPatch) -> Callable[[], None]:
    """Return a function that opens both transmit gates for one test."""

    def unlock() -> None:
        monkeypatch.setattr(safety, "transmit_milestone_reached", True)
        monkeypatch.setenv(safety.tx_enabled_variable, safety.tx_enabled_value)

    return unlock


def make_transport() -> SerialTransport:
    """Build a transport for the fake test port."""
    return SerialTransport(test_port, test_baudrate)


def test_open_applies_line_settings(fake_ports: list[FakeSerial]) -> None:
    """Opening passes every line setting through and disables flow control."""
    with make_transport():
        link = fake_ports[0]
        assert link.port == test_port
        assert link.baudrate == test_baudrate
        assert link.bytesize == serial.EIGHTBITS
        assert link.parity == serial.PARITY_NONE
        assert link.stopbits == serial.STOPBITS_ONE
        assert (link.xonxoff, link.rtscts, link.dsrdtr) == (False,) * 3


def test_open_holds_dtr_and_rts_low(fake_ports: list[FakeSerial]) -> None:
    """DTR and RTS are lowered before opening and again after opening."""
    with make_transport():
        link = fake_ports[0]
        assert all(value is False for _, value, _ in link.line_events)
        for line in ("dtr", "rts"):
            states = {
                was_open
                for name, _, was_open in link.line_events
                if name == line
            }
            assert states == {False, True}
        assert link.dtr is False
        assert link.rts is False


def test_open_failure_raises_transport_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A port held elsewhere surfaces as TransportError, left closed."""
    install_fake(monkeypatch, BusySerial)
    port = make_transport()
    with pytest.raises(TransportError):
        port.open()
    assert port.is_open is False


def test_context_manager_releases_port_on_error(
    fake_ports: list[FakeSerial],
) -> None:
    """Leaving the ``with`` block through an exception still closes."""
    port = make_transport()
    with pytest.raises(RuntimeError), port:
        raise RuntimeError("operator abort")
    assert fake_ports[0].is_open is False
    assert port.is_open is False


def test_close_is_idempotent(fake_ports: list[FakeSerial]) -> None:
    """Closing twice, or before opening, raises nothing."""
    port = make_transport()
    port.close()
    port.open()
    port.close()
    port.close()
    assert port.is_open is False


def test_read_returns_received_bytes(fake_ports: list[FakeSerial]) -> None:
    """Received bytes pass through unchanged."""
    with make_transport() as port:
        fake_ports[0].rx_buffer = received_bytes
        assert port.in_waiting == len(received_bytes)
        assert port.read(len(received_bytes)) == received_bytes


def test_read_on_closed_port_raises(fake_ports: list[FakeSerial]) -> None:
    """Reading before open is a TransportError, not an AttributeError."""
    with pytest.raises(TransportError):
        make_transport().read()


def test_write_blocked_by_default(fake_ports: list[FakeSerial]) -> None:
    """With no configuration at all, write refuses and sends nothing."""
    with make_transport() as port:
        with pytest.raises(TransmitBlockedError):
            port.write(sample_frame, dry_run=False)
        assert fake_ports[0].written == []


def test_env_variable_alone_does_not_unlock(
    fake_ports: list[FakeSerial], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Setting LAURELL_TX_ENABLED=1 before M3 still blocks (SAF-1)."""
    monkeypatch.setenv(safety.tx_enabled_variable, safety.tx_enabled_value)
    with make_transport() as port:
        with pytest.raises(TransmitBlockedError):
            port.write(sample_frame, dry_run=False)
        assert fake_ports[0].written == []


@pytest.mark.parametrize("env_value", [None, *rejected_env_values])
def test_milestone_alone_does_not_unlock(
    fake_ports: list[FakeSerial],
    monkeypatch: pytest.MonkeyPatch,
    env_value: str | None,
) -> None:
    """After M3, only the exact value "1" enables transmit (SAF-2)."""
    monkeypatch.setattr(safety, "transmit_milestone_reached", True)
    if env_value is not None:
        monkeypatch.setenv(safety.tx_enabled_variable, env_value)
    with make_transport() as port:
        with pytest.raises(TransmitBlockedError):
            port.write(sample_frame, dry_run=False)
        assert fake_ports[0].written == []


def test_write_defaults_to_dry_run(
    fake_ports: list[FakeSerial], open_gate: Callable[[], None]
) -> None:
    """Even with both gates open, the default call sends nothing (SAF-3)."""
    open_gate()
    with make_transport() as port:
        assert port.write(sample_frame) == 0
        assert fake_ports[0].written == []


def test_write_sends_when_gates_open(
    fake_ports: list[FakeSerial], open_gate: Callable[[], None]
) -> None:
    """Both gates open plus ``dry_run=False`` sends the bytes once."""
    open_gate()
    with make_transport() as port:
        assert port.write(sample_frame, dry_run=False) == len(sample_frame)
        assert fake_ports[0].written == [sample_frame]


def test_write_on_closed_port_raises(
    fake_ports: list[FakeSerial], open_gate: Callable[[], None]
) -> None:
    """A real write needs an open port."""
    open_gate()
    with pytest.raises(TransportError):
        make_transport().write(sample_frame, dry_run=False)


class DisconnectedSerial(FakeSerial):
    """Fake port that opens, then fails all I/O like an unplugged cable."""

    @property
    def in_waiting(self) -> int:
        raise serial.SerialException("ClearCommError failed")

    def read(self, size: int) -> bytes:
        raise serial.SerialException("ReadFile failed")

    def write(self, data: bytes) -> int:
        raise serial.SerialException("WriteFile failed")


def test_open_twice_keeps_one_port(fake_ports: list[FakeSerial]) -> None:
    """A second open on an open transport does not reopen the port."""
    with make_transport() as port:
        port.open()
        assert len(fake_ports) == 1


def test_disconnect_surfaces_as_transport_error(
    monkeypatch: pytest.MonkeyPatch, open_gate: Callable[[], None]
) -> None:
    """pyserial I/O failures after open become TransportError."""
    install_fake(monkeypatch, DisconnectedSerial)
    open_gate()
    with make_transport() as port:
        with pytest.raises(TransportError):
            _ = port.in_waiting
        with pytest.raises(TransportError):
            port.read()
        with pytest.raises(TransportError):
            port.write(sample_frame, dry_run=False)
