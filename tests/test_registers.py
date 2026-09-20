"""Tests for registers implemented across all subsystems."""

from __future__ import annotations

from modbus_connection import ExceptionCode, ModbusExceptionError
from modbus_connection.mock import MockModbusUnit, WriteEvent

from brink_flair_modbus import (
    BrinkFlair,
    Co2SensorStatus,
    ControlMode,
    DigitalInputFunction,
    EBusPowerStatus,
    ExternalHeaterMode,
    FanControlType,
    FanFunction,
    FanStatus,
    FlowType,
    GeoExchangerStatus,
    GeoValveOutput,
    Language,
    ModbusParity,
    ModbusSpeed,
    OperatingMode,
    PreheaterStatus,
    SignalOutputFunction,
    StandbyCommand,
    SystemErrorStatus,
    VentilationMode,
)


def _writes(unit: MockModbusUnit) -> list[WriteEvent]:
    captured: list[WriteEvent] = []
    unit.on_write(captured.append)
    return captured


async def test_device_information_identity_registers(unit: MockModbusUnit) -> None:
    unit.input[4000] = 0x5331  # ASCII 'S', major 1
    unit.input[4001] = 0x0103  # minor 1, fix 3
    unit.input[4002] = 1  # build 0001
    unit.input[4003] = 0x0101  # hardware major 1, minor 1
    unit.input[4004] = 24
    unit.input[4005] = 3
    unit.input[4010] = 0x1234
    unit.input[4011] = 0x5678
    unit.input[4012] = 0x9012
    unit.input[4013] = 0x3132  # "12"
    unit.input[4014] = 0x3334  # "34"
    unit.input[4015] = 0x3536  # "56"
    unit.input[4016] = 0x3738  # "78"
    unit.input[4017] = 0x3930  # "90"
    unit.input[4018] = 0x415A  # "AZ"
    unit.input[4400] = 0x5331
    unit.input[4401] = 0x0103
    unit.input[4402] = 1
    unit.input[4403] = 0x0200

    device = BrinkFlair(unit)
    await device.async_update()

    info = device.info
    assert info.software_version == "S1.01.03.0001"
    assert info.hardware_version == "H1.1"
    assert info.manufacturer == "Brink"
    assert info.dipswitch == 3
    assert info.serial_number == "123456789012"
    assert info.serial_number_ascii == "1234567890AZ"
    assert info.uif_software_version == "S1.01.03.0001"
    assert info.uif_hardware_version == "H2.0"


async def test_extension_module_identity(unit: MockModbusUnit) -> None:
    unit.input[4500] = 0x5331
    unit.input[4501] = 0x0103
    unit.input[4502] = 1
    unit.input[4503] = 0x0100
    unit.input[4504] = 24
    unit.input[4505] = 3

    device = BrinkFlair(unit)
    await device.async_update()

    assert device.extension.available is True
    assert device.extension_available is True
    assert device.extension.device_type == 24
    assert device.extension.dipswitch == 3
    assert device.extension.software_version == "S1.01.03.0001"
    assert device.extension.hardware_version == "H1.0"


async def test_extension_module_measurements(unit: MockModbusUnit) -> None:
    unit.input[4520] = 245  # extension NTC 24.5 C
    unit.input[4521] = 1  # extension contact 1 closed
    unit.input[4522] = 0
    unit.input[4523] = 55  # extension analogue input 1, 5.5 V
    unit.input[4524] = 68
    unit.input[4541] = 1  # extension relay 1 energized
    unit.input[4542] = 0
    unit.input[4543] = 100  # extension analogue output 1, 10.0 V
    unit.input[4544] = 150

    device = BrinkFlair(unit)
    await device.async_update()

    extension = device.extension
    assert extension.temperature == 24.5
    assert extension.contact_1 is True
    assert extension.contact_2 is False
    assert extension.analogue_input_1 == 5.5
    assert extension.analogue_input_2 == 6.8
    assert extension.relay_1 is True
    assert extension.relay_2 is False
    assert extension.analogue_output_1 == 10.0
    assert extension.analogue_output_2 == 15.0


async def test_extension_module_unavailable(unit: MockModbusUnit) -> None:
    unit.input[4004] = 24
    unit.input[4036] = 250  # supply temperature, raw value x10
    unit.fail_read(
        4500,
        ModbusExceptionError(ExceptionCode.ILLEGAL_DATA_ADDRESS),
        register_type="input",
    )

    device = BrinkFlair(unit)
    await device.async_update()

    assert device.extension.available is False
    assert device.extension_available is False
    assert device.extension.device_type is None
    assert device.extension.temperature is None
    assert device.info.device_type == 24
    assert device.measurements.supply_temperature == 25.0


async def test_extension_module_probe_unavailable(unit: MockModbusUnit) -> None:
    unit.fail_read(
        4500,
        ModbusExceptionError(ExceptionCode.ILLEGAL_DATA_ADDRESS),
        register_type="input",
    )

    device = BrinkFlair(unit)
    await device.extension.async_update()

    assert device.extension.available is False
    assert device.extension.software_version == "unknown"


async def test_extension_module_recheck(unit: MockModbusUnit) -> None:
    unit.input[4504] = 24
    device = BrinkFlair(unit)

    await device.extension.async_update()
    assert device.extension_available is True

    unit.fail_read(
        4500,
        ModbusExceptionError(ExceptionCode.ILLEGAL_DATA_ADDRESS),
        register_type="input",
    )
    await device.async_recheck_extension()
    assert device.extension_available is False
    assert device.extension.device_type is None

    unit.fail_read(4500, None, register_type="input")
    unit.input[4500] = 0x5331
    unit.input[4501] = 0x0103
    unit.input[4502] = 1
    unit.input[4503] = 0x0100
    unit.input[4504] = 24
    unit.input[4505] = 3
    await device.async_recheck_extension()
    assert device.extension_available is True
    assert device.extension.device_type == 24
    assert device.extension.software_version == "S1.01.03.0001"


async def test_serial_number_unread_returns_none(unit: MockModbusUnit) -> None:
    device = BrinkFlair(unit)
    await device.async_update()
    assert device.info.serial_number is None
    assert device.info.serial_number_ascii is None


async def test_status_registers(unit: MockModbusUnit) -> None:
    unit.input[4020] = int(OperatingMode.AUTO_MODBUS)
    unit.input[4021] = int(FanControlType.CONSTANT_FLOW)
    unit.input[4022] = int(VentilationMode.AUTO)
    unit.input[4030] = int(FanStatus.RUNNING)
    unit.input[4040] = int(FanStatus.FAN_ERROR)
    unit.input[4060] = int(PreheaterStatus.ACTIVE)
    unit.input[4080] = 2
    unit.input[4090] = 1
    unit.input[4100] = 1
    unit.input[4101] = int(EBusPowerStatus.POWER_ON)
    unit.input[4150] = int(GeoExchangerStatus.OPEN_HIGH)
    unit.input[4200] = int(Co2SensorStatus.RUNNING)
    unit.input[4201] = 800
    unit.input[4202] = int(Co2SensorStatus.ERROR)
    unit.input[4800] = int(SystemErrorStatus.WARNING)
    unit.input[4801] = 214

    device = BrinkFlair(unit)
    await device.async_update()

    status = device.status
    assert status.operation_mode == OperatingMode.AUTO_MODBUS
    assert status.fan_control_type == FanControlType.CONSTANT_FLOW
    assert status.ventilation_mode == VentilationMode.AUTO
    assert status.supply_fan_status == FanStatus.RUNNING
    assert status.exhaust_fan_status == FanStatus.FAN_ERROR
    assert status.preheater_status == PreheaterStatus.ACTIVE
    assert status.flow_switch_position == 2
    assert status.signal_output == 1
    assert status.filter_dirty is True
    assert status.ebus_power_status == EBusPowerStatus.POWER_ON
    assert status.geo_exchanger_status == GeoExchangerStatus.OPEN_HIGH
    assert status.co2_1_status == Co2SensorStatus.RUNNING
    assert status.co2_1_value == 800
    assert status.co2_2_status == Co2SensorStatus.ERROR
    assert status.system_error == SystemErrorStatus.WARNING
    assert status.active_incident == 214


async def test_measurement_registers(unit: MockModbusUnit) -> None:
    unit.input[4033] = 120  # supply mass flow kg/h
    unit.input[4035] = 1000  # supply anemometer rpm
    unit.input[4043] = 110  # exhaust mass flow kg/h
    unit.input[4045] = 990  # exhaust anemometer rpm
    unit.input[4051] = 1234  # bypass step position
    unit.input[4061] = 42  # preheater capacity %
    unit.input[4082] = 215  # dwelling temperature 21.5 C
    unit.input[4083] = 550  # RHT humidity 55.0 %
    unit.input[4110] = 0x1230  # 18:48
    unit.input[4111] = 0x1507  # day 21, year 7
    unit.input[4113] = 0x0001  # operating time high word
    unit.input[4114] = 0x86A0  # operating time low word (0x186A0 = 100000 h)
    unit.input[4118] = 0x1234  # total flow high word
    unit.input[4119] = 0x5678  # total flow low word

    device = BrinkFlair(unit)
    await device.async_update()

    measurements = device.measurements
    assert measurements.supply_mass_flow == 120
    assert measurements.supply_anemometer_rpm == 1000
    assert measurements.exhaust_mass_flow == 110
    assert measurements.exhaust_anemometer_rpm == 990
    assert measurements.bypass_step_position == 1234
    assert measurements.preheater_capacity == 42
    assert measurements.dwelling_temperature == 21.5
    assert measurements.rht_humidity == 55.0
    assert measurements.current_time == "18:48"
    assert measurements.current_date == "21-07"
    assert measurements.current_operating_time == 100000
    assert measurements.total_flow == 0x12345678


async def test_dwelling_temperature_sensor_unplugged(unit: MockModbusUnit) -> None:
    device = BrinkFlair(unit)

    unit.input[4082] = 9999  # 0x270F: dwelling NTC reads this while unplugged
    await device.async_update()
    assert device.measurements.dwelling_temperature is None

    unit.input[4082] = 0x7FFF  # NAN_INT16: shared "absent sensor" sentinel
    await device.async_update()
    assert device.measurements.dwelling_temperature is None


async def test_settings_holding_registers(unit: MockModbusUnit) -> None:
    unit.holding[6010] = 20  # PWM inlet preset 0
    unit.holding[6017] = 90  # PWM exhaust preset 3
    unit.holding[6030] = int(FlowType.CONSTANT_FLOW)
    unit.holding[6031] = 3
    unit.holding[6032] = 1
    unit.holding[6033] = 1
    unit.holding[6034] = 5
    unit.holding[6130] = int(ExternalHeaterMode.POST_HEATER)
    unit.holding[6131] = 210  # post-heater set point 21.0 C
    unit.holding[6140] = 1  # RHT sensor mode on
    unit.holding[6141] = 1  # sensitivity
    unit.holding[6150] = 1  # CO2 sensor mode on
    unit.holding[6151] = 400
    unit.holding[6170] = int(SignalOutputFunction.FILTER_WARNING)
    unit.holding[6171] = 1  # CV exhaust connected
    unit.holding[6201] = int(DigitalInputFunction.BYPASS_CONTROL)
    unit.holding[6202] = int(FanFunction.POSITION_SWITCH)
    unit.holding[6240] = 1  # geo exchanger enabled
    unit.holding[6241] = 50  # min geo temperature 5.0 C
    unit.holding[6244] = int(GeoValveOutput.RELAY_OUTPUT_1)
    unit.holding[6900] = int(Language.DUTCH)
    unit.holding[7990] = 2  # external customer interface
    unit.holding[7991] = 21
    unit.holding[7992] = int(ModbusSpeed.BAUD_115200)
    unit.holding[7993] = int(ModbusParity.EVEN)

    device = BrinkFlair(unit)
    await device.async_update()

    settings = device.settings
    assert settings.pwm_inlet_0 == 20
    assert settings.pwm_exhaust_3 == 90
    assert settings.flow_type == FlowType.CONSTANT_FLOW
    assert settings.switch_default_position == 3
    assert settings.display_as_switch is True
    assert settings.imbalance_allowed is True
    assert settings.imbalance_value == 5
    assert settings.external_heater_mode == ExternalHeaterMode.POST_HEATER
    assert settings.postheater_setpoint == 21.0
    assert settings.rht_sensor_mode is True
    assert settings.rht_sensor_sensitivity == 1
    assert settings.co2_sensor_mode is True
    assert settings.co2_1_low_level == 400
    assert settings.signal_output_function == SignalOutputFunction.FILTER_WARNING
    assert settings.cv_connected is True
    assert settings.digital_input_1_function == DigitalInputFunction.BYPASS_CONTROL
    assert settings.digital_input_1_supply_fan == FanFunction.POSITION_SWITCH
    assert settings.geo_exchanger is True
    assert settings.geo_minimum_temperature == 5.0
    assert settings.geo_valve_output == GeoValveOutput.RELAY_OUTPUT_1
    assert settings.language == Language.DUTCH
    assert settings.modbus_interface_type == 2
    assert settings.modbus_slave_address == 21
    assert settings.modbus_speed == ModbusSpeed.BAUD_115200
    assert settings.modbus_parity == ModbusParity.EVEN


async def test_write_standby_through_field(unit: MockModbusUnit) -> None:
    writes = _writes(unit)

    device = BrinkFlair(unit)
    await device.async_update()
    await device.settings.write("standby", StandbyCommand.STANDBY)

    assert any(event.address == 8003 and event.values == [1] for event in writes)


async def test_set_standby_normal_mode(unit: MockModbusUnit) -> None:
    writes = _writes(unit)

    device = BrinkFlair(unit)
    await device.async_set_standby(True)
    assert any(event.address == 8003 and event.values == [1] for event in writes)

    await device.async_set_standby(False)
    assert any(event.address == 8003 and event.values == [2] for event in writes)


async def test_reset_appliance(unit: MockModbusUnit) -> None:
    writes = _writes(unit)

    device = BrinkFlair(unit)
    await device.async_reset_appliance()

    assert any(event.address == 8011 and event.values == [1] for event in writes)


async def test_write_imbalance_allowed_validates(unit: MockModbusUnit) -> None:
    from brink_flair_modbus import BrinkValueValidationError

    device = BrinkFlair(unit)
    await device.async_update()
    try:
        await device.settings.write("imbalance_value", 21)
    except BrinkValueValidationError:
        pass
    else:
        raise AssertionError("write of an out-of-range imbalance should fail")


async def test_write_flow_type_validates(unit: MockModbusUnit) -> None:
    from brink_flair_modbus import BrinkValueValidationError

    device = BrinkFlair(unit)
    await device.async_update()
    try:
        await device.settings.write("flow_type", 99)
    except BrinkValueValidationError:
        pass
    else:
        raise AssertionError("write of an unknown flow type should fail")


async def test_write_control_mode(unit: MockModbusUnit) -> None:
    writes = _writes(unit)

    device = BrinkFlair(unit)
    await device.async_update()
    await device.settings.write("control_mode", ControlMode.FLOW)

    assert any(event.address == 8000 and event.values == [2] for event in writes)
