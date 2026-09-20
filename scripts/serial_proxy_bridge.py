"""Bridging serial-proxy bytes onto a local pseudo-terminal.

modbus-connection's serial transport talks to a local terminal device, so this
tool creates a pseudo-terminal (PTY), subscribes one ESPHome serial-proxy
instance to its master end, and shuttles bytes in both directions. A Modbus
client (the ``brink_flair_modbus`` library on ``connect_serial``) opens the
slave side and reaches the ventilation unit with the library's full stack
(tmodbus framing, CRC, pacing, error mapping) intact, while the ESPHome device
does the actual RS485 signalling.

The local PTY path is announced through the logger so a wrapper can learn it::

    uv run --extra dev python scripts/serial_proxy_bridge.py \\
        --host brink-flair-300.local \\
        --encryption-key nQkUeYz... \\
        --baudrate 19200 --parity E
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import pty
import tty
from collections.abc import Callable

import aioesphomeapi

_LOGGER = logging.getLogger(__name__)


def _parity(value: str) -> aioesphomeapi.SerialProxyParity:
    """Map a CLI parity letter to the ESPHome API enum."""
    return aioesphomeapi.SerialProxyParity["NONE" if value == "N" else value]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="serial_proxy_bridge",
        description=(
            "Expose one ESPHome serial-proxy instance as a local PTY, so a "
            "Modbus client can talk to the unit over the network."
        ),
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
    parser.add_argument("--baudrate", type=int, default=19200, help="bus speed in baud")
    parser.add_argument(
        "--parity", choices=("N", "E", "O"), default="E", help="line parity"
    )
    parser.add_argument(
        "--stop-bits", type=int, choices=(1, 2), default=1, help="stop bits per byte"
    )
    parser.add_argument(
        "--data-size",
        type=int,
        choices=(5, 6, 7, 8),
        default=8,
        help="data bits per byte",
    )
    return parser


class PtyBridge:
    """Shuttle bytes between a local PTY and one ESPHome serial-proxy."""

    def __init__(self, api: aioesphomeapi.APIClient, instance: int) -> None:
        self._api = api
        self._instance = instance
        self._loop = asyncio.get_running_loop()
        self._master_fd, self._slave_fd = pty.openpty()
        for fd, name in ((self._master_fd, "master"), (self._slave_fd, "slave")):
            tty.setraw(fd)
            os.set_blocking(fd, False)
        self._slave_path = os.ttyname(self._slave_fd)
        self._master_pending = bytearray()
        self._master_writable = False
        self._unsubscribe: Callable[[], None] | None = None

    @property
    def slave_path(self) -> str:
        """The terminal device the library should open."""
        return self._slave_path

    async def start(self) -> None:
        """Subscribe to the proxy and configure the UART over the API."""
        self._unsubscribe = self._api.subscribe_serial_proxy_data(self._on_proxy_data)
        try:
            await self._api.serial_proxy_subscribe_await_response(self._instance)
        except aioesphomeapi.APIConnectionError as err:
            raise RuntimeError(
                f"instance {self._instance} has no serial proxy: {err}"
            ) from err
        self._loop.add_reader(self._master_fd, self._drain_master)

    def _on_proxy_data(self, message: aioesphomeapi.SerialProxyDataReceived) -> None:
        """Queue the device's reply bytes for the library to read."""
        if message.instance != self._instance:
            return
        self._master_pending.extend(message.data)
        self._flush_master_pending()

    def _flush_master_pending(self) -> None:
        """Write the device's bytes into the PTY the library reads."""
        if not self._master_pending:
            return
        try:
            written = os.write(self._master_fd, self._master_pending)
        except BlockingIOError:
            written = 0
        del self._master_pending[:written]
        if self._master_pending and not self._master_writable:
            self._loop.add_writer(self._master_fd, self._flush_master_pending)
            self._master_writable = True
        if not self._master_pending and self._master_writable:
            self._loop.remove_writer(self._master_fd)
            self._master_writable = False

    def _drain_master(self) -> None:
        """Forward the library's request bytes to the serial proxy."""
        try:
            chunk = os.read(self._master_fd, 4096)
        except BlockingIOError:
            return
        if chunk:
            try:
                self._api.serial_proxy_write(self._instance, chunk)
            except aioesphomeapi.APIConnectionError as err:
                _LOGGER.error("could not write to the serial proxy: %s", err)

    async def close(self) -> None:
        """Drop the proxy subscription and close the PTY pair."""
        self._loop.remove_reader(self._master_fd)
        if self._master_writable:
            self._loop.remove_writer(self._master_fd)
        if self._unsubscribe is not None:
            self._unsubscribe()
        os.close(self._master_fd)
        os.close(self._slave_fd)


async def _run(args: argparse.Namespace) -> None:
    api = aioesphomeapi.APIClient(
        args.host,
        args.port,
        password=args.password,
        noise_psk=args.encryption_key,
        client_info="brink-flair-modbus/serial-proxy-bridge",
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
        _LOGGER.info(
            "bridged PTY %s <-> serial proxy instance %s",
            bridge.slave_path,
            args.instance,
        )
        while True:
            await asyncio.sleep(3600)
    finally:
        if bridge is not None:
            with contextlib.suppress(Exception):
                await bridge.close()
        with contextlib.suppress(Exception):
            await api.disconnect()


def main() -> None:
    """Run the byte bridge until interrupted."""
    args = _build_parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == "__main__":
    main()
