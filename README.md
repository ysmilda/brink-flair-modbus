# brink-flair-modbus

Read and control a Brink Flair heat recovery ventilation unit over Modbus.

The Flair range (200, 225, 300, 325, 350, 400, 450 and 600) speaks Modbus RTU
over RS-485 on its X15 connector. This library takes a
[`modbus-connection`](https://pypi.org/project/modbus-connection/) unit, so it
works through a Modbus TCP gateway as well as a serial adapter. It does not
import Home Assistant; the Home Assistant `brink_flair` integration is built on
it.

```python
from modbus_connection import ModbusTcpParams
from modbus_connection.tmodbus import ModbusConnection
from brink_flair_modbus import FlairDevice, VentilationLevel

connection = ModbusConnection(ModbusTcpParams(host="192.0.2.10", port=502))
device = FlairDevice(connection.for_unit(20))
identity = await device.async_read_identity()
state = await device.async_update()
await device.async_set_level(VentilationLevel.NORMAL)
```

The register map follows Brink's "Modbus UWA2-B/UWA2-E installation
regulations" (document 614882-D) and is checked against a Flair 300.
