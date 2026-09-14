"""Tests for the transmit safety gate."""

import pytest

from laurell import safety
from laurell.errors import TransmitBlockedError

gate_cases = [
    (False, None, False),
    (False, safety.tx_enabled_value, False),
    (True, None, False),
    (True, "0", False),
    (True, safety.tx_enabled_value, True),
]


def test_shipped_milestone_gate_is_closed() -> None:
    """The committed code keeps SAF-1 closed until the M4 change."""
    assert safety.transmit_milestone_reached is False


@pytest.mark.parametrize(("milestone", "env_value", "allowed"), gate_cases)
def test_gate_needs_milestone_and_env(
    monkeypatch: pytest.MonkeyPatch,
    milestone: bool,
    env_value: str | None,
    allowed: bool,
) -> None:
    """Transmit is allowed only when both gates are open."""
    monkeypatch.setattr(safety, "transmit_milestone_reached", milestone)
    if env_value is None:
        monkeypatch.delenv(safety.tx_enabled_variable, raising=False)
    else:
        monkeypatch.setenv(safety.tx_enabled_variable, env_value)

    assert safety.is_transmit_allowed() is allowed
    if allowed:
        safety.require_transmit_allowed()
    else:
        with pytest.raises(TransmitBlockedError):
            safety.require_transmit_allowed()
