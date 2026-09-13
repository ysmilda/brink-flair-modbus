"""Tests for register writes and the write validators."""

from __future__ import annotations

from modbus_connection.mock import MockModbusUnit, WriteEvent

from brink_flair_modbus import BrinkFlair, BrinkValueValidationError, VentilationLevel


def _writes(unit: MockModbusUnit) -> list[WriteEvent]:
    captured: list[WriteEvent] = []
    unit.on_write(captured.append)
    return captured


async def test_write_level(unit: MockModbusUnit) -> None:
    unit.holding[8001] = int(VentilationLevel.MEDIUM)
    writes = _writes(unit)

    device = BrinkFlair(unit)
    await device.async_update()
    await device.settings.write("level", VentilationLevel.HIGH)

    assert any(event.address == 8001 and event.values == [3] for event in writes)


async def test_write_control_mode_validates(unit: MockModbusUnit) -> None:
    device = BrinkFlair(unit)
    await device.async_update()
    try:
        await device.settings.write("control_mode", 99)
    except BrinkValueValidationError:
        pass
    else:
        raise AssertionError("write of unknown control-mode value should fail")


async def test_write_number_out_of_range(unit: MockModbusUnit) -> None:
    device = BrinkFlair(unit)
    await device.async_update()
    try:
        await device.settings.write("flow_0", -10)
    except BrinkValueValidationError:
        pass
    else:
        raise AssertionError("write of a negative flow should fail")


async def test_reset_filter_pulses_registers(unit: MockModbusUnit) -> None:
    writes = _writes(unit)

    device = BrinkFlair(unit)
    await device.async_reset_filter(delay=0)

    touches = [(event.address, event.values) for event in writes]
    assert (8010, [1]) in touches
    assert (8010, [0]) in touches


async def test_set_standby(unit: MockModbusUnit) -> None:
    writes = _writes(unit)

    device = BrinkFlair(unit)
    await device.async_set_standby(True)

    assert any(event.address == 8003 and event.values == [1] for event in writes)
