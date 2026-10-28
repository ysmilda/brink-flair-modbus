"""Exceptions raised by the Brink Flair library."""

from __future__ import annotations


class BrinkValueValidationError(ValueError):
    """A value cannot be written because it is outside the documented limits."""


class BypassOverrideBlockedError(BrinkValueValidationError):
    """Forcing the bypass open is refused at a high supply flow."""

    def __init__(self, supply_volume: int) -> None:
        """Initialize with the supply flow that blocked the override."""
        super().__init__(
            f"Forcing the bypass open is blocked at a supply flow of "
            f"{supply_volume} m³/h"
        )
        self.supply_volume = supply_volume
