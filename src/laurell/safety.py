"""Transmit safety gate shared by every module that can send bytes.

SAFETY.md, restated here as development_spec.md §3 requires:

- SAF-1: No serial transmit before milestone M3 is complete; blocked in code.
- SAF-2: Transmit is enabled only when ``LAURELL_TX_ENABLED=1``.
- SAF-3: Every transmit function takes ``dry_run``, default ``True``.
- SAF-4: Only allowlisted frames with a confirmed meaning may be sent.
- SAF-5: Commands that may start the motor need an explicit confirm arg.
- SAF-6: Device tests run only with an empty chuck and a closed lid.
- SAF-7: Wiring changes happen only with the device and PC powered off.
- SAF-8: No run command before the interlock status bits are decoded.
"""

import os

from laurell.errors import TransmitBlockedError

tx_enabled_variable = "LAURELL_TX_ENABLED"
tx_enabled_value = "1"

# SAF-1: only the reviewed M4 change may flip this, after M3 is accepted.
# The environment variable alone must never unlock sending.
transmit_milestone_reached = False


def is_transmit_allowed() -> bool:
    """Report whether both the milestone gate and the environment gate open.

    Returns:
        ``True`` only if milestone M3 is complete and
        ``LAURELL_TX_ENABLED`` is exactly ``"1"``.
    """
    return (
        transmit_milestone_reached
        and os.environ.get(tx_enabled_variable) == tx_enabled_value
    )


def require_transmit_allowed() -> None:
    """Refuse to continue unless sending is allowed.

    Raises:
        TransmitBlockedError: If milestone M3 is not complete (SAF-1) or
            ``LAURELL_TX_ENABLED`` is not ``"1"`` (SAF-2).
    """
    if not transmit_milestone_reached:
        raise TransmitBlockedError(
            "Serial transmit is disabled until milestone M3 is complete "
            "(SAF-1)."
        )
    if os.environ.get(tx_enabled_variable) != tx_enabled_value:
        raise TransmitBlockedError(
            f"Set {tx_enabled_variable}={tx_enabled_value} to enable serial "
            "transmit (SAF-2)."
        )
