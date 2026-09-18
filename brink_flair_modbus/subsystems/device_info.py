"""Identity registers of a Brink Flair unit (input registers).

Besides the device type, the identity block carries the software and hardware
versions of the base and user-interface (UIF) modules, the serial number, and
their dipswitch values. The optional extension (UWA2-E) module is covered by
``ExtensionModule``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..data_model import BrinkComponent, integer
from ..device_types import model_name_for_device_type
from ..versions import _hardware_version, _minor_fix, _type_version

if TYPE_CHECKING:
    from modbus_connection._protocol import ModbusUnit

# The input map 4000-4544 is documented as readable in full (Modbus
# installation regulations, UWA2-B/UWA2-E 614882), so the documented identity
# blocks are read as one range each.
_IDENTITY_RANGES = (
    (4000, 4005),  # base module versions, device type and dipswitch
    (4010, 4018),  # numeric and alpha-numeric serial number
    (4400, 4405),  # user-interface module versions, type and dipswitch
    (4410, 4415),  # UIF language-data and software versions
    (4420, 4421),  # UIF local switch and button
)


def _bcd_digits(*words: int | None) -> tuple[str, bool]:
    """Decode packed BCD words into their decimal digit string.

    Returns ``(digits, complete)``; ``complete`` is False when any word was
    missing or held a non-decimal nibble.
    """
    digits = ""
    complete = True
    for word in words:
        if word is None:
            return digits, False
        for shift in (12, 8, 4, 0):
            digit = (word >> shift) & 0xF
            if digit > 9:
                complete = False
                digits += "?"
            else:
                digits += str(digit)
    return digits, complete


class DeviceInformation(BrinkComponent):
    """The unit's identification data (input register space)."""

    register_space = "input"
    register_ranges = _IDENTITY_RANGES

    def __init__(self, unit: ModbusUnit, *, model_override: int | None = None) -> None:
        """Initialize and, when the device type is unknown, trust the given model."""
        super().__init__(unit)
        self._model_override = model_override

    _base_sw_type = integer(
        4000,
        signed=False,
        description="Base module software type and major version",
    )
    _base_sw_minor_fix = integer(
        4001,
        signed=False,
        description="Base module software minor and fix version",
    )
    _base_sw_build = integer(
        4002,
        signed=False,
        description="Base module software build number",
    )
    _base_hw_version = integer(
        4003,
        signed=False,
        description="Base module hardware version (major, minor)",
    )
    _device_type = integer(
        4004,
        signed=False,
        description="The device type reported by the unit",
    )
    dipswitch = integer(
        4005,
        signed=False,
        description="The base module dipswitch value",
    )
    _serial_digits_0 = integer(
        4010,
        signed=False,
        description="Serial number digits 0-3 in BCD",
    )
    _serial_digits_1 = integer(
        4011,
        signed=False,
        description="Serial number digits 4-7 in BCD",
    )
    _serial_digits_2 = integer(
        4012,
        signed=False,
        description="Serial number digits 8-11 in BCD",
    )
    _serial_ascii_0 = integer(
        4013,
        signed=False,
        description="Alpha-numeric serial number characters 0-1 in ASCII",
    )
    _serial_ascii_1 = integer(
        4014,
        signed=False,
        description="Alpha-numeric serial number characters 2-3 in ASCII",
    )
    _serial_ascii_2 = integer(
        4015,
        signed=False,
        description="Alpha-numeric serial number characters 4-5 in ASCII",
    )
    _serial_ascii_3 = integer(
        4016,
        signed=False,
        description="Alpha-numeric serial number characters 6-7 in ASCII",
    )
    _serial_ascii_4 = integer(
        4017,
        signed=False,
        description="Alpha-numeric serial number characters 8-9 in ASCII",
    )
    _serial_ascii_5 = integer(
        4018,
        signed=False,
        description="Alpha-numeric serial number characters 10-11 in ASCII",
    )
    _uif_sw_type = integer(
        4400,
        signed=False,
        description="UIF module software type and major version",
    )
    _uif_sw_minor_fix = integer(
        4401,
        signed=False,
        description="UIF module software minor and fix version",
    )
    _uif_sw_build = integer(
        4402,
        signed=False,
        description="UIF module software build number",
    )
    _uif_hw_version = integer(
        4403,
        signed=False,
        description="UIF module hardware version (major, minor)",
    )
    uif_device_type = integer(
        4404,
        signed=False,
        description="The UIF module device type",
    )
    uif_dipswitch = integer(
        4405,
        signed=False,
        description="The UIF module dipswitch value",
    )
    _lang_data_type = integer(
        4410,
        signed=False,
        description="Language data type and major version",
    )
    _lang_data_minor_fix = integer(
        4411,
        signed=False,
        description="Language data minor and fix version",
    )
    _lang_data_build = integer(
        4412,
        signed=False,
        description="Language data build number",
    )
    _uif_sw_nr_type = integer(
        4413,
        signed=False,
        description="UIF software version type and major version",
    )
    _uif_sw_nr_minor_fix = integer(
        4414,
        signed=False,
        description="UIF software version minor and fix version",
    )
    _uif_sw_nr_build = integer(
        4415,
        signed=False,
        description="UIF software version build number",
    )
    local_uif_switch = integer(
        4420,
        signed=False,
        description="The UIF local switch position (0-3)",
    )
    local_button = integer(
        4421,
        signed=False,
        description="The UIF local button value",
    )

    @property
    def device_type(self) -> int | None:
        """Return the raw device-type code."""
        return self._device_type

    @property
    def software_version(self) -> str:
        """Return the base module software version, e.g. ``S1.01.02.0001``."""
        type_version = _type_version(self._base_sw_type)
        minor_fix = _minor_fix(self._base_sw_minor_fix)
        if minor_fix is None:
            return type_version
        if self._base_sw_build is None:
            return f"{type_version}.{minor_fix}"
        return f"{type_version}.{minor_fix}.{self._base_sw_build:04d}"

    @property
    def hardware_version(self) -> str:
        """Return the base module hardware version, e.g. ``H1.1``."""
        return _hardware_version(self._base_hw_version)

    @property
    def serial_number(self) -> str | None:
        """Return the numeric serial number as a 12-digit string."""
        words = [getattr(self, f"_serial_digits_{i}") for i in range(3)]
        if not any(words):
            return None
        digits, complete = _bcd_digits(*words)
        if not complete:
            return None
        return digits

    @property
    def serial_number_ascii(self) -> str | None:
        """Return the alpha-numeric serial number, e.g. ``1234567890AZ``."""
        chars = []
        for i in range(6):
            word = getattr(self, f"_serial_ascii_{i}")
            if not word:
                return None
            chars.append(chr((word >> 8) & 0xFF))
            chars.append(chr(word & 0xFF))
        return "".join(chars)

    @property
    def uif_software_version(self) -> str:
        """Return the UIF module software version, e.g. ``S1.01.02.0001``."""
        type_version = _type_version(self._uif_sw_type)
        minor_fix = _minor_fix(self._uif_sw_minor_fix)
        if minor_fix is None:
            return type_version
        if self._uif_sw_build is None:
            return f"{type_version}.{minor_fix}"
        return f"{type_version}.{minor_fix}.{self._uif_sw_build:04d}"

    @property
    def uif_hardware_version(self) -> str:
        """Return the UIF module hardware version, e.g. ``H1.1``."""
        return _hardware_version(self._uif_hw_version)

    @property
    def manufacturer(self) -> str:
        """Return the manufacturer name."""
        return "Brink"

    @property
    def model(self) -> str:
        """Return the user-facing model name."""
        if self._model_override is not None:
            return f"Brink Flair {self._model_override}"
        return model_name_for_device_type(self._device_type)
