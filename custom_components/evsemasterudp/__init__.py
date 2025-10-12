"""
Intégration EVSE Master UDP pour Home Assistant
Support des bornes EVSE utilisant le protocole UDP EmProto (Morec et compatibles)
"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .evse_client import get_evse_client, EVSEClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "evsemasterudp"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]

# Intervalle de mise à jour (en secondes)
UPDATE_INTERVAL = timedelta(seconds=30)

class EVSEDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinateur pour mettre à jour les données EVSE"""

    def __init__(self, hass: HomeAssistant, client: EVSEClient) -> None:
        """Initialiser le coordinateur"""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self):
        """Récupérer les données des EVSEs"""
        try:
            # Récupérer toutes les EVSEs
            evses = self.client.get_all_evses()
            
            if not evses:
                _LOGGER.debug("Aucune EVSE trouvée")
                return {}
            
            _LOGGER.debug(f"Données EVSE mises à jour: {len(evses)} bornes trouvées")
            return evses
            
        except Exception as err:
            raise UpdateFailed(f"Erreur lors de la mise à jour des données EVSE: {err}")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurer l'intégration EVSE à partir d'une entrée de configuration"""
    
    # Récupérer les paramètres de configuration
    serial = entry.data.get("serial")
    password = entry.data.get("password")
    port = entry.data.get("port", 28376)
    
    _LOGGER.info(f"Configuration de l'EVSE {serial} sur le port {port}")
    
    # Obtenir le client EVSE
    client = get_evse_client()
    
    # Démarrer le client s'il n'est pas déjà démarré
    if not client.running:
        try:
            await client.start()
        except Exception as err:
            _LOGGER.error(f"Impossible de démarrer le client EVSE: {err}")
            return False
    
    # Attendre un peu pour découvrir les EVSEs
    await hass.async_add_executor_job(lambda: hass.loop.call_later(3, lambda: None))
    
    # Essayer de se connecter à l'EVSE configurée
    if serial and password:
        success = await client.login(serial, password)
        if success:
            _LOGGER.info(f"Connexion réussie à l'EVSE {serial}")
        else:
            _LOGGER.warning(f"Impossible de se connecter à l'EVSE {serial}")
    
    # Créer le coordinateur de données
    coordinator = EVSEDataUpdateCoordinator(hass, client)
    
    # Première mise à jour des données
    await coordinator.async_config_entry_first_refresh()
    
    # Stocker le coordinateur dans hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "serial": serial,
        "password": password,
    }
    
    # Configurer les plateformes (sensor, switch, number)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger l'intégration EVSE"""
    
    # Décharger les plateformes
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Nettoyer les données
        data = hass.data[DOMAIN].pop(entry.entry_id)
        
        # Arrêter le client s'il n'y a plus d'autres entrées
        if not hass.data[DOMAIN]:
            client = data["client"]
            await client.stop()
    
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recharger l'intégration EVSE"""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)