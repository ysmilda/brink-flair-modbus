"""Brink-specific field factories layered on ``modbus_connection.model``."""

from __future__ import annotations

from collections.abc import Iterable
from enum import IntEnum
from typing import Any

from modbus_connection.model import (
    Component,
    NumberField,
    PackedBitField,
    WriteValidator,
    bit as _modbus_bit,
    boolean as _modbus_boolean,
    enum as _modbus_enum,
    gauge as _modbus_gauge,
    integer as _modbus_integer,
    uint32 as _modbus_uint32,
)

from .exceptions import BrinkValueValidationError
from .metadata import (
    BooleanMetadata,
    DatapointMetadata,
    EnumMetadata,
    NumberMetadata,
    OptionMetadata,
    attach_metadata,
    step_from_digits,
)

NAN_INT16 = 0x7FFF  # the value the unit returns for an absent sensor


def _range_validator(
    min_value: float | None, max_value: float | None
) -> WriteValidator:
    """Return a write validator enforcing the documented value range."""

    def validate(value: Any) -> Any:
        number = float(value)
        if min_value is not None and number < min_value:
            raise BrinkValueValidationError(
                f"Value {value} is below minimum {min_value}"
            )
        if max_value is not None and number > max_value:
            raise BrinkValueValidationError(
                f"Value {value} is above maximum {max_value}"
            )
        return value

    return validate


def _enum_validator(enum_type: type[IntEnum]) -> WriteValidator:
    """Return a write validator coercing a value to a known enum member."""

    def validate(value: Any) -> Any:
        try:
            return enum_type(value)
        except (TypeError, ValueError) as err:
            raise BrinkValueValidationError(
                f"{value!r} is not valid for {enum_type.__name__}"
            ) from err

    return validate


def _validated_writable(
    writable: bool | WriteValidator, validator: WriteValidator
) -> bool | WriteValidator:
    """Return ``writable``, applying ``validator`` to plain-``True`` writes.

    A custom validator always wins: the caller already vetting the value takes
    precedence over the automatic range check or enum coercion.
    """
    if not writable:
        return False
    if callable(writable):
        return writable
    return validator


def _attach_number_metadata[T](
    field: NumberField[T],
    *,
    writable: bool | WriteValidator,
    description: str | None,
    min_value: float | None,
    max_value: float | None,
    step: float | None,
    digits: int | None,
    unit: str | None,
) -> NumberField[T]:
    """Attach the neutral metadata shared by every numeric field."""
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="number",
            description=description,
            writable=bool(writable),
            number=NumberMetadata(
                min_value=min_value,
                max_value=max_value,
                step=step,
                digits=digits,
                unit=unit,
            ),
        ),
    )


def integer(
    address: int,
    *,
    signed: bool = True,
    nan: int | Iterable[int] | None = None,
    stride: int = 0,
    writable: bool | WriteValidator = False,
    unit: str | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
    step: int | None = None,
    digits: int | None = None,
    description: str | None = None,
) -> NumberField[int]:
    """Create an integer field at a protocol register address."""
    field = _modbus_integer(
        address,
        signed=signed,
        nan=nan,
        stride=stride,
        writable=_validated_writable(writable, _range_validator(min_value, max_value)),
        unit=unit,
    )
    return _attach_number_metadata(
        field,
        writable=writable,
        description=description,
        min_value=min_value,
        max_value=max_value,
        step=step if step is not None else step_from_digits(digits),
        digits=digits,
        unit=unit,
    )


def gauge(
    address: int,
    scale: float,
    *,
    signed: bool = True,
    nan: int | Iterable[int] | None = None,
    stride: int = 0,
    writable: bool | WriteValidator = False,
    unit: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    step: float | None = None,
    digits: int | None = None,
    description: str | None = None,
) -> NumberField[float]:
    """Create a scaled numeric field at a protocol register address."""
    field = _modbus_gauge(
        address,
        scale,
        signed=signed,
        nan=nan,
        stride=stride,
        writable=_validated_writable(writable, _range_validator(min_value, max_value)),
        unit=unit,
    )
    return _attach_number_metadata(
        field,
        writable=writable,
        description=description,
        min_value=min_value,
        max_value=max_value,
        step=step if step is not None else step_from_digits(digits),
        digits=digits,
        unit=unit,
    )


def enum[E: IntEnum](
    address: int,
    enum_type: type[E],
    *,
    options: tuple[OptionMetadata, ...] | None = None,
    writable: bool | WriteValidator = False,
    description: str | None = None,
) -> NumberField[E]:
    """Create an enum field at a protocol register address."""
    field = _modbus_enum(
        address,
        enum_type,
        writable=_validated_writable(writable, _enum_validator(enum_type)),
    )
    resolved_options = options or tuple(
        OptionMetadata(member.name.lower(), int(member), member.name)
        for member in enum_type
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="enum",
            description=description,
            writable=bool(writable),
            enum=EnumMetadata(enum_type=enum_type, options=resolved_options),
        ),
    )


def boolean(
    address: int,
    *,
    writable: bool | WriteValidator = False,
    description: str | None = None,
) -> NumberField[bool]:
    """Create a 0/1 register field decoding to ``bool``."""
    return attach_metadata(
        _modbus_boolean(address, writable=writable),
        DatapointMetadata(
            value_kind="boolean",
            description=description,
            writable=bool(writable),
            boolean=BooleanMetadata(),
        ),
    )


def uint32(
    address: int,
    *,
    unit: str | None = None,
    description: str | None = None,
) -> NumberField[int]:
    """Create a 32-bit unsigned counter field at a protocol address."""
    field = _modbus_uint32(address, unit=unit)
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="number",
            description=description,
            writable=False,
            number=NumberMetadata(unit=unit, min_value=0),
        ),
    )


def bit(
    address: int,
    index: int,
    *,
    writable: bool | WriteValidator = False,
    description: str | None = None,
) -> PackedBitField:
    """Create one bit of a register as ``bool``."""
    field = _modbus_bit(address, index, writable=writable)
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="boolean",
            description=description,
            writable=bool(writable),
            boolean=BooleanMetadata(),
        ),
    )


class BrinkComponent(Component):
    """A Brink Flair sub-system: typed fields over readable register ranges."""
