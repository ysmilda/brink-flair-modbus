"""Talk to a Brink Flair over Modbus, independent of Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any, Literal, cast

from modbus_connection import IllegalDataAddressError, ModbusUnit

from . import registers as r
from .models import UNKNOWN_MODEL, FlairModel, model_for_appliance_type
from .registers import member_of, signed as _signed
from .settings import FLOW_PRESETS, SETTING_GROUPS, Setting, span

type RegisterKind = Literal["input", "holding"]

_LOGGER = logging.getLogger(__name__)


def _bcd(value: int) -> str:
    """Decode four BCD digits, high nibble first."""
    return "".join(str((value >> shift) & 0xF) for shift in (12, 8, 4, 0))


# Brink reports a temperature sensor that is not fitted as 999.9 degC.
_NOT_FITTED = 9999


def _temperature(value: int) -> float | None:
    """Decode a temperature in tenths of a degree, or None if not fitted."""
    return None if value == _NOT_FITTED else _signed(value) / 10


def _u32(high: int, low: int) -> int:
    """Combine two registers into a 32-bit number, high word first."""
    return (high << 16) | low


@dataclass(frozen=True, kw_only=True)
class FlairIdentity:
    """What a Flair says about itself."""

    serial_number: str
    appliance_type: int
    software_version: str
    hardware_version: str
    model: FlairModel | None
    """None when the appliance type is not in the model table."""

    @property
    def model_name(self) -> str:
        """The model name, or a generic name for an unknown type."""
        return (self.model or UNKNOWN_MODEL).name


@dataclass(frozen=True, kw_only=True)
class FlairState:
    """One poll of a Flair's readings and settings."""

    active_function: int
    fan_control_type: int
    ventilation_mode: int
    switch_position: int
    control_mode: int
    control_level: int
    control_flow: int
    standby: bool

    supply_fan_status: int
    supply_flow_setpoint: int
    supply_flow: int
    supply_fan_speed: int
    supply_temperature: float | None
    supply_humidity: float
    supply_pressure: float

    exhaust_fan_status: int
    exhaust_flow_setpoint: int
    exhaust_flow: int
    exhaust_fan_speed: int
    exhaust_temperature: float | None
    exhaust_humidity: float
    exhaust_pressure: float

    bypass_status: int
    frost_status: int
    frost_heater_power: int
    ntc1_temperature: float | None
    ntc2_temperature: float | None

    filter_dirty: bool
    filter_hours: int | None
    """None when the unit does not report it."""
    filter_interval_days: int
    operating_hours: int | None
    """None when the unit does not report it."""

    flow_presets: tuple[int, int, int, int]
    bypass_mode: int
    bypass_temp_indoor: float
    bypass_temp_outdoor: float
    bypass_hysteresis: float

    rht_humidity: float | None = None
    """Meaningful only when a humidity sensor is fitted."""
    preheater_status: int | None = None
    preheater_capacity: int | None = None
    co2: dict[int, int] = field(default_factory=dict)
    """CO2 level in ppm by sensor number (1 to 4), for running sensors."""

    # Installer settings that not every firmware serves; None when missing.
    imbalance_allowed: bool | None = None
    supply_imbalance: int | None = None
    """Supply airflow offset in %."""
    exhaust_imbalance: int | None = None
    """Exhaust airflow offset in %."""
    geo_heat_exchanger: bool | None = None
    geo_min_temp: float | None = None
    geo_max_temp: float | None = None

    def value_of[V](self, setting: Setting[V]) -> V | None:
        """Return the value this poll holds for a setting, or None if not served."""
        return cast("V | None", getattr(self, setting.field))

    @property
    def requested_level(self) -> r.VentilationLevel | None:
        """The level Modbus set, or None for a set airflow or the unit's own control."""
        if self.control_mode != r.ControlMode.SWITCH:
            return None
        return member_of(r.VentilationLevel, self.control_level)

    @property
    def target_flow(self) -> int:
        """The supply airflow the unit is heading for, in m3/h.

        While Modbus sets the ventilation, this is what was asked for: the
        unit's own setpoint (4031) lags behind a change by several seconds.
        """
        if self.control_mode == r.ControlMode.FLOW:
            return self.control_flow
        if (level := self.requested_level) is not None:
            return self.flow_presets[level]
        return self.supply_flow_setpoint

    @property
    def bypass_state(self) -> r.BypassState:
        """The bypass position, simplified to open, closed or initializing."""
        return r.BYPASS_STATUS_MAP.get(self.bypass_status, r.BypassState.INITIALIZING)

    @property
    def has_error(self) -> bool:
        """Whether the unit reports a fault."""
        return (
            self.active_function
            in (r.ActiveFunction.NON_BLOCKING_ERROR, r.ActiveFunction.BLOCKING_ERROR)
            or self.fan_control_type == r.FanControlType.ERROR
            or r.FanStatus.ERROR in (self.supply_fan_status, self.exhaust_fan_status)
            or self.frost_status == r.FrostStatus.ERROR
            or self.bypass_state == r.BypassState.ERROR
        )

    @property
    def preheater_active(self) -> bool | None:
        """Whether the preheater is running, or None when the unit does not report it."""
        if self.preheater_status is None:
            return None
        return self.preheater_status == 2

    @property
    def frost_protection_active(self) -> bool:
        """Whether frost protection is acting on the airflow or the heater."""
        return self.frost_status in r.FROST_ACTIVE_STATES

    @property
    def filter_days_remaining(self) -> int | None:
        """Days until the filter warning, never below zero."""
        if self.filter_hours is None:
            return None
        return max(0, self.filter_interval_days - self.filter_hours // 24)

    def flow_preset_bounds(
        self, level: r.VentilationLevel, max_flow: int
    ) -> tuple[int, int]:
        """Return the lowest and highest airflow a level may take, keeping levels in order."""
        lower = self.flow_presets[level - 1] if level > r.VentilationLevel.AWAY else 0
        upper = (
            self.flow_presets[level + 1]
            if level < r.VentilationLevel.HIGH
            else max_flow
        )
        return lower, upper


class FlairDevice:
    """A Brink Flair reached through a Modbus unit."""

    def __init__(self, unit: ModbusUnit) -> None:
        """Wrap a Modbus unit."""
        self._unit = unit
        self.identity: FlairIdentity | None = None
        # What Home Assistant last asked for: a control mode and its value,
        # a level in switch mode or m3/h in flow mode.
        self._requested: tuple[r.ControlMode, int] | None = None
        self._unsupported: set[tuple[str, int]] = set()

    @property
    def unsupported_registers(self) -> list[str]:
        """Optional registers this unit refused, such as "holding 6240"."""
        return sorted(f"{kind} {address}" for kind, address in self._unsupported)

    @property
    def model(self) -> FlairModel:
        """The model, or a generic one before identification or when unknown."""
        if self.identity is None or self.identity.model is None:
            return UNKNOWN_MODEL
        return self.identity.model

    async def _read(self, kind: RegisterKind, address: int, count: int) -> list[int]:
        if kind == "input":
            return await self._unit.read_input_registers(address, count)
        return await self._unit.read_holding_registers(address, count)

    async def _read_optional(
        self, kind: RegisterKind, address: int, count: int
    ) -> list[int] | None:
        """Read registers that not every unit or firmware serves."""
        if (kind, address) in self._unsupported:
            return None
        try:
            return await self._read(kind, address, count)
        except IllegalDataAddressError:
            _LOGGER.debug("%s register %s is not served by this unit", kind, address)
            self._unsupported.add((kind, address))
            return None

    async def async_read_identity(self) -> FlairIdentity:
        """Read the serial number, versions and appliance type."""
        # 4006 to 4009 are not served, so these are two reads.
        versions = await self._read("input", r.IR_SOFTWARE_VERSION, 5)
        serial_regs = await self._read("input", r.IR_SERIAL_NUMBER, 3)
        sw_type_major, sw_minor_fix, sw_build, hardware, appliance_type = versions
        serial = "".join(_bcd(value) for value in serial_regs)
        software = (
            f"{sw_type_major & 0xFF}.{sw_minor_fix >> 8}.{sw_minor_fix & 0xFF}"
            f".{sw_build}"
        )
        self.identity = FlairIdentity(
            serial_number=serial,
            appliance_type=appliance_type,
            software_version=software,
            hardware_version=f"{hardware >> 8}.{hardware & 0xFF}",
            model=model_for_appliance_type(appliance_type),
        )
        return self.identity

    async def async_update(self) -> FlairState:
        """Read all readings and settings."""
        status = await self._read("input", r.IR_ACTIVE_FUNCTION, 5)
        supply = await self._read("input", r.IR_SUPPLY_FAN_STATUS, 8)
        exhaust = await self._read("input", r.IR_EXHAUST_FAN_STATUS, 8)
        (bypass_status,) = await self._read("input", r.IR_BYPASS_STATUS, 1)
        frost = await self._read("input", r.IR_FROST_STATUS, 2)
        # The wall switch position, then the NTC1, NTC2 and RHT sensors.
        switch_and_sensors = await self._read("input", r.IR_SWITCH_POSITION, 4)
        (filter_status,) = await self._read("input", r.IR_FILTER_STATUS, 1)
        operating = await self._read_optional("input", r.IR_OPERATING_HOURS, 2)
        filter_hours = await self._read_optional("input", r.IR_FILTER_HOURS, 1)
        control = await self._read("holding", r.RC_CONTROL, 4)
        settings = await self._read_settings()

        control_mode = control[0]
        if self._requested is None:
            # Pick up a level or flow set before Home Assistant restarted.
            if (
                control_mode == r.ControlMode.SWITCH
                and member_of(r.VentilationLevel, control[1]) is not None
            ):
                self._requested = (r.ControlMode.SWITCH, control[1])
            elif control_mode == r.ControlMode.FLOW:
                self._requested = (r.ControlMode.FLOW, control[2])
        if self._requested is not None and control_mode == r.ControlMode.OFF:
            # The remote control registers reset after a power cut.
            _LOGGER.info("Modbus control was reset, sending the last setting again")
            await self._apply_control(*self._requested)
            control = await self._read("holding", r.RC_CONTROL, 4)
            control_mode = control[0]

        state = FlairState(
            active_function=status[0],
            fan_control_type=status[1],
            ventilation_mode=status[2],
            switch_position=switch_and_sensors[0],
            control_mode=control_mode,
            control_level=control[1],
            control_flow=control[2],
            standby=control[3] == 1,
            supply_pressure=_signed(status[3]) / 10,
            exhaust_pressure=_signed(status[4]) / 10,
            supply_fan_status=supply[0],
            supply_flow_setpoint=supply[1],
            supply_flow=supply[2],
            supply_fan_speed=supply[4],
            supply_temperature=_temperature(supply[6]),
            supply_humidity=supply[7],
            exhaust_fan_status=exhaust[0],
            exhaust_flow_setpoint=exhaust[1],
            exhaust_flow=exhaust[2],
            exhaust_fan_speed=exhaust[4],
            exhaust_temperature=_temperature(exhaust[6]),
            exhaust_humidity=exhaust[7],
            bypass_status=bypass_status,
            frost_status=frost[0],
            frost_heater_power=frost[1],
            ntc1_temperature=_temperature(switch_and_sensors[1]),
            ntc2_temperature=_temperature(switch_and_sensors[2]),
            filter_dirty=filter_status == 1,
            operating_hours=_u32(*operating) if operating else None,
            filter_hours=filter_hours[0] if filter_hours else None,
            rht_humidity=switch_and_sensors[3],
            **await self._read_optional_parts(),
            **settings,
        )
        return state

    async def _read_settings(self) -> dict[str, Any]:
        """Read the settings table, one run of registers at a time."""
        values: dict[str, Any] = {}
        for group in SETTING_GROUPS:
            start, count = span(group)
            if group[0].optional:
                registers = await self._read_optional("holding", start, count)
            else:
                registers = await self._read("holding", start, count)
            if registers is None:
                continue
            for setting in group:
                offset = setting.address - start
                values[setting.field] = setting.decode(
                    registers[offset : offset + setting.count]
                )
        return values

    async def _read_optional_parts(self) -> dict[str, Any]:
        """Read the registers of optional parts, where served."""
        values: dict[str, Any] = {}
        if heater := await self._read_optional("input", r.IR_PREHEATER_STATUS, 2):
            values["preheater_status"] = heater[0]
            values["preheater_capacity"] = heater[1]
        if co2 := await self._read_optional("input", r.IR_CO2_SENSORS, 8):
            # Only a running sensor has a valid reading. An absent sensor
            # reports an error status.
            values["co2"] = {
                number + 1: co2[number * 2 + 1]
                for number in range(4)
                if co2[number * 2] == r.CO2SensorStatus.RUNNING
            }
        return values

    async def _write(self, address: int, value: int) -> None:
        await self._unit.write_register(address, value)

    async def async_set_setting[V](self, setting: Setting[V], value: V) -> None:
        """Write a setting."""
        if setting.encode is None:
            msg = f"{setting.field} is written with a method of its own"
            raise TypeError(msg)
        await self._write(setting.address, setting.encode(value))

    async def async_set_flow_preset(self, level: r.VentilationLevel, flow: int) -> None:
        """Set the airflow behind a ventilation level, in m3/h."""
        await self._write(FLOW_PRESETS.address + level, flow)

    async def async_set_standby(self, standby: bool) -> None:
        """Put the unit in standby, or wake it."""
        await self._write(r.RC_STANDBY, 1 if standby else 2)

    async def async_reset_filter(self) -> None:
        """Reset the filter counter after a filter change."""
        await self._write(r.RC_FILTER_RESET, 1)

    async def _apply_control(self, mode: r.ControlMode, value: int) -> None:
        # A Flair 300 rejects a write of 8000 that does not change it
        # (Illegal Data Value), so only switch it when it is not set yet.
        (control_mode,) = await self._read("holding", r.RC_CONTROL, 1)
        if control_mode != mode:
            await self._write(r.RC_CONTROL, mode)
        address = (
            r.RC_SWITCH_POSITION if mode == r.ControlMode.SWITCH else r.RC_FLOW_RATE
        )
        await self._write(address, value)

    async def async_set_level(self, level: r.VentilationLevel) -> None:
        """Take over control and set the ventilation level."""
        await self._apply_control(r.ControlMode.SWITCH, level)
        self._requested = (r.ControlMode.SWITCH, level)

    async def async_set_flow(self, flow: int) -> None:
        """Take over control and set the airflow in m3/h, within the model's range."""
        model = self.model
        flow = min(model.max_flow, max(model.min_flow, flow))
        await self._apply_control(r.ControlMode.FLOW, flow)
        self._requested = (r.ControlMode.FLOW, flow)
