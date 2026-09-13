from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from modbus_connection.mock import MockModbusConnection, MockModbusUnit


@pytest_asyncio.fixture
async def unit() -> AsyncGenerator[MockModbusUnit, None]:
    """Return a fresh interactive mock Modbus unit for a single test."""
    connection = MockModbusConnection()
    mock = connection.for_unit(1)
    yield mock
    await connection.disconnect()
