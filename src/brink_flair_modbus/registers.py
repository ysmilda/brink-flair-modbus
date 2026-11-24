"""Brink Flair Modbus register map.

Taken from Brink's "Modbus UWA2-B/UWA2-E installation regulations" (document
614882-D). Addresses are the "Modbus address" values the document lists, which
go on the wire as they are (confirmed on a Flair 300).
"""

from enum import IntEnum


def signed(value: int) -> int:
    """Interpret a 16-bit register as a signed number."""
    return value - 0x10000 if value & 0x8000 else value


def member_of[E: IntEnum](enum: type[E], value: int) -> E | None:
    """Return the enum member a register value stands for, or None if it is none."""
    try:
        return enum(value)
    except ValueError:
        return None


# Factory serial settings (installer menu step 14).
DEFAULT_UNIT_ID = 20
DEFAULT_BAUDRATE = 19200
DEFAULT_STOPBITS = 1

# --- Input registers (function 0x04) -----------------------------------------
IR_SOFTWARE_VERSION = 4000  # 3 registers: type/major, minor/fix, build
IR_HARDWARE_VERSION = 4003  # high byte major, low byte minor
IR_APPLIANCE_TYPE = 4004
IR_DIPSWITCH = 4005
IR_SERIAL_NUMBER = 4010  # 3 registers, 4 BCD digits each

IR_ACTIVE_FUNCTION = 4020
IR_FAN_CONTROL_TYPE = 4021
IR_VENTILATION_MODE = 4022
IR_SUPPLY_PRESSURE = 4023  # signed, 0.1 Pa
IR_EXHAUST_PRESSURE = 4024  # signed, 0.1 Pa

IR_SUPPLY_FAN_STATUS = 4030
IR_SUPPLY_FLOW_SETPOINT = 4031  # m3/h
IR_SUPPLY_FLOW = 4032  # m3/h
IR_SUPPLY_FAN_SPEED = 4034  # rpm
IR_SUPPLY_TEMPERATURE = 4036  # signed, 0.1 degC
IR_SUPPLY_HUMIDITY = 4037  # % (the document says 0.1 %, a Flair 300 reports whole %)

IR_EXHAUST_FAN_STATUS = 4040
IR_EXHAUST_FLOW_SETPOINT = 4041
IR_EXHAUST_FLOW = 4042
IR_EXHAUST_FAN_SPEED = 4044
IR_EXHAUST_TEMPERATURE = 4046
IR_EXHAUST_HUMIDITY = 4047

IR_BYPASS_STATUS = 4050
IR_PREHEATER_STATUS = 4060
IR_PREHEATER_CAPACITY = 4061  # %
IR_FROST_STATUS = 4070
IR_FROST_HEATER_POWER = 4071  # %
IR_FROST_FAN_REDUCTION = 4072  # %

IR_SWITCH_POSITION = 4080
IR_NTC1_TEMPERATURE = 4081  # signed, 0.1 degC, 9999 when not fitted
IR_NTC2_TEMPERATURE = 4082  # signed, 0.1 degC
IR_RHT_HUMIDITY = 4083  # %, assumed to match 4037

IR_FILTER_STATUS = 4100
IR_OPERATING_HOURS = 4113  # 32-bit
IR_FILTER_HOURS = 4115  # hours since the last filter reset

IR_CO2_SENSORS = 4200  # 4 x (status, ppm)

# --- Holding registers (functions 0x03 / 0x06) -------------------------------
HR_FLOW_PRESETS = 6000  # 4 registers, m3/h for levels 0 to 3, step 5
HR_IMBALANCE_ALLOWED = 6033  # 0 no, 1 yes
HR_SUPPLY_IMBALANCE = 6035  # signed, %, -15 to 15
HR_EXHAUST_IMBALANCE = 6036  # signed, %, -15 to 15
HR_BYPASS_MODE = 6100
HR_BYPASS_TEMP_INDOOR = 6101  # 0.1 degC, 150-350, step 5
HR_BYPASS_TEMP_OUTDOOR = 6102  # 0.1 degC, 70-150, step 5
HR_BYPASS_HYSTERESIS = 6103  # 0.1 degC, 0-50, step 5
HR_FILTER_DAYS = 6120  # 1-365
HR_EXTERNAL_HEATER_MODE = 6130
HR_RHT_SENSOR_MODE = 6140
HR_CO2_SENSOR_MODE = 6150
HR_GEO_HEAT_EXCHANGER = 6240  # 0 off, 1 on
HR_GEO_MIN_TEMP = 6241  # signed, 0.1 degC, 0-100
HR_GEO_MAX_TEMP = 6242  # signed, 0.1 degC, 150-400

# --- Remote control registers (functions 0x03 / 0x06) ------------------------
RC_CONTROL = 8000
RC_SWITCH_POSITION = 8001
RC_FLOW_RATE = 8002
RC_STANDBY = 8003
RC_FILTER_RESET = 8010


class ActiveFunction(IntEnum):
    """What the unit is doing (register 4020)."""

    STANDBY = 0
    BOOTLOADER = 1
    NON_BLOCKING_ERROR = 2
    BLOCKING_ERROR = 3
    MANUAL = 4
    HOLIDAY = 5
    NIGHT_VENTILATION = 6
    PARTY = 7
    BYPASS_BOOST = 8
    NORMAL_BOOST = 9
    AUTO_CO2 = 10
    AUTO_EBUS = 11
    AUTO_MODBUS = 12
    AUTO_PORTAL = 13
    AUTO_LOCAL = 14


class VentilationLevel(IntEnum):
    """Ventilation level (registers 4022, 4080 and 8001)."""

    AWAY = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3


class FanStatus(IntEnum):
    """Fan state (registers 4030 and 4040)."""

    NO_COMMUNICATION = 2
    IDLE = 3
    RUNNING = 4
    BLOCKED = 5
    ERROR = 6


class BypassMode(IntEnum):
    """Bypass setting (register 6100)."""

    AUTOMATIC = 0
    CLOSED = 1
    OPEN = 2


class BypassState(IntEnum):
    """Bypass position, simplified from register 4050."""

    INITIALIZING = 0
    OPEN = 1
    CLOSED = 2
    ERROR = 3


# Brink's table lists both 1 and 3 as open and 2 and 4 as closed, and 255 as
# an error.
BYPASS_STATUS_MAP = {
    0: BypassState.INITIALIZING,
    1: BypassState.OPEN,
    2: BypassState.CLOSED,
    3: BypassState.OPEN,
    4: BypassState.CLOSED,
    255: BypassState.ERROR,
}


class FanControlType(IntEnum):
    """How the fans are regulated (register 4021)."""

    INITIALIZING = 0
    CONSTANT_FLOW = 1
    CONSTANT_PWM = 2
    OFF = 3
    ERROR = 4
    MASS_BALANCE = 5
    STANDBY = 6


class CO2SensorStatus(IntEnum):
    """CO2 sensor state (registers 4200, 4202, 4204 and 4206)."""

    ERROR = 0
    NOT_INITIALIZED = 1
    IDLE = 2
    WARMING_UP = 3
    RUNNING = 4
    CALIBRATING = 5
    SELF_TEST = 6


class FrostStatus(IntEnum):
    """Frost protection state (register 4070)."""

    NOT_INITIALIZED = 0
    POWER_UP_DELAY = 1
    NO_FROST = 2
    NO_FROST_DELAY = 3
    START_DELAY = 4
    WAIT_FOR_ICING = 5
    ICE_DETECTED_DELAY = 6
    HEATING = 7
    WAIT_FOR_FREE_HEATER = 8
    FAN_CONTROL_START_DELAY = 9
    FAN_CONTROL_WAIT_DELAY = 10
    FAN_CONTROL = 11
    FAN_OFF_DELAY = 12
    FAN_OFF = 13
    FAN_RESTARTING = 14
    ERROR = 15
    TEST_MODE = 16


# Frost protection is acting on the airflow or the heater in these states.
FROST_ACTIVE_STATES = frozenset(
    {
        FrostStatus.ICE_DETECTED_DELAY,
        FrostStatus.HEATING,
        FrostStatus.WAIT_FOR_FREE_HEATER,
        FrostStatus.FAN_CONTROL_START_DELAY,
        FrostStatus.FAN_CONTROL_WAIT_DELAY,
        FrostStatus.FAN_CONTROL,
        FrostStatus.FAN_OFF_DELAY,
        FrostStatus.FAN_OFF,
        FrostStatus.FAN_RESTARTING,
    }
)


class ControlMode(IntEnum):
    """Who sets the ventilation level (register 8000)."""

    OFF = 0
    SWITCH = 1
    FLOW = 2
