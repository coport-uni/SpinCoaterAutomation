"""Receive-first serial transport for the 650 Series controller.

SAFETY.md, restated here as development_spec.md §3 requires: no transmit
before M3 (SAF-1); transmit only with ``LAURELL_TX_ENABLED=1`` (SAF-2);
every transmit takes ``dry_run=True`` by default (SAF-3); only allowlisted
frames (SAF-4); motor commands need explicit confirmation (SAF-5); device
tests with an empty chuck and closed lid (SAF-6); wiring changes powered
off (SAF-7); no run command before the interlock bits are decoded (SAF-8).
"""

from __future__ import annotations

import logging
from types import TracebackType

import serial

from laurell import safety
from laurell.errors import TransportError

logger = logging.getLogger(__name__)

default_read_timeout_s = 0.1


class SerialTransport:
    """Own one serial port with the transmit path gated by SAFETY.md.

    The port opens with every control line and flow-control option off,
    because some USB converters assert DTR and RTS on open and the
    controller's reaction to those lines is unknown.

    Args:
        port: Port name, such as ``"COM16"`` or ``"/dev/ttyUSB0"``.
        baudrate: Line speed in bits per second. There is no default
            because the controller's baud rate is not confirmed yet.
        bytesize: Data bits per character, as a pyserial constant.
        parity: Parity mode, as a pyserial constant.
        stopbits: Stop bits per character, as a pyserial constant.
        timeout: Read timeout in seconds; ``None`` blocks until data.
    """

    def __init__(
        self,
        port: str,
        baudrate: int,
        bytesize: int = serial.EIGHTBITS,
        parity: str = serial.PARITY_NONE,
        stopbits: float = serial.STOPBITS_ONE,
        timeout: float | None = default_read_timeout_s,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self._link: serial.Serial | None = None

    def __enter__(self) -> SerialTransport:
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        """Whether the underlying port is currently open."""
        return self._link is not None and self._link.is_open

    @property
    def in_waiting(self) -> int:
        """Number of received bytes waiting in the input buffer.

        Raises:
            TransportError: If the port is closed or has disconnected.
        """
        link = self._require_open()
        try:
            return link.in_waiting
        except serial.SerialException as error:
            raise TransportError(
                f"{self.port} disconnected: {error}"
            ) from error

    def open(self) -> None:
        """Open the port with DTR and RTS held low.

        Opening an already open transport does nothing.

        Raises:
            TransportError: If the port is missing or held by another
                process.
        """
        if self.is_open:
            return
        link = serial.Serial()
        link.port = self.port
        link.baudrate = self.baudrate
        link.bytesize = self.bytesize
        link.parity = self.parity
        link.stopbits = self.stopbits
        link.timeout = self.timeout
        link.xonxoff = False
        link.rtscts = False
        link.dsrdtr = False
        # pyserial applies these states while opening, so the lines should
        # never rise. They are lowered again after opening in case a driver
        # ignores the initial state.
        link.dtr = False
        link.rts = False
        try:
            link.open()
            link.dtr = False
            link.rts = False
        except serial.SerialException as error:
            link.close()
            raise TransportError(
                f"Could not open {self.port}: {error}"
            ) from error
        self._link = link
        logger.info("Opened %s at %d baud", self.port, self.baudrate)

    def close(self) -> None:
        """Release the port. Closing a closed transport does nothing."""
        if self._link is None:
            return
        try:
            self._link.close()
        finally:
            self._link = None
            logger.info("Closed %s", self.port)

    def read(self, size: int = 1) -> bytes:
        """Read up to ``size`` bytes, returning early on timeout.

        Args:
            size: Maximum number of bytes to return.

        Returns:
            The bytes received, possibly fewer than ``size``.

        Raises:
            TransportError: If the port is closed or has disconnected.
        """
        link = self._require_open()
        try:
            return link.read(size)
        except serial.SerialException as error:
            raise TransportError(
                f"{self.port} disconnected: {error}"
            ) from error

    def write(self, data: bytes, *, dry_run: bool = True) -> int:
        """Send bytes to the controller once the safety gate allows it.

        The gate is checked before anything else, so a blocked call never
        touches the port, even as a dry run.

        Args:
            data: Raw bytes to send.
            dry_run: If ``True`` (the default, SAF-3), log the bytes
                instead of sending them.

        Returns:
            Number of bytes written; ``0`` for a dry run.

        Raises:
            TransmitBlockedError: If the safety gate is closed.
            TransportError: If the port is closed or the write fails.
        """
        safety.require_transmit_allowed()
        if dry_run:
            logger.info("Dry run, not sent to %s: %s", self.port, data.hex(" "))
            return 0
        link = self._require_open()
        try:
            written = link.write(data)
        except serial.SerialException as error:
            raise TransportError(
                f"Write to {self.port} failed: {error}"
            ) from error
        return written or 0

    def _require_open(self) -> serial.Serial:
        if self._link is None or not self._link.is_open:
            raise TransportError(f"{self.port} is not open.")
        return self._link
