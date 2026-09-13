# brink-flair-modbus

A Python library for reading and writing **Brink Flair** (and compatible)
ventilation units over Modbus, on top of
[`modbus-connection`](https://pypi.org/project/modbus-connection/).

## Usage

`BrinkFlair` contains the full implementation of the devices capabilities. It uses a `ModbusUnit` for connection with the device.

```python
import asyncio

from modbus_connection import ModbusTcpParams
from modbus_connection._protocol import ModbusUnit, connect

from brink_flair_modbus import BrinkFlair


async def main() -> None:
    unit: ModbusUnit = await connect(ModbusTcpParams(host="192.0.2.10", port=502))
    device = BrinkFlair(unit)

    await device.async_update()
    print(device.info.model)  # "Brink Flair 300"
    print(device.measurements.supply_temperature)
    print(device.flow_limits)  # (FlowLimits(300, 280))

    await unit.close()


asyncio.run(main())
```

## Development

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```console
uv sync --extra dev
uv run ruff check .
uv run mypy brink_flair_modbus
uv run pytest
uv build
```

Type checking (`mypy --strict`) and linting (`ruff`) are enforced in CI.

## License

MIT

## Inspiration taken from

 - https://github.com/fonske/Brink-flair-modbus
 - https://github.com/jarcovlieger/brink-hrv-modbus
