"""Optional extension module (UWA2-E) identity and measurements.

The extension board is optional: its registers (4500-4505, 4520-4524,
4541-4544) are only served while the module is installed. This component is
therefore read apart from the unit's pooled update, and marks itself
unavailable when the unit refuses those registers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..data_model import NAN_INT16, BrinkComponent, boolean, gauge, integer
from ..versions import _hardware_version, _minor_fix, _type_version

if TYPE_CHECKING:
    from modbus_connection._protocol import ModbusUnit

_EXTENSION_RANGES = (
    (4500, 4505),  # extension module versions, type and dipswitch
    (4520, 4524),  # extension module NTC, contacts and analogue inputs
    (4541, 4544),  # extension module relay and analogue outputs
)


class ExtensionModule(BrinkComponent):
    """The optional UWA2-E extension module of the unit."""

    register_space = "input"
    register_ranges = _EXTENSION_RANGES

    def __init__(self, unit: ModbusUnit) -> None:
        """Initialize the extension module, assumed present until proven absent."""
        super().__init__(unit)
        self._available = True

    _sw_type = integer(
        4500,
        signed=False,
        description="Extension module software type and major version",
    )
    _sw_minor_fix = integer(
        4501,
        signed=False,
        description="Extension module software minor and fix version",
    )
    _sw_build = integer(
        4502,
        signed=False,
        description="Extension module software build number",
    )
    _hw_version = integer(
        4503,
        signed=False,
        description="Extension module hardware version (major, minor)",
    )
    device_type = integer(
        4504,
        signed=False,
        description="The extension module device type",
    )
    dipswitch = integer(
        4505,
        signed=False,
        description="The extension module dipswitch value",
    )
    temperature = gauge(
        4520,
        0.1,
        signed=True,
        nan=NAN_INT16,
        unit="°C",
        digits=1,
        description="Temperature of the extension module NTC",
    )
    contact_1 = boolean(
        4521,
        description="Whether extension contact 1 is closed",
    )
    contact_2 = boolean(
        4522,
        description="Whether extension contact 2 is closed",
    )
    analogue_input_1 = gauge(
        4523,
        0.1,
        signed=False,
        unit="V",
        digits=1,
        description="Voltage at extension analogue input 1",
    )
    analogue_input_2 = gauge(
        4524,
        0.1,
        signed=False,
        unit="V",
        digits=1,
        description="Voltage at extension analogue input 2",
    )
    relay_1 = boolean(
        4541,
        description="Whether extension relay output 1 is energized (24V)",
    )
    relay_2 = boolean(
        4542,
        description="Whether extension relay output 2 is energized (24V)",
    )
    analogue_output_1 = gauge(
        4543,
        0.1,
        signed=False,
        unit="V",
        digits=1,
        description="Voltage at extension analogue output 1",
    )
    analogue_output_2 = gauge(
        4544,
        0.1,
        signed=False,
        unit="V",
        digits=1,
        description="Voltage at extension analogue output 2",
    )

    @property
    def available(self) -> bool:
        """Whether the extension module answered its registers."""
        return self._available

    @property
    def software_version(self) -> str:
        """Return the extension module software version, e.g. ``S1.01.02.0001``."""
        type_version = _type_version(self._sw_type)
        minor_fix = _minor_fix(self._sw_minor_fix)
        if minor_fix is None:
            return type_version
        if self._sw_build is None:
            return f"{type_version}.{minor_fix}"
        return f"{type_version}.{minor_fix}.{self._sw_build:04d}"

    @property
    def hardware_version(self) -> str:
        """Return the extension module hardware version, e.g. ``H1.1``."""
        return _hardware_version(self._hw_version)

    def mark_unavailable(self) -> None:
        """Record that the unit refused the extension module's registers."""
        self._available = False
        self._values.clear()
