"""Tests for register writes and the write validators."""

from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusUnit, WriteEvent

from brink_flair_modbus import (
    BrinkFlair,
    BrinkValueValidationError,
    BypassMode,
    BypassOverrideBlockedError,
    StandbyCommand,
    VentilationLevel,
)


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


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(0, False), (int(StandbyCommand.STANDBY), True)],
)
async def test_standby_reads_back(
    unit: MockModbusUnit, raw: int, expected: bool
) -> None:
    unit.holding[8003] = raw

    device = BrinkFlair(unit)
    await device.async_update()

    assert device.standby is expected


async def test_bypass_open_blocked_at_high_supply(unit: MockModbusUnit) -> None:
    unit.input[4032] = 250  # supply volume
    writes = _writes(unit)

    device = BrinkFlair(unit)
    await device.async_update()
    with pytest.raises(BypassOverrideBlockedError) as err:
        await device.async_set_bypass_mode(BypassMode.OPEN)

    assert err.value.supply_volume == 250
    assert not any(event.address == 6100 for event in writes)


@pytest.mark.parametrize(
    ("supply", "mode"),
    [(150, BypassMode.OPEN), (250, BypassMode.AUTO), (250, BypassMode.CLOSED)],
)
async def test_bypass_mode_written(
    unit: MockModbusUnit, supply: int, mode: BypassMode
) -> None:
    unit.input[4032] = supply
    writes = _writes(unit)

    device = BrinkFlair(unit)
    await device.async_update()
    await device.async_set_bypass_mode(mode)

    assert any(
        event.address == 6100 and event.values == [int(mode)] for event in writes
    )
