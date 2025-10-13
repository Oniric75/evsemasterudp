"""
Client EVSE pour Home Assistant
"""
import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta

from .protocol import Communicator, EVSE, get_communicator

_LOGGER = logging.getLogger(__name__)

class EVSEClient:
    """Client pour communiquer avec les bornes EVSE via UDP"""
    
    def __init__(self, port: int = 28376):
        self.port = port
        self.communicator = get_communicator()
        self.running = False
        self.callbacks: Dict[str, Callable] = {}
        
        # Protection contre les changements rapides
        self._fast_change_protection: Dict[str, int] = {}  # serial -> minutes
        self._last_charge_change: Dict[str, datetime] = {}  # serial -> timestamp
        
    async def start(self):
        """Démarrer le client UDP"""
        if self.running:
            return
            
        try:
            await self.communicator.start()
            self.running = True
            
            # Ajouter notre callback pour les événements
            self.communicator.add_callback('evse_client', self._handle_evse_event)
            
            _LOGGER.info(f"Client EVSE démarré sur le port {self.port}")
            
        except Exception as e:
            _LOGGER.error(f"Erreur lors du démarrage du client EVSE: {e}")
            raise
    
    async def stop(self):
        """Arrêter le client"""
        self.running = False
        self.communicator.remove_callback('evse_client')
        await self.communicator.stop()
        _LOGGER.info("Client EVSE arrêté")
    
    async def _handle_evse_event(self, event: str, evse: EVSE):
        """Gérer les événements EVSE"""
        # Convertir l'EVSE en format compatible Home Assistant
        evse_data = self._evse_to_dict(evse)
        
        # Notifier nos callbacks
        for callback in self.callbacks.values():
            try:
                await callback(evse.info.serial, evse_data)
            except Exception as e:
                _LOGGER.error(f"Erreur dans le callback: {e}")
    
    def _evse_to_dict(self, evse: EVSE) -> Dict[str, Any]:
        """Convertir un objet EVSE en dictionnaire"""
        data = {
            'serial': evse.info.serial,
            'ip': evse.info.ip,
            'port': evse.info.port,
            'last_seen': evse.last_seen,
            'online': evse.is_online(),
            'logged_in': evse.is_logged_in(),
            'state': evse.get_meta_state(),
            
            # Informations de l'EVSE
            'brand': evse.info.brand,
            'model': evse.info.model,
            'hardware_version': evse.info.hardware_version,
            'software_version': evse.info.software_version,
            'max_power': evse.info.max_power,
            'max_electricity': evse.info.max_electricity,
            'phases': evse.info.phases,
            
            # Configuration
            'name': evse.config.name or 'EVSEMaster',
            'configured_max_electricity': evse.config.max_electricity,
            'temperature_unit': evse.config.temperature_unit,
        }
        
        # État électrique
        if evse.state:
            data.update({
                'current_power': evse.state.current_power,
                'voltage_l1': evse.state.l1_voltage,
                'voltage_l2': evse.state.l2_voltage,
                'voltage_l3': evse.state.l3_voltage,
                'current_l1': evse.state.l1_electricity,
                'current_l2': evse.state.l2_electricity,
                'current_l3': evse.state.l3_electricity,
                'temperature_inner': evse.state.inner_temp,
                'temperature_outer': evse.state.outer_temp,
                'gun_state': evse.state.gun_state,
                'output_state': evse.state.output_state,
                'errors': evse.state.errors,
            })
        else:
            # Valeurs par défaut si pas d'état
            data.update({
                'current_power': 0,
                'voltage_l1': 0,
                'voltage_l2': 0,
                'voltage_l3': 0,
                'current_l1': 0,
                'current_l2': 0,
                'current_l3': 0,
                'temperature_inner': 0,
                'temperature_outer': 0,
                'gun_state': 0,
                'output_state': 0,
                'errors': [],
            })
        
        # Session de charge
        if evse.current_charge:
            data.update({
                'charge_kwh': evse.current_charge.charge_kwh,
                'charge_id': evse.current_charge.charge_id,
                'start_date': evse.current_charge.start_date,
                'duration_seconds': evse.current_charge.duration_seconds,
                'charge_state': evse.current_charge.current_state,
            })
        else:
            data.update({
                'charge_kwh': 0,
                'charge_id': '',
                'start_date': None,
                'duration_seconds': 0,
                'charge_state': 0,
            })
        
        return data
    
    def add_callback(self, name: str, callback: Callable):
        """Ajouter un callback pour les changements d'état"""
        self.callbacks[name] = callback
    
    def remove_callback(self, name: str):
        """Supprimer un callback"""
        self.callbacks.pop(name, None)
    
    def get_evse(self, serial: str) -> Optional[Dict[str, Any]]:
        """Obtenir les données d'une EVSE"""
        evse = self.communicator.get_evse(serial)
        if evse:
            return self._evse_to_dict(evse)
        return None
    
    def get_all_evses(self) -> Dict[str, Dict[str, Any]]:
        """Obtenir toutes les EVSEs"""
        result = {}
        for serial, evse in self.communicator.get_all_evses().items():
            result[serial] = self._evse_to_dict(evse)
        return result
    
    async def login(self, serial: str, password: str) -> bool:
        """Se connecter à une EVSE"""
        evse = self.communicator.get_evse(serial)
        if not evse:
            _LOGGER.error(f"EVSE {serial} non trouvée")
            return False
        
        return await evse.login(password)
    
    async def start_charging(self, serial: str, amps: int = None, single_phase: bool = False) -> bool:
        """Démarrer la charge"""
        
        # Vérifier la protection contre les démarrages rapides
        if not self._can_start_charge(serial):
            return False
        
        evse = self.communicator.get_evse(serial)
        if not evse:
            _LOGGER.error(f"EVSE {serial} non trouvée")
            return False
        
        # Si aucun ampérage spécifié, utiliser une valeur sûre
        if amps is None:
            # Protection: Fallback à 16A au lieu de 32A si max_electricity pas encore lu
            # Ceci évite d'utiliser des valeurs trop élevées lors du premier démarrage
            if evse.config and evse.config.max_electricity > 0:
                # Utiliser la valeur configurée de l'EVSE
                amps = evse.config.max_electricity
            else:
                # Fallback de sécurité : 16A au lieu de 32A
                max_amps = evse.info.max_electricity if evse.info.max_electricity > 0 else 32
                amps = min(max_amps, 16)
        
        # Le démarrage est autorisé, pas besoin d'enregistrer (seuls les arrêts sont enregistrés)
        return await evse.charge_start(amps, single_phase)
    
    async def stop_charging(self, serial: str) -> bool:
        """Arrêter la charge"""
        evse = self.communicator.get_evse(serial)
        if not evse:
            _LOGGER.error(f"EVSE {serial} non trouvée")
            return False
        
        # Toujours autoriser l'arrêt (sécurité) mais enregistrer pour protection future
        result = await evse.charge_stop()
        
        # Enregistrer l'arrêt pour protéger le prochain démarrage
        if result:
            self._record_charge_state_change(serial)
            
        return result
    
    async def set_max_current(self, serial: str, amps: int) -> bool:
        """Définir le courant maximum"""
        evse = self.communicator.get_evse(serial)
        if not evse:
            _LOGGER.error(f"EVSE {serial} non trouvée")
            return False
        
        return await evse.set_max_electricity(amps)
    
    async def set_name(self, serial: str, name: str) -> bool:
        """Définir le nom de l'EVSE"""
        evse = self.communicator.get_evse(serial)
        if not evse:
            _LOGGER.error(f"EVSE {serial} non trouvée")
            return False
        
        return await evse.set_name(name)
    
    async def sync_time(self, serial: str) -> bool:
        """Synchroniser l'heure de l'EVSE"""
        evse = self.communicator.get_evse(serial)
        if not evse:
            _LOGGER.error(f"EVSE {serial} non trouvée")
            return False
        
        return await evse.sync_time()
    
    async def set_fast_change_protection(self, serial: str, minutes: int) -> None:
        """Définir la protection contre les changements rapides (en minutes)"""
        self._fast_change_protection[serial] = minutes
        _LOGGER.info(f"Protection changements rapides pour {serial}: {minutes} minutes")
    
    def get_fast_change_protection(self, serial: str) -> int:
        """Obtenir la protection actuelle (en minutes)

        Défaut ajusté à 1 minute (au lieu de 5) pour permettre une réactivité
        plus souple tout en évitant les cycles instantanés. L'utilisateur peut
        toujours augmenter la valeur via l'entité numérique ou désactiver (0).
        """
        return self._fast_change_protection.get(serial, 1)  # défaut 1 minute
    
    def _can_start_charge(self, serial: str) -> bool:
        """Vérifier si on peut démarrer la charge (protection anti-usure)"""
        protection_minutes = self.get_fast_change_protection(serial)
        
        # Si protection désactivée (0), autoriser
        if protection_minutes == 0:
            return True
        
        # Vérifier le délai depuis le dernier arrêt
        last_change = self._last_charge_change.get(serial)
        if last_change is None:
            return True
        
        time_since_last = datetime.now() - last_change
        min_interval = timedelta(minutes=protection_minutes)
        
        if time_since_last < min_interval:
            remaining = min_interval - time_since_last
            remaining_minutes = remaining.total_seconds() / 60
            _LOGGER.warning(
                f"Protection démarrage active pour {serial}: "
                f"attendre encore {remaining_minutes:.1f} minutes depuis le dernier arrêt "
                f"(protection: {protection_minutes} min)"
            )
            return False
        
        return True
    
    def _record_charge_state_change(self, serial: str) -> None:
        """Enregistrer un arrêt de charge (pour protéger le prochain démarrage)"""
        self._last_charge_change[serial] = datetime.now()
        _LOGGER.debug(f"Arrêt de charge enregistré pour {serial}")

    # --- Exposition utilitaire pour l'UI / capteurs ---
    def get_cooldown_remaining(self, serial: str) -> timedelta:
        """Retourner le temps restant avant qu'un nouveau démarrage soit autorisé.

        Retourne 0 si aucune protection active ou si délai déjà écoulé.
        """
        protection_minutes = self.get_fast_change_protection(serial)
        if protection_minutes == 0:
            return timedelta(0)
        last_change = self._last_charge_change.get(serial)
        if not last_change:
            return timedelta(0)
        min_interval = timedelta(minutes=protection_minutes)
        elapsed = datetime.now() - last_change
        remaining = min_interval - elapsed
        if remaining.total_seconds() < 0:
            return timedelta(0)
        return remaining

# Singleton pour partager l'instance entre les composants HA
_client_instance: Optional[EVSEClient] = None

def get_evse_client() -> EVSEClient:
    """Obtenir l'instance singleton du client EVSE"""
    global _client_instance
    if _client_instance is None:
        _client_instance = EVSEClient()
    return _client_instance