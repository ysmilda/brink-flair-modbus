"""Writing registers of a Brink Flair unit (holding registers).

The Modbus installation regulations (UWA2-B/UWA2-E, 614882) document the
holding map 6000-7992 and the remote-control block 8000-8011 as readable in
full, so spans covering only documented registers are read as one block.
"""

from __future__ import annotations

from ..data_model import BrinkComponent, bit, boolean, enum, gauge, integer
from ..enums import (
    BypassMode,
    ControlMode,
    DateFormat,
    DigitalInputFunction,
    ExternalHeaterMode,
    FanFunction,
    FlowType,
    GeoValveOutput,
    GeoValvePosition,
    Language,
    ModbusInterfaceType,
    ModbusParity,
    ModbusSpeed,
    SignalOutputFunction,
    StandbyCommand,
    TimeNotation,
    VentilationLevel,
)
from ..flow_limits import MAX_FLOW, MAX_MODBUS_FLOW_RATE

_SETTINGS_RANGES = (
    (6000, 6003),  # volume flow presets 0-3
    (6010, 6017),  # PWM presets for inlet and exhaust fans 0-3
    (6030, 6036),  # flow type, switch/display use and imbalance settings
    (6100, 6105),  # bypass mode, temperatures, hysteresis, boost and fan step
    (6110, 6111),  # frost control and minimum inlet temperature
    (6120, 6120),  # days before the filter warning
    (6130, 6131),  # external heater mode and post-heater set point
    (6140, 6141),  # RHT humidity sensor mode and sensitivity
    (6150, 6158),  # CO2 sensor mode and low/high levels
    (6170, 6171),  # signal output function and CV connection
    (6200, 6203),  # digital input 1 switch type and fan functions
    (6210, 6213),  # digital input 2 switch type and fan functions
    (6220, 6222),  # analogue input 1 mode and voltage range
    (6230, 6232),  # analogue input 2 mode and voltage range
    (6240, 6244),  # geo heat-exchanger settings
    (6900, 6906),  # language, date/time format and clock
    (7990, 7993),  # Modbus interface type, address, speed and parity
    (8000, 8003),  # control mode, level, flow rate and standby
    (8010, 8011),  # filter reset and appliance reset
)


class Settings(BrinkComponent):
    """Writable airflow, sensor and filter settings of the unit."""

    register_space = "holding"
    register_ranges = _SETTINGS_RANGES

    flow_0 = integer(
        6000,
        signed=True,
        writable=True,
        unit="m³/h",
        min_value=0,
        max_value=MAX_FLOW,
        description="Configured volume flow for step 0",
    )
    flow_1 = integer(
        6001,
        signed=True,
        writable=True,
        unit="m³/h",
        min_value=50,
        max_value=MAX_FLOW,
        description="Configured volume flow for step 1",
    )
    flow_2 = integer(
        6002,
        signed=True,
        writable=True,
        unit="m³/h",
        min_value=50,
        max_value=MAX_FLOW,
        description="Configured volume flow for step 2",
    )
    flow_3 = integer(
        6003,
        signed=True,
        writable=True,
        unit="m³/h",
        min_value=50,
        max_value=MAX_FLOW,
        description="Configured volume flow for step 3",
    )
    pwm_inlet_0 = integer(
        6010,
        signed=False,
        writable=True,
        unit="%",
        min_value=15,
        max_value=100,
        description="PWM preset of the inlet fan for step 0",
    )
    pwm_exhaust_0 = integer(
        6011,
        signed=False,
        writable=True,
        unit="%",
        min_value=15,
        max_value=100,
        description="PWM preset of the exhaust fan for step 0",
    )
    pwm_inlet_1 = integer(
        6012,
        signed=False,
        writable=True,
        unit="%",
        min_value=15,
        max_value=100,
        description="PWM preset of the inlet fan for step 1",
    )
    pwm_exhaust_1 = integer(
        6013,
        signed=False,
        writable=True,
        unit="%",
        min_value=15,
        max_value=100,
        description="PWM preset of the exhaust fan for step 1",
    )
    pwm_inlet_2 = integer(
        6014,
        signed=False,
        writable=True,
        unit="%",
        min_value=15,
        max_value=100,
        description="PWM preset of the inlet fan for step 2",
    )
    pwm_exhaust_2 = integer(
        6015,
        signed=False,
        writable=True,
        unit="%",
        min_value=15,
        max_value=100,
        description="PWM preset of the exhaust fan for step 2",
    )
    pwm_inlet_3 = integer(
        6016,
        signed=False,
        writable=True,
        unit="%",
        min_value=15,
        max_value=100,
        description="PWM preset of the inlet fan for step 3",
    )
    pwm_exhaust_3 = integer(
        6017,
        signed=False,
        writable=True,
        unit="%",
        min_value=15,
        max_value=100,
        description="PWM preset of the exhaust fan for step 3",
    )
    flow_type = enum(
        6030,
        FlowType,
        writable=True,
        description="The fan control method",
    )
    switch_default_position = integer(
        6031,
        signed=False,
        writable=True,
        min_value=0,
        max_value=3,
        description="The flow-switch position used while no switch is connected",
    )
    display_as_switch = boolean(
        6032,
        writable=True,
        description="Whether the display acts as the flow switch",
    )
    imbalance_allowed = boolean(
        6033,
        writable=True,
        description="Whether inlet/exhaust imbalance is permitted",
    )
    imbalance_value = integer(
        6034,
        signed=False,
        writable=True,
        unit="%",
        min_value=0,
        max_value=20,
        description="Inlet flow increase relative to the exhaust",
    )
    # Fan imbalance trim, in tenths of a percent (register value x10).
    imbalance_intake = gauge(
        6035,
        0.1,
        signed=True,
        writable=True,
        unit="%",
        min_value=-15,
        max_value=15,
        step=1,
        description="Intake fan balance trim relative to a balanced rig",
    )
    imbalance_exhaust = gauge(
        6036,
        0.1,
        signed=True,
        writable=True,
        unit="%",
        min_value=-15,
        max_value=15,
        step=1,
        description="Exhaust fan balance trim relative to a balanced rig",
    )
    bypass_mode = enum(
        6100,
        BypassMode,
        writable=True,
        description="User selection that overrides the automatic bypass",
    )
    # Bypass control temperatures, in tenths of a degree (register value x10).
    bypass_from_dwelling = gauge(
        6101,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=15,
        max_value=35,
        step=0.5,
        description="Indoor temperature above which the bypass may open",
    )
    bypass_from_outside = gauge(
        6102,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=7,
        max_value=15,
        step=0.5,
        description="Outdoor temperature below which the bypass stays shut",
    )
    bypass_hysteresis = gauge(
        6103,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=0,
        max_value=5,
        step=0.5,
        description="Temperature hysteresis of the bypass logic",
    )
    bypass_boost = bit(
        6104,
        0,
        writable=True,
        description="Boost that opens the bypass while it is active",
    )
    bypass_boost_position = integer(
        6105,
        signed=True,
        writable=True,
        min_value=0,
        max_value=3,
        description="Fan position used while bypass boost is active",
    )
    # Frost-protection temperature thresholds, in tenths of a degree.
    frost_control_temperature = gauge(
        6110,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=-1.5,
        max_value=1.5,
        step=0.5,
        description="Temperature at which frost protection starts",
    )
    frost_minimum_inlet_temperature = gauge(
        6111,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=7,
        max_value=17,
        step=0.5,
        description="Coldest inlet air allowed before fan reduction",
    )
    filter_change_days = integer(
        6120,
        signed=True,
        writable=True,
        min_value=0,
        max_value=365,
        description="Days until the filter warning should appear",
    )
    external_heater_mode = enum(
        6130,
        ExternalHeaterMode,
        writable=True,
        description="How an external heater is used",
    )
    postheater_setpoint = gauge(
        6131,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=15,
        max_value=30,
        step=0.5,
        description="Temperature the post-heater targets",
    )
    rht_sensor_mode = boolean(
        6140,
        writable=True,
        description="Whether the humidity sensor steers ventilation",
    )
    rht_sensor_sensitivity = integer(
        6141,
        signed=True,
        writable=True,
        min_value=-2,
        max_value=2,
        description="Sensitivity of the humidity sensor",
    )
    co2_sensor_mode = boolean(
        6150,
        writable=True,
        description="Whether a CO2 sensor steers ventilation",
    )
    co2_1_low_level = integer(
        6151,
        signed=False,
        writable=True,
        unit="ppm",
        min_value=400,
        max_value=2000,
        description="Threshold below which CO2 sensor 1 targets low flow",
    )
    co2_1_high_level = integer(
        6152,
        signed=False,
        writable=True,
        unit="ppm",
        min_value=400,
        max_value=2000,
        description="Threshold above which CO2 sensor 1 targets high flow",
    )
    co2_2_low_level = integer(
        6153,
        signed=False,
        writable=True,
        unit="ppm",
        min_value=400,
        max_value=2000,
        description="Threshold below which CO2 sensor 2 targets low flow",
    )
    co2_2_high_level = integer(
        6154,
        signed=False,
        writable=True,
        unit="ppm",
        min_value=400,
        max_value=2000,
        description="Threshold above which CO2 sensor 2 targets high flow",
    )
    co2_3_low_level = integer(
        6155,
        signed=False,
        writable=True,
        unit="ppm",
        min_value=400,
        max_value=2000,
        description="Threshold below which CO2 sensor 3 targets low flow",
    )
    co2_3_high_level = integer(
        6156,
        signed=False,
        writable=True,
        unit="ppm",
        min_value=400,
        max_value=2000,
        description="Threshold above which CO2 sensor 3 targets high flow",
    )
    co2_4_low_level = integer(
        6157,
        signed=False,
        writable=True,
        unit="ppm",
        min_value=400,
        max_value=2000,
        description="Threshold below which CO2 sensor 4 targets low flow",
    )
    co2_4_high_level = integer(
        6158,
        signed=False,
        writable=True,
        unit="ppm",
        min_value=400,
        max_value=2000,
        description="Threshold above which CO2 sensor 4 targets high flow",
    )
    signal_output_function = enum(
        6170,
        SignalOutputFunction,
        writable=True,
        description="What the signal output reports",
    )
    cv_connected = boolean(
        6171,
        writable=True,
        description="Whether a central-heating exhaust is connected",
    )
    digital_input_1_closed = boolean(
        6200,
        writable=True,
        description="Whether digital input 1 is normally closed",
    )
    digital_input_1_function = enum(
        6201,
        DigitalInputFunction,
        writable=True,
        description="What digital input 1 does",
    )
    digital_input_1_supply_fan = enum(
        6202,
        FanFunction,
        writable=True,
        description="Supply-fan response to digital input 1",
    )
    digital_input_1_exhaust_fan = enum(
        6203,
        FanFunction,
        writable=True,
        description="Exhaust-fan response to digital input 1",
    )
    digital_input_2_closed = boolean(
        6210,
        writable=True,
        description="Whether digital input 2 is normally closed",
    )
    digital_input_2_function = enum(
        6211,
        DigitalInputFunction,
        writable=True,
        description="What digital input 2 does",
    )
    digital_input_2_supply_fan = enum(
        6212,
        FanFunction,
        writable=True,
        description="Supply-fan response to digital input 2",
    )
    digital_input_2_exhaust_fan = enum(
        6213,
        FanFunction,
        writable=True,
        description="Exhaust-fan response to digital input 2",
    )
    analogue_input_1_mode = boolean(
        6220,
        writable=True,
        description="Whether analogue input 1 is enabled",
    )
    analogue_input_1_vmin = gauge(
        6221,
        0.1,
        signed=False,
        writable=True,
        unit="V",
        min_value=0,
        max_value=10,
        step=0.5,
        description="Voltage at which analogue input 1 maps to minimum flow",
    )
    analogue_input_1_vmax = gauge(
        6222,
        0.1,
        signed=False,
        writable=True,
        unit="V",
        min_value=0,
        max_value=10,
        step=0.5,
        description="Voltage at which analogue input 1 maps to maximum flow",
    )
    analogue_input_2_mode = boolean(
        6230,
        writable=True,
        description="Whether analogue input 2 is enabled",
    )
    analogue_input_2_vmin = gauge(
        6231,
        0.1,
        signed=False,
        writable=True,
        unit="V",
        min_value=0,
        max_value=10,
        step=0.5,
        description="Voltage at which analogue input 2 maps to minimum flow",
    )
    analogue_input_2_vmax = gauge(
        6232,
        0.1,
        signed=False,
        writable=True,
        unit="V",
        min_value=0,
        max_value=10,
        step=0.5,
        description="Voltage at which analogue input 2 maps to maximum flow",
    )
    geo_exchanger = boolean(
        6240,
        writable=True,
        description="Whether the geo heat-exchanger is enabled",
    )
    geo_minimum_temperature = gauge(
        6241,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=0,
        max_value=10,
        step=0.5,
        description="Outdoor temperature below which the geo valve stays shut",
    )
    geo_maximum_temperature = gauge(
        6242,
        0.1,
        signed=True,
        writable=True,
        unit="°C",
        min_value=15,
        max_value=40,
        step=0.5,
        description="Outdoor temperature above which the geo valve opens",
    )
    geo_valve_default_position = enum(
        6243,
        GeoValvePosition,
        writable=True,
        description="Geo valve position when its output sits at 0V",
    )
    geo_valve_output = enum(
        6244,
        GeoValveOutput,
        writable=True,
        description="The output driving the geo valve",
    )
    language = enum(
        6900,
        Language,
        writable=True,
        description="The unit language",
    )
    date_format = enum(
        6901,
        DateFormat,
        writable=True,
        description="The date format",
    )
    time_notation = enum(
        6902,
        TimeNotation,
        writable=True,
        description="The clock format",
    )
    clock_month_day = integer(
        6903,
        signed=False,
        writable=True,
        min_value=0,
        max_value=0xFFFF,
        description="Unit clock month and day (high byte month, low byte day)",
    )
    clock_year = integer(
        6904,
        signed=False,
        writable=True,
        min_value=0,
        max_value=0xFFFF,
        description="Unit clock year",
    )
    clock_time = integer(
        6905,
        signed=False,
        writable=True,
        min_value=0,
        max_value=0xFFFF,
        description="Unit clock time (high byte hours, low byte minutes)",
    )
    clock_day_seconds = integer(
        6906,
        signed=False,
        writable=True,
        min_value=0,
        max_value=0xFFFF,
        description="Unit clock weekday and seconds (high byte weekday, low byte seconds)",
    )
    modbus_interface_type = enum(
        7990,
        ModbusInterfaceType,
        writable=True,
        description="Where the Modbus interface is wired",
    )
    modbus_slave_address = integer(
        7991,
        signed=False,
        writable=True,
        min_value=1,
        max_value=247,
        description="The Modbus slave address",
    )
    modbus_speed = enum(
        7992,
        ModbusSpeed,
        writable=True,
        description="The Modbus baud rate",
    )
    modbus_parity = enum(
        7993,
        ModbusParity,
        writable=True,
        description="The Modbus parity setting",
    )
    control_mode = enum(
        8000,
        ControlMode,
        writable=True,
        description="The unit's control mode",
    )
    level = enum(
        8001,
        VentilationLevel,
        writable=True,
        description="The manual ventilation level",
    )
    desired_flow_rate = integer(
        8002,
        signed=False,
        writable=True,
        unit="m³/h",
        min_value=0,
        max_value=MAX_MODBUS_FLOW_RATE,
        description="Target volume flow in Flow mode",
    )
    standby = enum(
        8003,
        StandbyCommand,
        writable=True,
        description="Ask the unit into or out of standby",
    )
    reset_filter = bit(
        8010,
        0,
        writable=True,
        description="Pulse to reset the filter counter",
    )
    reset_appliance = boolean(
        8011,
        writable=True,
        description="Pulse to reset the appliance",
    )
