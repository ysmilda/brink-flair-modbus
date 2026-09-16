"""Discrete values reported or accepted by a Brink Flair unit."""

from __future__ import annotations

from enum import IntEnum


class OperatingMode(IntEnum):
    """The ventilation unit's overall operating mode (input register 4020)."""

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
    AUTO_LAN_WLAN_PORTAL = 13
    AUTO_LAN_WLAN_LOCAL = 14


class BypassStatus(IntEnum):
    """The heat-recovery bypass position (input register 4050)."""

    INITIALIZE = 0
    OPENING = 1
    CLOSING = 2
    OPEN = 3
    CLOSED = 4
    ERROR = 255


class FrostStatus(IntEnum):
    """The frost-protection state machine (input register 4070)."""

    INITIALIZE = 0
    POWERUP_DELAY = 1
    NO_FROST = 2
    NO_FROST_DELAY = 3
    FROST_CONTROL_START_DELAY = 4
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
    TEST_MODUS = 16


class VentilationLevel(IntEnum):
    """The manual ventilation level (holding register 8001)."""

    ABSENCE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ControlMode(IntEnum):
    """The control mode (holding register 8000)."""

    OFF = 0
    STEP = 1
    FLOW = 2


class BypassMode(IntEnum):
    """The user-selected bypass state (holding register 6100)."""

    AUTO = 0
    CLOSED = 1
    OPEN = 2


class FanControlType(IntEnum):
    """The method used to control the fans (input register 4021)."""

    INITIALIZING = 0
    CONSTANT_FLOW = 1
    CONSTANT_PWM = 2
    OFF = 3
    ERROR = 4
    MASS_BALANCE = 5
    STANDBY = 6


class VentilationMode(IntEnum):
    """The currently active ventilation mode (input register 4022)."""

    HOLIDAY = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    AUTO = 4


class FanStatus(IntEnum):
    """The state of one fan (input registers 4030 and 4040)."""

    NO_COMMUNICATION = 2
    IDLE = 3
    RUNNING = 4
    BLOCKED = 5
    FAN_ERROR = 6


class PreheaterStatus(IntEnum):
    """The preheater state machine (input register 4060)."""

    INITIALIZE = 0
    INACTIVE = 1
    ACTIVE = 2
    TEST_MODE = 3


class EBusPowerStatus(IntEnum):
    """The eBus power state (input register 4101)."""

    POWER_UP = 0
    INITIALIZE_POWER = 1
    POWER_OFF = 2
    POWER_ON = 3
    WAIT_FOR_POWER_OFF = 4
    SLAVE_POWER_OFF = 5


class GeoExchangerStatus(IntEnum):
    """The geo heat-exchanger valve (input register 4150)."""

    OPEN_LOW = 0
    CLOSED = 1
    OPEN_HIGH = 2


class Co2SensorStatus(IntEnum):
    """The state of a CO2 sensor (input registers 4200-4206)."""

    ERROR = 0
    NOT_INITIALIZED = 1
    IDLE = 2
    WARMING_UP = 3
    RUNNING = 4
    CALIBRATING = 5
    SELF_TEST = 6


class SystemErrorStatus(IntEnum):
    """The overall system error state (input register 4800)."""

    NO_ERROR = 0
    WARNING = 1
    NON_BLOCKING_ERROR = 2
    BLOCKING_ERROR = 3


class FlowType(IntEnum):
    """The fan control method (holding register 6030)."""

    CONSTANT_PWM = 0
    CONSTANT_FLOW = 1
    CONSTANT_MASS_FLOW = 2


class ExternalHeaterMode(IntEnum):
    """How an external heater is used (holding register 6130)."""

    NOT_AVAILABLE = 0
    PRE_HEATER = 1
    POST_HEATER = 2


class SignalOutputFunction(IntEnum):
    """What the signal output reports (holding register 6170)."""

    OFF = 0
    FILTER_WARNING = 1
    ERROR_STATUS = 2
    FILTER_WARNING_AND_ERROR_STATUS = 3


class DigitalInputFunction(IntEnum):
    """What a digital input does (holding registers 6201 and 6211)."""

    OFF = 0
    ON = 1
    ON_IF_BYPASS_OPEN = 2
    BYPASS_CONTROL = 3
    EXTERNAL_VALVE_CONTROL = 4


class FanFunction(IntEnum):
    """How a digital input drives its fan (holding registers 6202-6213)."""

    FAN_OFF = 0
    ABSOLUTE_MINIMUM_FLOW = 1
    PREDEFINED_VALUE_MODE_1 = 2
    PREDEFINED_VALUE_MODE_2 = 3
    PREDEFINED_VALUE_MODE_3 = 4
    POSITION_SWITCH = 5
    ABSOLUTE_MAXIMUM_FLOW = 6
    UNCHANGED = 7


class GeoValvePosition(IntEnum):
    """The geo valve position at zero output (holding register 6243)."""

    CLOSED = 0
    OPEN = 1


class GeoValveOutput(IntEnum):
    """The output driving the geo valve (holding register 6244)."""

    ANALOGUE_OUTPUT_1 = 0
    ANALOGUE_OUTPUT_2 = 1
    RELAY_OUTPUT_1 = 2
    RELAY_OUTPUT_2 = 3


class Language(IntEnum):
    """The unit language (holding register 6900)."""

    ENGLISH = 0
    DUTCH = 1


class DateFormat(IntEnum):
    """The date format (holding register 6901)."""

    DD_MM_YYYY = 0
    MM_DD_YYYY = 1


class TimeNotation(IntEnum):
    """The clock format (holding register 6902)."""

    HOUR_12 = 0
    HOUR_24 = 1


class ModbusInterfaceType(IntEnum):
    """Where the Modbus interface is wired (holding register 7990)."""

    MODBUS_INTERNAL = 0
    MODBUS_EXTERNAL_CONNECT = 1
    EXTERNAL_CUSTOMER = 2


class ModbusSpeed(IntEnum):
    """The Modbus baud rate (holding register 7992)."""

    BAUD_1200 = 0
    BAUD_2400 = 1
    BAUD_4800 = 2
    BAUD_9600 = 3
    BAUD_19200 = 4
    BAUD_38400 = 5
    BAUD_56000 = 6
    BAUD_115200 = 7


class ModbusParity(IntEnum):
    """The Modbus parity setting (holding register 7993)."""

    NONE = 0
    EVEN = 1
    ODD = 2


class StandbyCommand(IntEnum):
    """The standby command and reported state (holding register 8003).

    Writing 0 leaves the unit alone, 1 places it in standby and 2 returns it
    to normal operation; the value read back is the actual standby state (0
    or 1) as changed through any interface.
    """

    NO_ACTION = 0
    STANDBY = 1
    NORMAL = 2
