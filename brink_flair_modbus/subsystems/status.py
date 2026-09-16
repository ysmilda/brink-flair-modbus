"""Operating status of a Brink Flair unit (input registers).

The status registers sit a few addresses apart in the readable input map
4000-4801 (Modbus installation regulations, UWA2-B/UWA2-E 614882), so each
cluster is read as its own block.
"""

from __future__ import annotations

from ..data_model import BrinkComponent, boolean, enum, integer
from ..enums import (
    BypassStatus,
    Co2SensorStatus,
    EBusPowerStatus,
    FanControlType,
    FanStatus,
    FrostStatus,
    GeoExchangerStatus,
    OperatingMode,
    PreheaterStatus,
    SystemErrorStatus,
    VentilationMode,
)

_STATUS_RANGES = (
    (4020, 4022),  # active function, fan control type, ventilation mode
    (4030, 4030),  # supply fan inlet state
    (4040, 4040),  # exhaust fan state
    (4050, 4050),  # bypass position
    (4060, 4060),  # preheater state
    (4070, 4070),  # frost-protection state
    (4080, 4080),  # flow switch position
    (4090, 4090),  # signal output
    (4100, 4101),  # filter-dirty flag and eBus power state
    (4150, 4150),  # geo heat-exchanger valve state
    (4200, 4207),  # CO2 sensor states and values
    (4800, 4801),  # overall system error state and active incident
)


class Status(BrinkComponent):
    """Mode, bypass, frost, filter and sensor states of the unit."""

    register_space = "input"
    register_ranges = _STATUS_RANGES

    operation_mode = enum(
        4020,
        OperatingMode,
        description="The unit's current operating mode",
    )
    fan_control_type = enum(
        4021,
        FanControlType,
        description="The method used to control the fans",
    )
    ventilation_mode = enum(
        4022,
        VentilationMode,
        description="The currently active ventilation mode",
    )
    supply_fan_status = enum(
        4030,
        FanStatus,
        description="The supply fan inlet state",
    )
    exhaust_fan_status = enum(
        4040,
        FanStatus,
        description="The exhaust fan state",
    )
    bypass_status = enum(
        4050,
        BypassStatus,
        description="The heat-recovery bypass position",
    )
    preheater_status = enum(
        4060,
        PreheaterStatus,
        description="The preheater state",
    )
    frost_status = enum(
        4070,
        FrostStatus,
        description="The frost-protection state",
    )
    flow_switch_position = integer(
        4080,
        signed=False,
        min_value=0,
        max_value=3,
        description="The flow switch position (0-3, 255 invalid)",
    )
    signal_output = integer(
        4090,
        signed=False,
        min_value=0,
        max_value=1,
        description="The signal output level (0V or 24V)",
    )
    filter_dirty = boolean(
        4100,
        description="Whether the filter counter has expired",
    )
    ebus_power_status = enum(
        4101,
        EBusPowerStatus,
        description="The eBus power state",
    )
    geo_exchanger_status = enum(
        4150,
        GeoExchangerStatus,
        description="The geo heat-exchanger valve state",
    )
    co2_1_status = enum(
        4200,
        Co2SensorStatus,
        description="The state of CO2 sensor 1",
    )
    co2_1_value = integer(
        4201,
        signed=False,
        unit="ppm",
        description="The measured CO2 concentration of sensor 1",
    )
    co2_2_status = enum(
        4202,
        Co2SensorStatus,
        description="The state of CO2 sensor 2",
    )
    co2_2_value = integer(
        4203,
        signed=False,
        unit="ppm",
        description="The measured CO2 concentration of sensor 2",
    )
    co2_3_status = enum(
        4204,
        Co2SensorStatus,
        description="The state of CO2 sensor 3",
    )
    co2_3_value = integer(
        4205,
        signed=False,
        unit="ppm",
        description="The measured CO2 concentration of sensor 3",
    )
    co2_4_status = enum(
        4206,
        Co2SensorStatus,
        description="The state of CO2 sensor 4",
    )
    co2_4_value = integer(
        4207,
        signed=False,
        unit="ppm",
        description="The measured CO2 concentration of sensor 4",
    )
    system_error = enum(
        4800,
        SystemErrorStatus,
        description="The overall system error state",
    )
    active_incident = integer(
        4801,
        signed=False,
        description="The active incident error code (0 when none)",
    )
