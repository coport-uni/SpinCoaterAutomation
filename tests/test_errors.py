"""Tests for the laurell exception hierarchy."""

import builtins

import pytest

from laurell import errors

package_errors = [
    errors.TransportError,
    errors.TransmitBlockedError,
    errors.ProtocolError,
    errors.TimeoutError,
    errors.DeviceStateError,
]


@pytest.mark.parametrize("error_type", package_errors)
def test_errors_derive_from_laurell_error(error_type: type[Exception]) -> None:
    """Catching LaurellError catches every package error."""
    with pytest.raises(errors.LaurellError):
        raise error_type("failure")


def test_timeout_is_also_builtin_timeout() -> None:
    """Generic ``except TimeoutError`` handlers still catch it."""
    with pytest.raises(builtins.TimeoutError):
        raise errors.TimeoutError("no response")
