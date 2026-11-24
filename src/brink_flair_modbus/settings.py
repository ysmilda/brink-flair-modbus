"""The unit's settings, as one table.

Each entry names the FlairState field it fills, the holding register it lives
in, how to decode the register value into that field, and how to encode a
value back into a register for writing. The device reads and writes through
this table, and callers can describe their settings with it, so each register
is written down once.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from . import registers as r
from .registers import signed


def _flag(regs: Sequence[int]) -> bool:
    return regs[0] == 1


def _flag_value(value: bool) -> int:
    return 1 if value else 0


def _integer(regs: Sequence[int]) -> int:
    return regs[0]


type FlowPresets = tuple[int, int, int, int]
"""The airflow in m3/h for ventilation levels 0 to 3."""


def _presets(regs: Sequence[int]) -> FlowPresets:
    return (regs[0], regs[1], regs[2], regs[3])


def _tenths(regs: Sequence[int]) -> float:
    return regs[0] / 10


def _tenths_value(value: float) -> int:
    return round(value * 10)


def _signed_tenths(regs: Sequence[int]) -> float:
    return signed(regs[0]) / 10


def _signed_tenths_value(value: float) -> int:
    return round(value * 10) & 0xFFFF


def _signed_percent(regs: Sequence[int]) -> int:
    return signed(regs[0])


def _percent_value(value: int) -> int:
    return int(value) & 0xFFFF


@dataclass(frozen=True, kw_only=True)
class Setting[V]:
    """A setting kept in one or more holding registers, with values of type V."""

    field: str
    """The FlairState field this setting fills."""
    address: int
    """The first holding register, as the Brink document lists it."""
    decode: Callable[[Sequence[int]], V]
    """Turns the register values into the field's value."""
    encode: Callable[[V], int] | None
    """Turns a value into the register value to write, or None for a setting
    the device writes with a method of its own, such as the flow presets."""
    count: int = 1
    """How many registers the setting spans."""
    optional: bool = False
    """Whether not every unit or firmware serves it."""


FLOW_PRESETS: Setting[FlowPresets] = Setting(
    field="flow_presets",
    address=r.HR_FLOW_PRESETS,
    count=4,
    decode=_presets,
    encode=None,
)
BYPASS_MODE: Setting[int] = Setting(
    field="bypass_mode",
    address=r.HR_BYPASS_MODE,
    decode=_integer,
    encode=int,
)
BYPASS_TEMP_INDOOR: Setting[float] = Setting(
    field="bypass_temp_indoor",
    address=r.HR_BYPASS_TEMP_INDOOR,
    decode=_tenths,
    encode=_tenths_value,
)
BYPASS_TEMP_OUTDOOR: Setting[float] = Setting(
    field="bypass_temp_outdoor",
    address=r.HR_BYPASS_TEMP_OUTDOOR,
    decode=_tenths,
    encode=_tenths_value,
)
BYPASS_HYSTERESIS: Setting[float] = Setting(
    field="bypass_hysteresis",
    address=r.HR_BYPASS_HYSTERESIS,
    decode=_tenths,
    encode=_tenths_value,
)
FILTER_INTERVAL: Setting[int] = Setting(
    field="filter_interval_days",
    address=r.HR_FILTER_DAYS,
    decode=_integer,
    encode=int,
)

IMBALANCE_ALLOWED: Setting[bool] = Setting(
    field="imbalance_allowed",
    address=r.HR_IMBALANCE_ALLOWED,
    decode=_flag,
    encode=_flag_value,
    optional=True,
)
SUPPLY_IMBALANCE: Setting[int] = Setting(
    field="supply_imbalance",
    address=r.HR_SUPPLY_IMBALANCE,
    decode=_signed_percent,
    encode=_percent_value,
    optional=True,
)
EXHAUST_IMBALANCE: Setting[int] = Setting(
    field="exhaust_imbalance",
    address=r.HR_EXHAUST_IMBALANCE,
    decode=_signed_percent,
    encode=_percent_value,
    optional=True,
)
GEO_HEAT_EXCHANGER: Setting[bool] = Setting(
    field="geo_heat_exchanger",
    address=r.HR_GEO_HEAT_EXCHANGER,
    decode=_flag,
    encode=_flag_value,
    optional=True,
)
GEO_MIN_TEMP: Setting[float] = Setting(
    field="geo_min_temp",
    address=r.HR_GEO_MIN_TEMP,
    decode=_signed_tenths,
    encode=_signed_tenths_value,
    optional=True,
)
GEO_MAX_TEMP: Setting[float] = Setting(
    field="geo_max_temp",
    address=r.HR_GEO_MAX_TEMP,
    decode=_signed_tenths,
    encode=_signed_tenths_value,
    optional=True,
)

SETTINGS: tuple[Setting[Any], ...] = (
    FLOW_PRESETS,
    BYPASS_MODE,
    BYPASS_TEMP_INDOOR,
    BYPASS_TEMP_OUTDOOR,
    BYPASS_HYSTERESIS,
    FILTER_INTERVAL,
    IMBALANCE_ALLOWED,
    SUPPLY_IMBALANCE,
    EXHAUST_IMBALANCE,
    GEO_HEAT_EXCHANGER,
    GEO_MIN_TEMP,
    GEO_MAX_TEMP,
)


def _end(group: Sequence[Setting[Any]]) -> int:
    return group[-1].address + group[-1].count


def read_groups(settings: Sequence[Setting[Any]]) -> list[list[Setting[Any]]]:
    """Group settings whose registers are contiguous, so each group is one read.

    Required and optional settings are never mixed, because an optional read
    can fail without failing the rest.
    """
    groups: list[list[Setting[Any]]] = []
    for setting in sorted(settings, key=lambda s: (s.optional, s.address)):
        if groups:
            last = groups[-1]
            if last[0].optional == setting.optional and setting.address == _end(last):
                last.append(setting)
                continue
        groups.append([setting])
    return groups


def span(group: Sequence[Setting[Any]]) -> tuple[int, int]:
    """Return the first register and the number of registers a group reads."""
    start = group[0].address
    return start, _end(group) - start


SETTING_GROUPS: tuple[list[Setting[Any]], ...] = tuple(read_groups(SETTINGS))
