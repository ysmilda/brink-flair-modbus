"""Fixtures for the flair_modbus tests."""

from typing import Any

from modbus_connection import IllegalDataAddressError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit
import pytest

SERIAL = "429000220102"


def _bcd(digits: str) -> int:
    return int(digits, 16)


# Input registers a real Flair 300 refuses with IllegalDataAddress, so a read
# that spans one of them fails as it would on the unit.
UNSERVED_INPUT_REGISTERS = (*range(4006, 4010), *range(4102, 4110))


def refuse_unserved_registers(unit: MockModbusUnit) -> None:
    """Make the mock refuse the registers a real Flair 300 refuses."""
    for address in UNSERVED_INPUT_REGISTERS:
        unit.fail_read(address, IllegalDataAddressError(), register_type="input")


def flair_300_registers() -> tuple[dict[int, Any], dict[int, Any]]:
    """Input and holding registers of a Flair 300.

    Values come from a real Flair 300 (appliance type 24), with the serial
    number replaced, the level set to normal and the bypass open.
    """
    inputs = {
        4000: [0x5303, 0x010A, 3, 0x0201, 24, 63],
        4010: [_bcd(SERIAL[0:4]), _bcd(SERIAL[4:8]), _bcd(SERIAL[8:12])],
        4020: [12, 0, 2, 37, 42],
        4030: [4, 140, 148, 0, 1320, 0, 191, 43],
        4040: [4, 137, 151, 0, 1380, 0, 133, 94],
        4050: [1, 920],
        4060: [0, 0],
        4070: [2, 0, 100],
        4080: [2, 125, 9999, 0],
        4100: 0,
        4113: [0, 1234, 48 * 24],
        4200: [0] * 8,
    }
    holding = {
        6000: [50, 140, 200, 250],
        6033: 1,
        6035: [0, 0],
        6100: [0, 240, 150, 20],
        6120: 90,
        6130: 0,
        6140: 0,
        6150: 0,
        6240: [0, 50, 250],
        8000: [1, 2, 0, 0],
    }
    return inputs, holding


@pytest.fixture
def unit() -> MockModbusUnit:
    """A Modbus unit that answers like a Flair 300."""
    unit = MockModbusConnection().for_unit(20)
    unit.input, unit.holding = flair_300_registers()
    refuse_unserved_registers(unit)
    return unit
