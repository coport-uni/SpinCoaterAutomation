"""Exception hierarchy for the laurell package.

Every error raised on purpose derives from ``LaurellError`` so callers can
catch package failures without swallowing unrelated exceptions.
"""

import builtins


class LaurellError(Exception):
    """Base class for all errors raised by the laurell package."""


class TransportError(LaurellError):
    """The serial port could not be opened or used, or it disconnected."""


class TransmitBlockedError(LaurellError):
    """A transmit was attempted while the safety gate is closed.

    Sending stays blocked until milestone M3 is complete and the
    ``LAURELL_TX_ENABLED`` environment variable is ``1`` (see SAFETY.md).
    """


class ProtocolError(LaurellError):
    """A frame could not be parsed or failed its checksum."""


class TimeoutError(LaurellError, builtins.TimeoutError):
    """No response arrived within the allowed time.

    It also derives from the built-in ``TimeoutError`` so generic
    ``except TimeoutError`` handlers keep working.
    """


class DeviceStateError(LaurellError):
    """The device refused an action because of its state, e.g. interlock."""
