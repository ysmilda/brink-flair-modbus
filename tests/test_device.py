"""Tests for reading and writing a Flair."""

from modbus_connection import IllegalDataAddressError
from modbus_connection.mock import MockModbusUnit
import pytest

from flair_modbus import (
    BYPASS_TEMP_INDOOR,
    FLOW_PRESETS,
    UNKNOWN_MODEL,
    BypassState,
    ControlMode,
    FlairDevice,
    VentilationLevel,
    member_of,
)
from flair_modbus.device import _bcd, _temperature, _u32
from flair_modbus.models import FLAIR_300
from flair_modbus.registers import signed

from .conftest import SERIAL


def test_decoding() -> None:
    """Register values decode as Brink documents them."""
    assert signed(0xFF9C) == -100
    assert signed(215) == 215
    assert _bcd(0x4290) == "4290"
    assert _u32(1, 2) == 65538


def test_temperature_not_fitted() -> None:
    """A sensor that is not fitted reads 9999 and decodes as None."""
    assert _temperature(9999) is None
    assert _temperature(125) == 12.5
    assert _temperature(0xFFE2) == -3.0


def test_member_of() -> None:
    """A register value outside an enum maps to None."""
    assert member_of(VentilationLevel, 2) is VentilationLevel.NORMAL
    assert member_of(VentilationLevel, 9) is None


async def test_identity(unit: MockModbusUnit) -> None:
    """The identity decodes the serial number, versions and model."""
    device = FlairDevice(unit)
    assert device.model is UNKNOWN_MODEL
    identity = await device.async_read_identity()
    assert identity.serial_number == SERIAL
    assert identity.software_version == "3.1.10.3"
    assert identity.hardware_version == "2.1"
    assert identity.model is FLAIR_300
    assert device.model is FLAIR_300


async def test_unknown_model(unit: MockModbusUnit) -> None:
    """An appliance type outside the model table uses generic limits."""
    unit.input[4000] = [0x5303, 0x010A, 3, 0x0201, 7, 63]
    device = FlairDevice(unit)
    identity = await device.async_read_identity()
    assert identity.model is None
    assert identity.model_name == UNKNOWN_MODEL.name
    assert device.model is UNKNOWN_MODEL


async def test_state(unit: MockModbusUnit) -> None:
    """A poll decodes readings and the settings table."""
    state = await FlairDevice(unit).async_update()
    assert state.requested_level is VentilationLevel.NORMAL
    assert state.target_flow == 200
    assert state.flow_presets == (50, 140, 200, 250)
    assert state.value_of(BYPASS_TEMP_INDOOR) == 24.0
    assert state.bypass_state is BypassState.OPEN
    assert state.filter_days_remaining == 42
    assert state.flow_preset_bounds(VentilationLevel.NORMAL, 300) == (140, 250)
    assert state.flow_preset_bounds(VentilationLevel.HIGH, 300) == (200, 300)


async def test_set_level_and_flow(unit: MockModbusUnit) -> None:
    """Setting a level or a flow takes over control, within the model's range."""
    device = FlairDevice(unit)
    await device.async_read_identity()
    await device.async_set_flow(1000)
    assert unit.holding[8000] == ControlMode.FLOW
    assert unit.holding[8002] == 300
    state = await device.async_update()
    assert state.target_flow == 300
    assert state.requested_level is None

    await device.async_set_level(VentilationLevel.HIGH)
    assert unit.holding[8000] == ControlMode.SWITCH
    assert unit.holding[8001] == VentilationLevel.HIGH


async def test_control_restored_after_reset(unit: MockModbusUnit) -> None:
    """When the unit forgets Modbus control, the last request is sent again."""
    device = FlairDevice(unit)
    await device.async_set_level(VentilationLevel.LOW)
    unit.holding[8000] = [0, 0, 0, 0]
    state = await device.async_update()
    assert state.control_mode == ControlMode.SWITCH
    assert state.requested_level is VentilationLevel.LOW


async def test_settings_writes(unit: MockModbusUnit) -> None:
    """Settings encode into their registers; flow presets have their own write."""
    device = FlairDevice(unit)
    await device.async_set_setting(BYPASS_TEMP_INDOOR, 22.5)
    assert unit.holding[6101] == 225
    with pytest.raises(TypeError):
        await device.async_set_setting(FLOW_PRESETS, (50, 100, 150, 200))
    await device.async_set_flow_preset(VentilationLevel.HIGH, 260)
    assert unit.holding[6003] == 260
    await device.async_set_standby(True)
    assert unit.holding[8003] == 1
    await device.async_reset_filter()
    assert unit.holding[8010] == 1


async def test_refused_register_is_not_read_again(unit: MockModbusUnit) -> None:
    """An optional register the unit refuses is skipped from then on."""
    unit.fail_read(4060, IllegalDataAddressError(), register_type="input")
    device = FlairDevice(unit)
    state = await device.async_update()
    assert state.preheater_active is None
    assert device.unsupported_registers == ["input 4060"]

    unit.input[4060] = [2, 40]
    assert (await device.async_update()).preheater_active is None


async def test_fault_sources(unit: MockModbusUnit) -> None:
    """A fan control error or a bypass error counts as a fault."""
    device = FlairDevice(unit)
    assert not (await device.async_update()).has_error

    unit.input[4020] = [12, 4, 2, 37, 42]
    assert (await device.async_update()).has_error

    unit.input[4020] = [12, 1, 2, 37, 42]
    unit.input[4050] = [255, 920]
    state = await device.async_update()
    assert state.bypass_state == BypassState.ERROR
    assert state.has_error
