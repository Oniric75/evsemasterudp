"""(Removed legacy switch placeholder kept intentionally blank)."""

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EVSE switches"""
    
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    serial = data["serial"]
    base_name = data.get("base_name", f"EVSE {serial}")
    
    # Create the charging switch
    entities = [
        EVSEChargingSwitch(coordinator, client, serial, base_name),
    ]
    
    async_add_entities(entities)

class EVSEChargingSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to start/stop charging"""
    
    def __init__(self, coordinator, client, serial: str, base_name: str):
        super().__init__(coordinator)
        self.client = client
        self.serial = serial
        self._attr_name = f"{base_name} Charge"
        self._attr_unique_id = f"{serial}_charging"
        self._attr_icon = "mdi:power"

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
    
    @property
    def is_on(self) -> bool | None:
        """Return whether charging is active"""
        data = self.evse_data
        return data.get("state") == "CHARGING"
    
    @property
    def available(self) -> bool:
        """Return whether the switch is available"""
        data = self.evse_data
        return data.get("online", False) and data.get("logged_in", False)
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start charging"""
        # Use the built-in protection logic in the client
        # (Fallback to 16A instead of 32A if max_electricity not yet read)
        success = await self.client.start_charging(self.serial, amps=None, single_phase=False)
        if success:
            await self.coordinator.async_request_refresh()
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop charging"""
        success = await self.client.stop_charging(self.serial)
        if success:
            await self.coordinator.async_request_refresh()