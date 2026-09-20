"""Exercise ``BrinkFlair`` against a real unit through the serial-proxy bridge.

Starts the PTY bridge (``serial_proxy_bridge``), points ``connect_serial`` at
its slave end, and runs the library's full reads against the ventilation unit
over the ESPHome serial proxy:

    uv run --extra dev python scripts/serial_proxy_test.py \\
        --host brink-flair-300.local \\
        --encryption-key nQkUeYz... \\
        --baudrate 19200 --parity E

``--instance`` is the zero-based index of the proxy entry in the device's
``serial_proxy:`` list; ``--unit-id`` is the Modbus slave address of the
ventilation unit (20 for the author's Brink Flair).
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
from typing import Any

import aioesphomeapi
from modbus_connection.tmodbus import connect_serial
from serial_proxy_bridge import PtyBridge, _parity

from brink_flair_modbus import BrinkFlair

_BAUD_OPTIONS = (1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="serial_proxy_test",
        description="Run BrinkFlair against a real unit through the serial-proxy bridge.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host", required=True, help="ESPHome device host name or IP address"
    )
    parser.add_argument(
        "--port", type=int, default=6053, help="ESPHome native API port"
    )
    parser.add_argument(
        "--encryption-key",
        help="base64 encryption key, when the api component uses encryption",
    )
    parser.add_argument("--password", help="legacy API password, when used")
    parser.add_argument(
        "--instance",
        type=int,
        default=0,
        help=("zero-based index of the proxy entry in the device's serial_proxy: list"),
    )
    parser.add_argument(
        "--unit-id",
        type=int,
        default=20,
        help="Modbus slave address of the ventilation unit",
    )
    parser.add_argument(
        "--baudrate", type=int, choices=_BAUD_OPTIONS, default=19200, help="bus speed"
    )
    parser.add_argument(
        "--parity", choices=("N", "E", "O"), default="E", help="line parity"
    )
    parser.add_argument(
        "--stop-bits", type=int, choices=(1, 2), default=1, help="stop bits per byte"
    )
    parser.add_argument(
        "--data-size", type=int, choices=(5, 6, 7, 8), default=8, help="data bits"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="how long to wait for a Modbus reply, in seconds",
    )
    parser.add_argument(
        "--message-spacing",
        type=float,
        default=0.0,
        help="minimum gap between requests, in seconds",
    )
    parser.add_argument(
        "--model-override",
        type=int,
        help="pin a model when the reported device type is unknown",
    )
    return parser


def _dump_component(title: str, component: Any) -> None:
    """Print every declared field of a component and its current value."""
    print(f"{title}:")
    for name in component.declared_fields:
        value = getattr(component, name)
        print(f"  {name}: {value}")


async def _run(args: argparse.Namespace) -> int:
    api = aioesphomeapi.APIClient(
        args.host,
        args.port,
        password=args.password,
        noise_psk=args.encryption_key,
        client_info="brink-flair-modbus/serial-proxy-test",
    )
    bridge: PtyBridge | None = None
    try:
        await api.connect(login=True)
        bridge = PtyBridge(api, args.instance)
        await bridge.start()
        with contextlib.suppress(Exception):
            await api.serial_proxy_configure_await_response(
                args.instance,
                args.baudrate,
                parity=_parity(args.parity),
                stop_bits=args.stop_bits,
                data_size=args.data_size,
            )
    except aioesphomeapi.APIConnectionError as err:
        print(f"could not reach {args.host}: {err}")
        return 1

    connection = None
    try:
        assert bridge is not None
        connection = await connect_serial(
            bridge.slave_path,
            baudrate=args.baudrate,
            bytesize=args.data_size,
            parity=args.parity,
            stopbits=args.stop_bits,
            timeout=args.timeout,
            framer="rtu",
            message_spacing=args.message_spacing,
        )
        unit = connection.for_unit(args.unit_id)

        probe = await BrinkFlair.async_probe(unit)
        print(f"probe: device type {probe.device_type} -> {probe.model_name}")

        device = BrinkFlair(unit, model_override=args.model_override)
        await device.async_update()
        await device.async_recheck_extension()

        print()
        _dump_component("Device information", device.info)
        print()
        _dump_component("Measurements", device.measurements)
        print()
        _dump_component("Status", device.status)
        print()
        _dump_component("Settings", device.settings)
        print()
        if device.extension_available:
            _dump_component("Extension module", device.extension)
        else:
            print("Extension module: not available (registers not served)")
        print()
        print(
            f"filter used: {device.measurements.filter_used_days} days, "
            f"exchange in: {device.exchange_filter_in} days"
        )
        return 0
    finally:
        if connection is not None:
            with contextlib.suppress(Exception):
                await connection.disconnect()
        if bridge is not None:
            with contextlib.suppress(Exception):
                await bridge.close()
        with contextlib.suppress(Exception):
            await api.disconnect()


def main() -> None:
    """Parse arguments and test the library through the proxy bridge."""
    args = _build_parser().parse_args()
    try:
        status = asyncio.run(_run(args))
    except KeyboardInterrupt:
        status = 130
    raise SystemExit(status)


if __name__ == "__main__":
    main()
