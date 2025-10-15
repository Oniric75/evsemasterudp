"""Sensors for the EVSE EmProto integration"""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfEnergy,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EVSE sensors"""
    
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    serial = data["serial"]
    base_name = data.get("base_name", f"EVSE {serial}")
    
    # Create sensors
    client = data["client"]
    entities = [
        EVSEStateSensor(coordinator, serial, base_name),
        EVSEPowerSensor(coordinator, serial, base_name),
        EVSECurrentSensor(coordinator, serial, base_name),
        EVSEVoltageSensor(coordinator, serial, base_name),
        EVSEEnergySensor(coordinator, serial, base_name),
        EVSETemperatureSensor(coordinator, serial, base_name, "inner"),
        EVSETemperatureSensor(coordinator, serial, base_name, "outer"),
        EVSEChargeStatusSensor(coordinator, serial, base_name, client),
    ]
    
    async_add_entities(entities)

class EVSEBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for EVSE"""
    
    def __init__(self, coordinator, serial: str, base_name: str):
        super().__init__(coordinator)
        self.serial = serial
        self.base_name = base_name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": base_name,
            "manufacturer": "Oniric75",
            "model": "EVSE Master UDP",
        }
    
    @property
    def evse_data(self):
        """Get EVSE data"""
        return self.coordinator.data.get(self.serial, {})

class EVSEChargeStatusSensor(EVSEBaseSensor):
    """Simple binary (charging / idle)."""

    def __init__(self, coordinator, serial: str, base_name: str, client):
        super().__init__(coordinator, serial, base_name)
        self.client = client
        self._attr_name = f"{base_name} Charge Status"
        self._attr_unique_id = f"{serial}_charge_status"
        self._attr_icon = "mdi:ev-station"

    @property
    def native_value(self):
        data = self.evse_data
        if not data:
            return None
    # Determine if charging: meta-state CHARGING or output_state==1 or significant power
        current_power = data.get("current_power", 0) or 0
        charging = bool(
            data.get("state") == "CHARGING" or
            data.get("output_state") == 1 or
            current_power > 10
        )

        if charging:
            return "charging"

        # Check cooldown protection
        remaining = self.client.get_cooldown_remaining(self.serial)
        if remaining.total_seconds() > 0:
            return "soft_protection"  # anti-cycle protection mode
        return "not_charging"

    @property
    def extra_state_attributes(self):
        remaining = self.client.get_cooldown_remaining(self.serial)
        return {
            "cooldown_remaining_s": int(remaining.total_seconds()),
        }

class EVSEStateSensor(EVSEBaseSensor):
    """EVSE state sensor"""
    
    def __init__(self, coordinator, serial: str, base_name: str):
        super().__init__(coordinator, serial, base_name)
        self._attr_name = f"{base_name} State"
        self._attr_unique_id = f"{serial}_state"
        self._attr_icon = "mdi:ev-station"
    
    @property
    def native_value(self) -> str | None:
        """Return the EVSE state"""
        data = self.evse_data
        if not data.get("online"):
            return "offline"
        return data.get("state", "unknown").lower()
    
    @property
    def extra_state_attributes(self):
        """Additional attributes"""
        data = self.evse_data
        return {
            "online": data.get("online", False),
            "logged_in": data.get("logged_in", False),
            "ip": data.get("ip"),
            "last_seen": data.get("last_seen"),
        }

class EVSEPowerSensor(EVSEBaseSensor):
    """EVSE power sensor"""
    
    def __init__(self, coordinator, serial: str, base_name: str):
        super().__init__(coordinator, serial, base_name)
        self._attr_name = f"{base_name} Power"
        self._attr_unique_id = f"{serial}_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:flash"
    
    @property
    def native_value(self) -> float | None:
        """Return the current power"""
        data = self.evse_data
        return data.get("current_power", 0)

class EVSECurrentSensor(EVSEBaseSensor):
    """EVSE current sensor"""
    
    def __init__(self, coordinator, serial: str, base_name: str):
        super().__init__(coordinator, serial, base_name)
        self._attr_name = f"{base_name} Current"
        self._attr_unique_id = f"{serial}_current"
        self._attr_device_class = SensorDeviceClass.CURRENT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_icon = "mdi:current-ac"
    
    @property
    def native_value(self) -> float | None:
        """Return the current"""
        data = self.evse_data
        return data.get("current_l1", 0)

class EVSEVoltageSensor(EVSEBaseSensor):
    """EVSE voltage sensor"""
    
    def __init__(self, coordinator, serial: str, base_name: str):
        super().__init__(coordinator, serial, base_name)
        self._attr_name = f"{base_name} Voltage"
        self._attr_unique_id = f"{serial}_voltage"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_icon = "mdi:sine-wave"
    
    @property
    def native_value(self) -> float | None:
        """Return the current voltage"""
        data = self.evse_data
        return data.get("voltage_l1", 0)

class EVSEEnergySensor(EVSEBaseSensor):
    """EVSE energy sensor"""
    
    def __init__(self, coordinator, serial: str, base_name: str):
        super().__init__(coordinator, serial, base_name)
        self._attr_name = f"{base_name} Energy"
        self._attr_unique_id = f"{serial}_energy"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:counter"
    
    @property
    def native_value(self) -> float | None:
        """Return the consumed energy"""
        data = self.evse_data
        return data.get("charge_kwh", 0)

class EVSETemperatureSensor(EVSEBaseSensor):
    """EVSE temperature sensor"""
    
    def __init__(self, coordinator, serial: str, base_name: str, temp_type: str):
        super().__init__(coordinator, serial, base_name)
        self.temp_type = temp_type
        self._attr_name = f"{base_name} Temperature {temp_type.title()}"
        self._attr_unique_id = f"{serial}_temperature_{temp_type}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer"
    
    @property
    def native_value(self) -> float | None:
        """Return the temperature"""
        data = self.evse_data
        return data.get(f"temperature_{self.temp_type}", 0)