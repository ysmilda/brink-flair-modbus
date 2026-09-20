"""Tests for ``BrinkFlair.async_probe`` and the device object."""

from __future__ import annotations

from modbus_connection import ModbusError
from modbus_connection.mock import MockModbusUnit

from brink_flair_modbus import BrinkFlair, BrinkProbe, FlowLimits


async def test_probe_known_device_type(unit: MockModbusUnit) -> None:
    unit.input[4004] = 24
    assert await BrinkFlair.async_probe(unit) == BrinkProbe(device_type=24)


async def test_probe_unmapped_device_type(unit: MockModbusUnit) -> None:
    unit.input[4004] = 321
    assert await BrinkFlair.async_probe(unit) == BrinkProbe(device_type=321)


async def test_probe_read_failure_returns_none(unit: MockModbusUnit) -> None:
    unit.fail_read(4004, ModbusError("no such register"), register_type="input")
    assert await BrinkFlair.async_probe(unit) == BrinkProbe(device_type=None)


async def test_update_reads_subsystems(unit: MockModbusUnit) -> None:
    unit.input[4004] = 24
    unit.input[4036] = 250  # supply temperature, raw value x10
    unit.input[4037] = 50  # supply relative humidity
    unit.input[4115] = 48  # filter used hours
    unit.holding[6120] = 200  # filter change days

    device = BrinkFlair(unit)
    await device.async_update()

    assert device.info.model == "Brink Flair 300"
    assert device.info.device_type == 24
    assert device.measurements.supply_temperature == 25.0
    assert device.measurements.supply_relative_humidity == 50
    assert device.flow_limits == FlowLimits(300, 280)
    assert device.measurements.filter_used_days == 2.0
    assert device.exchange_filter_in == 198.0


async def test_model_override(unit: MockModbusUnit) -> None:
    device = BrinkFlair(unit, model_override=600)
    await device.async_update()
    assert device.info.model == "Brink Flair 600"
    assert device.flow_limits == FlowLimits(600, 600)


async def test_unknown_device_type_falls_back_to_default(unit: MockModbusUnit) -> None:
    unit.input[4004] = 321
    device = BrinkFlair(unit)
    await device.async_update()
    assert device.info.model == "Brink Flair 300"
    assert device.flow_limits == FlowLimits(300, 280)
