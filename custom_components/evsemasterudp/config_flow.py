"""Config flow pour l'intégration EVSE Master UDP"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .evse_client import get_evse_client

_LOGGER = logging.getLogger(__name__)

DOMAIN = "evsemasterudp"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("serial"): str,
        vol.Required("password"): str,
        vol.Optional("port", default=28376): int,
        vol.Optional("name", default="EVSE"): str,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestionnaire du flux de configuration pour EVSE EmProto"""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Gérer l'étape initiale de configuration par l'utilisateur"""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Valider la configuration
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Erreur inattendue")
                errors["base"] = "unknown"
            else:
                # Créer l'entrée de configuration
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Valider les données d'entrée utilisateur"""
    
    serial = data["serial"]
    password = data["password"]
    port = data.get("port", 28376)
    
    # Obtenir le client EVSE
    client = get_evse_client()
    
    # Démarrer le client temporairement pour tester
    was_running = client.running
    if not was_running:
        try:
            await client.start()
        except Exception as err:
            _LOGGER.error(f"Impossible de démarrer le client EVSE: {err}")
            raise CannotConnect
    
    try:
        # Attendre plus longtemps pour découvrir les EVSEs (comme test_full.py)
        import asyncio
        await asyncio.sleep(5)
        
        # Vérifier si l'EVSE est trouvée - Retry en cas d'échec
        evse = client.get_evse(serial)
        if not evse:
            # Retry après 2 secondes supplémentaires
            _LOGGER.warning(f"EVSE {serial} non trouvée, nouvelle tentative...")
            await asyncio.sleep(2)
            evse = client.get_evse(serial)
            
        if not evse:
            _LOGGER.error(f"EVSE {serial} non trouvée après 7 secondes")
            raise CannotConnect
        
        _LOGGER.info(f"EVSE {serial} trouvée, tentative de connexion...")
        
        # Tester la connexion avec retry
        success = await client.login(serial, password)
        if not success:
            # Un seul retry pour éviter de bloquer l'EVSE
            _LOGGER.warning(f"Première tentative d'auth échouée pour {serial}, retry...")
            await asyncio.sleep(2)
            success = await client.login(serial, password)
            
        if not success:
            raise InvalidAuth
        
        _LOGGER.info(f"Connexion réussie à l'EVSE {serial}")
        
        return {
            "title": f"EVSE {serial}",
            "serial": serial,
        }
        
    finally:
        # Arrêter le client s'il n'était pas démarré avant
        if not was_running:
            await client.stop()

class CannotConnect(HomeAssistantError):
    """Erreur pour indiquer qu'on ne peut pas se connecter"""

class InvalidAuth(HomeAssistantError):
    """Erreur pour indiquer une authentification invalide"""