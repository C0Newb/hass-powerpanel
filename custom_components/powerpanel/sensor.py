from enum import Enum  # noqa: D100
import math
import sys

# pylint: enable=unused-wildcard-import
import threading
import time
import traceback

from pysnmp import hlapi
from pysnmp.error import PySnmpError

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
    EntityCategory,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

# pylint: disable=unused-wildcard-import
from .const import DOMAIN, LOGGER


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """Set up the sensor platform."""
    LOGGER.info("SETUP_ENTRY")
    ipaddress = config_entry.data.get(CONF_IP_ADDRESS)
    serviceName = config_entry.data.get(CONF_USERNAME)
    port = config_entry.data.get(CONF_PORT)
    updateIntervalSeconds = config_entry.options.get(CONF_SCAN_INTERVAL)
    maxretries = 3

    for i in range(maxretries):
        try:
            monitor = PowerPanelSnmpMonitor(
                ipaddress, port, serviceName, updateIntervalSeconds, async_add_entities
            )
            break
        except:
            if i == maxretries - 1:
                raise

    hass.data[DOMAIN][config_entry.entry_id] = {"monitor": monitor}

    monitor.start()

    def _stop_monitor(_event):
        monitor.stopped = True

    # hass.states.async_set
    hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, _stop_monitor)
    LOGGER.info("Init done")
    return True


class BatteryStatus(Enum):
    """Battery status."""

    Unknown = 1
    BatteryNormal = 2
    BatteryLow = 3

    @staticmethod
    def get_icon(value):
        """Return the icon for a given value."""

        if value == BatteryStatus.BatteryLow.value:
            return "mdi:battery-20"
        if value == BatteryStatus.BatteryNormal.value:
            return "mdi:battery"
        return "mdi:battery-unknown"


class BatteryReplaceIndicator(Enum):
    """Battery replacement indicator."""

    NoBatteryNeedsReplacing = 1
    BatteryNeedsReplacing = 2

    @staticmethod
    def get_icon(value):
        """Return the icon for a given value."""
        if value == BatteryReplaceIndicator.NoBatteryNeedsReplacing.value:
            return "mdi:battery-heart-variant"
        return "mdi:battery-alert-variant-outline"


class InputLineFailCause(Enum):
    """Input line failure cause."""

    NoTransfer = 1
    HighLineVoltage = 2
    LowLineVoltage = 3
    SelfTest = 4

    @staticmethod
    def get_icon(value):
        """Return the icon for a given value."""
        if value == InputLineFailCause.NoTransfer.value:
            # return "mdi:transmission-tower"
            return "mdi:power-plug"
        if value == InputLineFailCause.HighLineVoltage.value:
            return "mdi:flash-triangle"
        if value == InputLineFailCause.LowLineVoltage.value:
            # return "mdi:transmission-tower-off"
            return "mdi:power-plug-off"
        return "mdi:battery-sync"  # Battery check ?


class InputStatus(Enum):
    """Incoming utility power status."""

    Normal = 1
    OverVoltage = 2
    UnderVoltage = 3
    FrequencyFailure = 4
    Blackout = 5

    @staticmethod
    def get_icon(value):
        """Return the icon for a given value."""
        if value == InputStatus.Normal.value:
            return "mdi:transmission-tower"
        if value == InputStatus.OverVoltage.value:
            return "mdi:flash-triangle"
        if value == InputStatus.UnderVoltage.value:
            return "mdi:lightning-bolt-outline"
        if value == InputStatus.FrequencyFailure.value:
            return "mdi:sine-wave"
        return "mdi:transmission-tower-off"


class OutputStatus(Enum):
    """Outgoing power status, what the UPS is doing."""

    Unknown = 1
    OnLine = 2
    OnBattery = 3
    OnBoost = 4
    OnSleep = 5
    Off = 6
    Rebooting = 7

    @staticmethod
    def get_icon(value):
        """Return the icon for a given value."""
        if value == OutputStatus.Unknown.value:
            return "mdi:help-box-outline"
        if value == OutputStatus.OnLine.value:
            return "mdi:transmission-tower"
        if value == OutputStatus.OnBattery.value:
            return "mdi:home-battery-outline"
        if value == OutputStatus.OnBoost.value:
            return "mdi:home-lightning-bolt-outline"
        if value == OutputStatus.OnSleep.value:
            return "mdi:power-sleep"
        if value == OutputStatus.Off.value:
            return "mdi:power-plug-off"
        return "mdi:restart"


class AudioAlarm(Enum):
    """Alarm audio state."""

    Timed = 1
    Enable = 2
    Disable = 3
    Mute = 4

    @staticmethod
    def get_icon(value):
        """Return the icon for a given value."""
        if value == AudioAlarm.Timed.value:
            return "mdi:timer"
        if value == AudioAlarm.Enable.value:
            return "mdi:volume-high"
        if value == AudioAlarm.Disable.value:
            return "mdi:alarm-off"
        return "mdi:volume-off"


class PowerPanelSnmpSensor(Entity):
    """Power Panel SNMP sensor."""

    def __init__(self, uniqueId, name=None, powerPanelSnmpMonitor=None) -> None:
        """Initialize."""
        self._attributes = {}
        self._state = "NOTRUN"
        self.entity_id = uniqueId
        if name is None:
            name = uniqueId
        self._name = name
        self._monitor: PowerPanelSnmpMonitor = powerPanelSnmpMonitor
        LOGGER.info(f"Create Sensor {uniqueId}")

    def set_state(self, state):
        """Set the state."""
        if self._state == state:
            return
        self._state = state
        if self.enabled:
            self.schedule_update_ha_state()

    def set_attributes(self, attributes):
        """Set the state attributes."""
        self._attributes = attributes

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return self.entity_id

    @property
    def should_poll(self) -> bool:
        """Only poll to update phonebook, if defined."""
        return False

    @property
    def state_attributes(self) -> dict[str, any] | None:
        """Return the state attributes."""
        return self._attributes

    @property
    def state(self) -> bool:
        """Return the state of the device."""
        return self._state

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def device_info(self):
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._monitor.serialNumber)},
            name=self._monitor.name + " UPS",
            manufacturer="CyberPower",
            model=self._monitor.model,
            sw_version=self._monitor.powerPanelVersion,
        )

    def update(self) -> None:
        """Log the word update and some id. Idk, linter wants a damn doc string."""
        LOGGER.info("update " + self.entity_id)


class PowerPanelSnmpMonitor:
    """Linter something something this is a class read the name."""

    def __init__(
        self,
        target_ip,
        port,
        serviceName,
        updateIntervalSeconds=1,
        async_add_entities=None,
    ) -> None:
        """Initalizes_the grabbing my SNMP data class."""

        self.target_ip = target_ip
        self.port = port
        self.serviceName = serviceName
        self.stopped = False
        self.async_add_entities = async_add_entities
        self.updateIntervalSeconds = updateIntervalSeconds

        self.meterSensors = {}

        self.stat_time = 0

        # ident
        self.model = "Unknown"
        self.serialNumber = "Unknown"
        self.name = "UPS"
        self.powerPanelVersion = "0"
        self.upsFirmwareVersion = "0"
        self.powerRating = 0

        # battery
        self.batteryStatus = BatteryStatus.Unknown
        self.timeOnBattery = 0
        self.batteryPercentage = 0
        self.batteryRuntimeRemaining = 0
        self.batteryReplaceIndicator = BatteryReplaceIndicator.NoBatteryNeedsReplacing
        # utility
        self.inputVoltage = 0
        self.inputFrequency = 0
        self.inputLineFailCause = InputLineFailCause.NoTransfer
        self.inputStatus = InputStatus.Normal
        # output
        self.outputStatus = OutputStatus.Unknown
        self.outputVoltage = 0
        self.outputFrequency = 0
        self.outputLoad = 0
        self.outputCurrent = 0
        self.outputPower = self.outputVoltage * self.outputCurrent
        # input/output
        self.alarmAudio = AudioAlarm.Disable

        self.update_stats()  # try this to throw error if not working.
        if async_add_entities is not None:
            self.setupEntities()

    # region static methods
    @staticmethod
    def construct_object_types(list_of_oids):
        """Linter doc string."""
        object_types = []
        for oid in list_of_oids:
            object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))  # noqa: PERF401
        return object_types

    @staticmethod
    def fetch(handler, count):
        """Return an SNMP data value."""
        result = []
        for _ in range(count):
            try:
                error_indication, error_status, error_index, var_binds = next(handler)
                if not error_indication and not error_status:
                    items = {}
                    for var_bind in var_binds:
                        items[str(var_bind[0])] = __class__.cast(var_bind[1])
                    result.append(items)
                else:
                    raise RuntimeError(f"Got SNMP error: {error_indication}")
            except StopIteration:
                break
        return result

    @staticmethod
    def get(
        target,
        oids,
        credentials,
        port=161,
        engine=hlapi.SnmpEngine(),
        context=hlapi.ContextData(),
    ) -> list:
        """Use SNMP to get a OID endpoint status."""
        handler = hlapi.getCmd(
            engine,
            credentials,
            hlapi.UdpTransportTarget((target, port)),
            context,
            *__class__.construct_object_types(oids),
        )
        return __class__.fetch(handler, 1)[0]

    @staticmethod
    def cast(value):
        """Attempt to cast a value as an int, float, string or give up."""
        try:
            return int(value)
        except (ValueError, TypeError):
            try:
                return float(value)
            except (ValueError, TypeError):
                try:
                    return str(value)
                except (ValueError, TypeError):
                    pass
        return value

    # endregion
    def getBatteryIcon(self):
        """Battery icon depending on percentage and wether or not we're online."""
        divider = "-"
        if self.outputStatus == OutputStatus.OnLine.value:
            divider = "-charging-"

        if self.batteryPercentage > 98:
            return "mdi:battery" + divider[0:-1]
        if self.batteryPercentage < 10:
            # man python amirite, anyways drop the last "-"
            return "mdi:battery" + divider + "outline"
        return (
            "mdi:battery" + divider + str(math.floor(self.batteryPercentage / 10)) + "0"
        )  # Convert 82, for example, to 80

    def getOutputLoadIcon(self):
        """Get the guage icon representing the current output load."""
        if self.outputLoad > 90:
            return "mdi:gauge-full"
        if self.outputLoad > 55:
            return "mdi:gauge"
        if self.outputLoad > 25:
            return "mdi:gauge-low"
        return "mdi:gauge-empty"

    def update_stats(self):
        """Grab the UPS data from PowerPanel using SNMP."""
        data = __class__.get(
            self.target_ip,
            [
                "1.3.6.1.4.1.3808.1.1.1.1.1.1.0",  # model
                "1.3.6.1.4.1.3808.1.1.1.1.1.2.0",  # name
                "1.3.6.1.4.1.3808.1.1.1.1.2.1.0",  # firmware version
                "1.3.6.1.4.1.3808.1.1.1.1.2.3.0",  # serial number
                "1.3.6.1.4.1.3808.1.1.1.1.2.4.0",  # powerpanel version
                "1.3.6.1.4.1.3808.1.1.1.1.2.6.0",  # powerRating
                "1.3.6.1.4.1.3808.1.1.1.1.2.7.0",  # currentRating
                "1.3.6.1.4.1.3808.1.1.1.2.1.1.0",  # batteryStatus
                "1.3.6.1.4.1.3808.1.1.1.2.1.2.0",  # timeOnBattery
                "1.3.6.1.4.1.3808.1.1.1.2.2.1.0",  # batteryPercentage
                "1.3.6.1.4.1.3808.1.1.1.2.2.4.0",  # batteryRuntimeRemaining
                "1.3.6.1.4.1.3808.1.1.1.2.2.5.0",  # batteryReplaceIndicator
                "1.3.6.1.4.1.3808.1.1.1.3.2.1.0",  # inputVoltage
                "1.3.6.1.4.1.3808.1.1.1.3.2.4.0",  # inputFrequency
                "1.3.6.1.4.1.3808.1.1.1.3.2.5.0",  # inputLineFailCause
                "1.3.6.1.4.1.3808.1.1.1.3.2.6.0",  # inputStatus
                "1.3.6.1.4.1.3808.1.1.1.4.1.1.0",  # outputStatus
                "1.3.6.1.4.1.3808.1.1.1.4.2.1.0",  # outputVoltage
                "1.3.6.1.4.1.3808.1.1.1.4.2.2.0",  # outputFrequency
                "1.3.6.1.4.1.3808.1.1.1.4.2.3.0",  # outputLoad
                "1.3.6.1.4.1.3808.1.1.1.4.2.4.0",  # outputCurrent
                "1.3.6.1.4.1.3808.1.1.1.5.2.4.0",  # alarmAudio
            ],
            hlapi.CommunityData(self.serviceName, self.serviceName, 0),
            self.port,
        )

        self.model = data["1.3.6.1.4.1.3808.1.1.1.1.1.1.0"]  # model
        self.name = data["1.3.6.1.4.1.3808.1.1.1.1.1.2.0"]  # name
        self.serialNumber = data["1.3.6.1.4.1.3808.1.1.1.1.2.3.0"]  # serial number
        self.powerRating = data["1.3.6.1.4.1.3808.1.1.1.1.2.6.0"]  # powerRating
        self.currentRating = data["1.3.6.1.4.1.3808.1.1.1.1.2.7.0"]  # currentRating
        self.powerPanelVersion = data[
            "1.3.6.1.4.1.3808.1.1.1.1.2.4.0"
        ]  # powerpanel version
        self.upsFirmwareVersion = data[
            "1.3.6.1.4.1.3808.1.1.1.1.2.1.0"
        ]  # firmware version
        # battery
        self.batteryStatus = data["1.3.6.1.4.1.3808.1.1.1.2.1.1.0"]  # batteryStatus
        self.timeOnBattery = (
            data["1.3.6.1.4.1.3808.1.1.1.2.1.2.0"] / 100
        )  # timeOnBattery
        self.batteryPercentage = data[
            "1.3.6.1.4.1.3808.1.1.1.2.2.1.0"
        ]  # batteryPercentage
        self.batteryRuntimeRemaining = (
            data["1.3.6.1.4.1.3808.1.1.1.2.2.4.0"] / 100 / 60
        )  # batteryRuntimeRemaining (in minutes! (it only gives a number rounded to a minute))
        self.batteryReplaceIndicator = data[
            "1.3.6.1.4.1.3808.1.1.1.2.2.5.0"
        ]  # batteryReplaceIndicator

        # utility
        self.inputVoltage = data["1.3.6.1.4.1.3808.1.1.1.3.2.1.0"] / 10  # inputVoltage
        self.inputFrequency = (
            data["1.3.6.1.4.1.3808.1.1.1.3.2.4.0"] / 10
        )  # inputFrequency
        self.inputLineFailCause = data[
            "1.3.6.1.4.1.3808.1.1.1.3.2.5.0"
        ]  # inputLineFailCause
        self.inputStatus = data["1.3.6.1.4.1.3808.1.1.1.3.2.6.0"]  # inputStatus

        # output
        self.outputStatus = data["1.3.6.1.4.1.3808.1.1.1.4.1.1.0"]  # outputStatus
        self.outputVoltage = (
            data["1.3.6.1.4.1.3808.1.1.1.4.2.1.0"] / 10
        )  # outputVoltage
        self.outputFrequency = (
            data["1.3.6.1.4.1.3808.1.1.1.4.2.2.0"] / 10
        )  # outputFrequency
        self.outputLoad = data["1.3.6.1.4.1.3808.1.1.1.4.2.3.0"]  # outputLoad
        self.outputCurrent = (
            data["1.3.6.1.4.1.3808.1.1.1.4.2.4.0"] / 10
        )  # outputCurrent
        self.outputPower = self.outputVoltage * self.outputCurrent

        self.alarmAudio = data["1.3.6.1.4.1.3808.1.1.1.5.2.4.0"]  # alarmAudio

    def start(self):
        """Start polling."""
        threading.Thread(target=self.watcher).start()

    def watcher(self):
        """Poll."""
        LOGGER.info(
            f"Start Watcher Thread - updateInterval:{self.updateIntervalSeconds}"
        )

        while not self.stopped:
            try:
                # LOGGER.warning('Get PowerMeters: ')
                self.update_stats()
                if self.async_add_entities is not None:
                    self.updateEntities()
            except (KeyError, PySnmpError):
                time.sleep(1)  # sleep a second for these errors
            except:  # other errors get logged...  # noqa: E722
                e = traceback.format_exc()
                LOGGER.error(e)
            if self.updateIntervalSeconds is None:
                self.updateIntervalSeconds = 5

            time.sleep(max(1, self.updateIntervalSeconds))

    def setupEntities(self):
        """Setups up the sensor entities."""
        self.update_stats()
        if self.async_add_entities is not None:
            self.updateEntities()

    def _addOrUpdateEntity(
        self,
        uniqueId,
        friendlyname,
        value,
        unit="",
        deviceClass: SensorDeviceClass = None,
        enum: list = None,
        state: str = "measurement",
        icon: str = None,
        enabled: bool = True,
        entityCategory=EntityCategory.DIAGNOSTIC,
    ):
        attributes = {
            "unit_of_measurement": unit,
            "friendly_name": friendlyname,
            "state_class": state,
            "entity_registry_enabled_default": enabled,
            "entity_registry_visible_default": enabled,
            "suggested_display_precision": 1,
            "entity_category": entityCategory,
        }
        if deviceClass is not None:
            attributes["device_class"] = deviceClass.name
        if enum is not None:
            attributes["options"] = enum
        if icon is not None:
            attributes["icon"] = icon

        if uniqueId in self.meterSensors:
            sensor = self.meterSensors[uniqueId]
            sensor.set_state(value)
            sensor.set_attributes(attributes)
        else:
            sensor = PowerPanelSnmpSensor(
                uniqueId, friendlyname, powerPanelSnmpMonitor=self
            )
            sensor._state = value
            sensor.set_attributes(attributes)
            self.async_add_entities([sensor])
            # time.sleep(.5)#sleep a moment and wait for async add
            self.meterSensors[uniqueId] = sensor

    def updateEntities(self):
        """Linter doc string."""
        allSensorsPrefix = (
            "sensor." + DOMAIN + "_" + self.target_ip.replace(".", "_") + "_"
        )

        # Static "model number, max output"
        self._addOrUpdateEntity(
            allSensorsPrefix + "model",
            "UPS Device Model",
            self.model,
            state="total",
            icon="mdi:badge-account",
        )
        self._addOrUpdateEntity(
            allSensorsPrefix + "name",
            "UPS Device Friendly Name",
            self.name,
            state="total",
            icon="mdi:badge-account",
            enabled=False,
        )
        self._addOrUpdateEntity(  # Power rating (VA)
            allSensorsPrefix + "power_rating",
            "UPS Device Power Rating",
            self.powerRating,
            unit="VA",
            deviceClass=SensorDeviceClass.APPARENT_POWER,
            state="total",
            icon="mdi:lightning-bolt",
            enabled=False,
        )
        self._addOrUpdateEntity(  # Power rating (VA)
            allSensorsPrefix + "current_rating",
            "UPS Device Current Rating",
            self.currentRating,
            unit="A",
            deviceClass=SensorDeviceClass.CURRENT,
            state="total",
            icon="mdi:lightning-bolt",
            enabled=False,
        )

        # Battery
        self._addOrUpdateEntity(  # Battery status
            allSensorsPrefix + "battery_status",
            "UPS Battery Status",
            BatteryStatus(self.batteryStatus).name,
            deviceClass=SensorDeviceClass.ENUM,
            enum=[e.name for e in BatteryStatus],
            icon=BatteryStatus.get_icon(self.batteryStatus),
            enabled=False,
        )
        self._addOrUpdateEntity(  # Time on battery
            allSensorsPrefix + "battery_time_on_battery",
            "Time on Battery Backup",
            self.timeOnBattery,
            unit="s",
            deviceClass=SensorDeviceClass.DURATION,
            state="total",
            icon="mdi:timer",
            enabled=False,
        )
        self._addOrUpdateEntity(  # Battery percentage %
            allSensorsPrefix + "battery_percentage",
            "Battery Percentage",
            self.batteryPercentage,
            unit="%",
            deviceClass=SensorDeviceClass.BATTERY,
            icon=self.getBatteryIcon(),
        )

        self._addOrUpdateEntity(  # Battery runtime remaining
            allSensorsPrefix + "battery_runtime",
            "Remaining Battery Runtime",
            self.batteryRuntimeRemaining,
            unit="m",
            deviceClass=SensorDeviceClass.DURATION,
            icon="mdi:timer",
        )
        self._addOrUpdateEntity(  # Battery replace indicator
            allSensorsPrefix + "battery_replace_indicator",
            "Battery Replacement Indicator",
            BatteryReplaceIndicator(self.batteryReplaceIndicator).name,
            deviceClass=SensorDeviceClass.ENUM,
            enum=[e.name for e in BatteryReplaceIndicator],
            icon=BatteryReplaceIndicator.get_icon(self.batteryReplaceIndicator),
        )

        # Input
        self._addOrUpdateEntity(  # Input voltage
            allSensorsPrefix + "input_voltage",
            "Utility Input Voltage",
            self.inputVoltage,
            unit="v",
            deviceClass=SensorDeviceClass.VOLTAGE,
            icon="mdi:lightning-bolt",
        )
        self._addOrUpdateEntity(  # Input frequency
            allSensorsPrefix + "input_frequency",
            "Utility Input Frequency",
            self.inputFrequency,
            unit="Hz",
            deviceClass=SensorDeviceClass.FREQUENCY,
            icon="mdi:sine-wave",
            enabled=False,
        )
        self._addOrUpdateEntity(  # Input failure reason
            allSensorsPrefix + "input_line_fail_cause",
            "Utility Input Failure Reason",
            InputLineFailCause(self.inputLineFailCause).name,
            deviceClass=SensorDeviceClass.ENUM,
            enum=[e.name for e in InputLineFailCause],
            icon=InputLineFailCause.get_icon(self.inputLineFailCause),
            enabled=False,
        )
        self._addOrUpdateEntity(  # Utility input status
            allSensorsPrefix + "input_status",
            "Utility Input Status",
            InputStatus(self.inputStatus).name,
            deviceClass=SensorDeviceClass.ENUM,
            enum=[e.name for e in InputStatus],
            icon=InputStatus.get_icon(self.inputStatus),
        )

        # Output
        self._addOrUpdateEntity(  # Output status
            allSensorsPrefix + "output_status",
            "Output Status",
            OutputStatus(self.outputStatus).name,
            deviceClass=SensorDeviceClass.ENUM,
            enum=[e.name for e in OutputStatus],
            icon=OutputStatus.get_icon(self.outputStatus),
            enabled=False,
        )
        self._addOrUpdateEntity(  # Output voltage
            allSensorsPrefix + "output_voltage",
            "Output Voltage",
            self.outputVoltage,
            unit="v",
            deviceClass=SensorDeviceClass.VOLTAGE,
            icon="mdi:lightning-bolt",
            enabled=False,
        )
        self._addOrUpdateEntity(  # Output frequency
            allSensorsPrefix + "output_frequency",
            "Output Frequency",
            self.outputFrequency,
            unit="Hz",
            deviceClass=SensorDeviceClass.FREQUENCY,
            icon="mdi:sine-wave",
            enabled=False,
        )
        self._addOrUpdateEntity(  # Output load
            allSensorsPrefix + "output_load",
            "Output Load",
            self.outputLoad,
            unit="%",
            deviceClass=SensorDeviceClass.BATTERY,
            icon=self.getOutputLoadIcon(),
        )
        self._addOrUpdateEntity(  # Output current (amps)
            allSensorsPrefix + "output_current",
            "Output Current",
            self.outputCurrent,
            unit="A",
            deviceClass=SensorDeviceClass.CURRENT,
            icon="mdi:lightning-bolt",
            enabled=False,
        )

        self._addOrUpdateEntity(  # Wattage
            allSensorsPrefix + "output_power",
            "Output Wattage",
            self.outputPower,
            unit="W",
            deviceClass=SensorDeviceClass.POWER,
            icon="mdi:lightning-bolt",
        )

        # Alarm status
        self._addOrUpdateEntity(
            allSensorsPrefix + "alarm_audio",
            "Alarm Status",
            self.alarmAudio,
            deviceClass=SensorDeviceClass.ENUM,
            enum=[e.name for e in AudioAlarm],
            icon=AudioAlarm.get_icon(self.alarmAudio),
            enabled=False,
            entityCategory=EntityCategory.CONFIG,
        )
