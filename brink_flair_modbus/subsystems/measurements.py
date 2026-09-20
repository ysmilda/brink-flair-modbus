"""Airflow and climate measurements of a Brink Flair unit (input registers).

All values are read from the input register space (FC04). Register addresses
are the unit's protocol addresses as published in the Brink Flair Modbus
register map.
"""

from __future__ import annotations

from ..data_model import (
    NAN_INT16,
    BrinkComponent,
    gauge,
    integer,
    uint32,
)

_ABSENT_DWELLING = 0x270F  # 9999: the dwelling NTC reads this while unplugged

# The Modbus installation regulations (UWA2-B/UWA2-E, 614882) document the
# input map 4000-4544 as readable in full, so spans that only cover documented
# registers are read as one block: fewer requests per poll at no extra risk.
# The extension module's own registers (4520-4544) live in ExtensionModule,
# which is read apart from this pooled update.
_MEASUREMENT_RANGES = (
    (4023, 4024),  # supply and exhaust static pressure
    (4031, 4037),  # supply airflow, fan speed and climate
    (4041, 4047),  # exhaust airflow, fan speed and climate
    (4051, 4051),  # bypass step position
    (4061, 4061),  # preheater capacity
    (4071, 4072),  # frost heater power and fan reduction
    (4081, 4083),  # NTC1 and NTC2 temperature and RHT humidity
    (4110, 4111),  # current time and date
    (4113, 4114),  # operating time in hours (32-bit)
    (4115, 4119),  # filter counters and total flow
)


class Measurements(BrinkComponent):
    """Airflow, pressure and climate measurements of the unit."""

    register_space = "input"
    register_ranges = _MEASUREMENT_RANGES

    supply_pressure = integer(
        4023,
        signed=True,
        nan=NAN_INT16,
        unit="Pa",
        description="Static pressure at the supply side",
    )
    exhaust_pressure = integer(
        4024,
        signed=True,
        nan=NAN_INT16,
        unit="Pa",
        description="Static pressure at the exhaust side",
    )
    setpoint_supply_volume = integer(
        4031,
        signed=False,
        unit="m³/h",
        description="The configured supply volume flow set point",
    )
    supply_volume = integer(
        4032,
        signed=False,
        unit="m³/h",
        description="Actual supply volume flow",
    )
    supply_mass_flow = integer(
        4033,
        signed=False,
        unit="kg/h",
        description="Actual supply mass flow",
    )
    supply_fan_rpm = integer(
        4034,
        signed=False,
        unit="rpm",
        description="Supply fan speed",
    )
    supply_anemometer_rpm = integer(
        4035,
        signed=False,
        unit="rpm",
        description="Supply inlet anemometer speed",
    )
    supply_temperature = gauge(
        4036,
        0.1,
        signed=True,
        nan=NAN_INT16,
        unit="°C",
        digits=1,
        description="Temperature of the air supplied to the house",
    )
    supply_relative_humidity = integer(
        4037,
        signed=True,
        unit="%",
        description="Relative humidity of the air supplied to the house",
    )
    setpoint_exhaust_volume = integer(
        4041,
        signed=False,
        unit="m³/h",
        description="The configured exhaust volume flow set point",
    )
    exhaust_volume = integer(
        4042,
        signed=False,
        unit="m³/h",
        description="Actual exhaust volume flow",
    )
    exhaust_mass_flow = integer(
        4043,
        signed=False,
        unit="kg/h",
        description="Actual exhaust mass flow",
    )
    exhaust_fan_rpm = integer(
        4044,
        signed=False,
        unit="rpm",
        description="Exhaust fan speed",
    )
    exhaust_anemometer_rpm = integer(
        4045,
        signed=False,
        unit="rpm",
        description="Exhaust anemometer speed",
    )
    exhaust_temperature = gauge(
        4046,
        0.1,
        signed=True,
        nan=NAN_INT16,
        unit="°C",
        digits=1,
        description="Temperature of the air exhausted from the house",
    )
    exhaust_relative_humidity = integer(
        4047,
        signed=True,
        unit="%",
        description="Relative humidity of the air exhausted from the house",
    )
    bypass_step_position = integer(
        4051,
        signed=False,
        description="The bypass step position relative to its point of zero",
    )
    preheater_capacity = integer(
        4061,
        signed=False,
        unit="%",
        description="The preheater output as a percentage of its capacity",
    )
    frost_heater_setpoint = integer(
        4071,
        signed=True,
        unit="%",
        description="The frost heater power set point",
    )
    frost_fan_reduction = integer(
        4072,
        signed=True,
        unit="%",
        description="Fan reduction applied during frost protection",
    )
    outside_temperature = gauge(
        4081,
        0.1,
        signed=True,
        nan=NAN_INT16,
        unit="°C",
        digits=1,
        description="Outside temperature",
    )
    dwelling_temperature = gauge(
        4082,
        0.1,
        signed=True,
        nan=(NAN_INT16, _ABSENT_DWELLING),
        unit="°C",
        digits=1,
        description="Dwelling temperature (Flair 450/600)",
    )
    rht_humidity = gauge(
        4083,
        0.1,
        signed=False,
        unit="%",
        digits=1,
        description="Ambient relative humidity reported by the RHT sensor",
    )
    _current_time_word = integer(
        4110,
        signed=False,
        description="Current time (high byte hours, low byte minutes)",
    )
    _current_date_word = integer(
        4111,
        signed=False,
        description="Current date (high byte days, low byte year within decade)",
    )
    current_operating_time = uint32(
        4113,
        unit="h",
        description="Total operating time in hours",
    )
    filter_used_hours = integer(
        4115,
        signed=False,
        description="Hours of operation counted by the filter counter",
    )
    filter_used_volume = uint32(
        4116,
        unit="m³/h",
        description="Total volume channeled through the filter",
    )
    total_flow = uint32(
        4118,
        unit="m³/h",
        description="Total volume channeled through the unit",
    )

    @property
    def filter_used_days(self) -> float | None:
        """Return the elapsed filter lifetime in days."""
        hours = self.filter_used_hours
        if hours is None:
            return None
        return hours / 24

    @property
    def current_time(self) -> str | None:
        """Return the unit clock as ``HH:MM`` (input register 4110)."""
        word = self._current_time_word
        if word is None:
            return None
        return f"{(word >> 8) & 0xFF:02d}:{word & 0xFF:02d}"

    @property
    def current_date(self) -> str | None:
        """Return the unit date as ``DD-YY`` (input register 4111).

        The register carries only the day and the year within the current
        decade, so the returned date is necessarily approximate.
        """
        word = self._current_date_word
        if word is None:
            return None
        return f"{(word >> 8) & 0xFF:02d}-{word & 0xFF:02d}"
