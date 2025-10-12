"""
Communicateur UDP pour les EVSEs EmProto
"""
import asyncio
import socket
import struct
import logging
from typing import Dict, Optional, Callable, Any, List
from datetime import datetime, timedelta

from .datagram import Datagram, parse_datagrams
from .datagrams import (
    RequestLogin, LoginConfirm, PasswordErrorResponse,
    Heading, HeadingResponse, SingleACStatus, SingleACStatusResponse,
    CurrentChargeRecord, RequestChargeStatusRecord, ChargeStart, ChargeStop,
    SetAndGetOutputElectricity, SetAndGetNickName, SetAndGetSystemTime,
    UnknownCommand341
)

_LOGGER = logging.getLogger(__name__)

class EVSEInfo:
    """Informations sur une EVSE"""
    def __init__(self, serial: str, ip: str, port: int):
        self.serial = serial
        self.ip = ip
        self.port = port
        self.brand = "EVSE"
        self.model = ""
        self.hardware_version = ""
        self.software_version = ""
        self.max_power = 0
        self.max_electricity = 32
        self.hot_line = ""
        self.phases = 1
        self.can_force_single_phase = False
        self.feature = 0
        self.support_new = 0

class EVSEConfig:
    """Configuration d'une EVSE"""
    def __init__(self):
        self.name = ""
        self.language = 254
        self.offline_charge = 0
        self.max_electricity = 6
        self.temperature_unit = 1

class EVSEState:
    """État électrique d'une EVSE"""
    def __init__(self):
        self.current_power = 0.0
        self.current_amount = 0.0
        self.l1_voltage = 0.0
        self.l1_electricity = 0.0
        self.l2_voltage = 0.0
        self.l2_electricity = 0.0
        self.l3_voltage = 0.0
        self.l3_electricity = 0.0
        self.inner_temp = 0.0
        self.outer_temp = 0.0
        self.current_state = 0
        self.gun_state = 0
        self.output_state = 0
        self.errors = []

class EVSECurrentCharge:
    """Session de charge en cours"""
    def __init__(self):
        self.port = 1
        self.current_state = 0
        self.charge_id = ""
        self.start_type = 0
        self.charge_type = 0
        self.reservation_date = datetime.fromtimestamp(0)
        self.user_id = ""
        self.max_electricity = 0
        self.start_date = datetime.fromtimestamp(0)
        self.duration_seconds = 0
        self.start_kwh_counter = 0.0
        self.current_kwh_counter = 0.0
        self.charge_kwh = 0.0
        self.charge_price = 0.0
        self.fee_type = 0
        self.charge_fee = 0.0

class EVSE:
    """Représentation d'une EVSE"""
    
    def __init__(self, communicator: 'Communicator', serial: str, ip: str, port: int):
        self.communicator = communicator
        self.info = EVSEInfo(serial, ip, port)
        self.config = EVSEConfig()
        self.state: Optional[EVSEState] = None
        self.current_charge: Optional[EVSECurrentCharge] = None
        
        self.last_seen = datetime.now()
        self.last_active_login: Optional[datetime] = None
        self.password: Optional[str] = None
        self._logged_in = False
        
        # États possibles selon le protocole
        self.GUN_STATES = {
            0: "DISCONNECTED",
            1: "CONNECTED_LOCKED", 
            2: "CONNECTED_UNLOCKED"
        }
        
        self.OUTPUT_STATES = {
            0: "IDLE",
            1: "CHARGING"
        }
    
    def update_ip(self, ip: str, port: int) -> bool:
        """Mettre à jour l'IP et le port"""
        self.last_seen = datetime.now()
        changed = False
        
        if ip != self.info.ip:
            self.info.ip = ip
            changed = True
        
        if port != self.info.port:
            self.info.port = port
            changed = True
        
        return changed
    
    def is_online(self) -> bool:
        """Vérifier si l'EVSE est en ligne"""
        # Considérer offline après 30 secondes sans message
        return (datetime.now() - self.last_seen).total_seconds() < 30
    
    def is_logged_in(self) -> bool:
        """Vérifier si on est connecté à l'EVSE"""
        return self._logged_in and self.is_online()
    
    def get_meta_state(self) -> str:
        """Obtenir l'état méta de l'EVSE"""
        if not self.is_online():
            return "OFFLINE"
        if not self.is_logged_in():
            return "NOT_LOGGED_IN"
        if not self.state:
            return "IDLE"
        if self.state.errors:
            return "ERROR"
        if self.state.output_state == 1:  # CHARGING
            return "CHARGING"
        if self.state.gun_state != 0:  # Not DISCONNECTED
            return "PLUGGED_IN"
        return "IDLE"
    
    async def send_datagram(self, datagram: Datagram) -> int:
        """Envoyer un datagramme à l'EVSE"""
        if isinstance(datagram, HeadingResponse):
            self.last_active_login = datetime.now()
        
        return await self.communicator.send(datagram, self)
    
    async def login(self, password: str) -> bool:
        """Se connecter à l'EVSE"""
        try:
            self.password = password
            
            # Envoyer RequestLogin avec le mot de passe
            login_request = RequestLogin()
            login_request.set_device_serial(self.info.serial)
            login_request.set_device_password(password)
            
            await self.send_datagram(login_request)
            
            # Attendre un peu pour la réponse
            await asyncio.sleep(1)
            
            # Si on a reçu des infos de login, on est connecté
            if self.info.model:  # Rempli lors du login
                self._logged_in = True
                _LOGGER.info(f"Connexion réussie à {self.info.serial}")
                
                # Demander l'état actuel
                await self.send_datagram(RequestChargeStatusRecord())
                return True
            else:
                _LOGGER.error(f"Échec de connexion à {self.info.serial}")
                return False
                
        except Exception as e:
            _LOGGER.error(f"Erreur lors de la connexion: {e}")
            return False
    
    async def charge_start(self, max_amps: int = 6, single_phase: bool = False, 
                          user_id: str = "", charge_id: str = "") -> bool:
        """Démarrer la charge"""
        if not self.is_logged_in():
            raise RuntimeError("Non connecté à l'EVSE")
        
        try:
            charge_start = ChargeStart()
            charge_start.set_device_serial(self.info.serial)
            charge_start.set_device_password(self.password)
            charge_start.set_max_electricity(max_amps)
            charge_start.set_single_phase(single_phase)
            
            if user_id:
                charge_start.set_user_id(user_id)
            if charge_id:
                charge_start.set_charge_id(charge_id)
            else:
                # Générer un ID unique
                import time
                charge_start.set_charge_id(f"{int(time.time())}")
            
            await self.send_datagram(charge_start)
            _LOGGER.info(f"Commande de charge envoyée: {max_amps}A")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erreur lors du démarrage de charge: {e}")
            return False
    
    async def charge_stop(self, user_id: str = "") -> bool:
        """Arrêter la charge"""
        if not self.is_logged_in():
            raise RuntimeError("Non connecté à l'EVSE")
        
        try:
            charge_stop = ChargeStop()
            charge_stop.set_device_serial(self.info.serial)
            charge_stop.set_device_password(self.password)
            charge_stop.user_id = user_id
            
            await self.send_datagram(charge_stop)
            _LOGGER.info("Commande d'arrêt de charge envoyée")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erreur lors de l'arrêt de charge: {e}")
            return False
    
    async def set_max_electricity(self, amps: int) -> bool:
        """Définir le courant maximum"""
        if not self.is_logged_in():
            raise RuntimeError("Non connecté à l'EVSE")
        
        try:
            set_current = SetAndGetOutputElectricity()
            set_current.set_device_serial(self.info.serial)
            set_current.set_device_password(self.password)
            set_current.max_electricity = amps
            
            await self.send_datagram(set_current)
            self.config.max_electricity = amps
            _LOGGER.info(f"Courant maximum défini à {amps}A")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erreur lors de la configuration: {e}")
            return False
    
    async def set_name(self, name: str) -> bool:
        """Définir le nom de l'EVSE"""
        if not self.is_logged_in():
            raise RuntimeError("Non connecté à l'EVSE")
        
        try:
            set_name = SetAndGetNickName()
            set_name.set_device_serial(self.info.serial)
            set_name.set_device_password(self.password)
            set_name.name = name
            
            await self.send_datagram(set_name)
            self.config.name = name
            _LOGGER.info(f"Nom défini à: {name}")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erreur lors de la configuration du nom: {e}")
            return False
    
    async def sync_time(self) -> bool:
        """Synchroniser l'heure de l'EVSE"""
        if not self.is_logged_in():
            raise RuntimeError("Non connecté à l'EVSE")
        
        try:
            sync_time = SetAndGetSystemTime()
            sync_time.set_device_serial(self.info.serial)
            sync_time.set_device_password(self.password)
            
            await self.send_datagram(sync_time)
            _LOGGER.info("Heure synchronisée")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erreur lors de la synchronisation: {e}")
            return False

class Communicator:
    """Communicateur UDP principal"""
    
    def __init__(self, port: int = 28376):
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.evses: Dict[str, EVSE] = {}
        self.callbacks: Dict[str, Callable] = {}
        self._periodic_task: Optional[asyncio.Task] = None
    
    async def start(self) -> int:
        """Démarrer le communicateur"""
        if self.running:
            return self.port
        
        try:
            # Créer le socket UDP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', self.port))
            
            # Activer le broadcast si possible
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except OSError:
                _LOGGER.warning("Broadcast non supporté")
            
            self.running = True
            _LOGGER.info(f"Communicateur démarré sur le port {self.port}")
            
            # Démarrer les tâches asyncio
            asyncio.create_task(self._listen_loop())
            self._periodic_task = asyncio.create_task(self._periodic_checks())
            
            return self.port
            
        except Exception as e:
            _LOGGER.error(f"Erreur lors du démarrage: {e}")
            raise
    
    async def stop(self):
        """Arrêter le communicateur"""
        self.running = False
        
        if self._periodic_task:
            self._periodic_task.cancel()
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        _LOGGER.info("Communicateur arrêté")
    
    async def _listen_loop(self):
        """Boucle d'écoute UDP"""
        while self.running and self.socket:
            try:
                await asyncio.sleep(0.01)  # Éviter de bloquer
                
                try:
                    # Vérifier que le socket existe encore
                    if not self.socket:
                        break
                        
                    data, addr = self.socket.recvfrom(1024)
                    await self._handle_message(data, addr)
                except socket.error:
                    # Pas de données disponibles
                    continue
                    
            except Exception as e:
                if self.running and self.socket:  # Ne logger que si on devrait encore tourner
                    _LOGGER.error(f"Erreur dans la boucle d'écoute: {e}")
                await asyncio.sleep(1)
        
        _LOGGER.debug("Boucle d'écoute UDP terminée")
    
    async def _handle_message(self, data: bytes, addr: tuple):
        """Traiter un message reçu"""
        try:
            datagrams = parse_datagrams(data)
            
            for datagram in datagrams:
                await self._process_datagram(datagram, addr)
                
        except Exception as e:
            _LOGGER.debug(f"Erreur lors du traitement du message: {e}")
    
    async def _process_datagram(self, datagram: Datagram, addr: tuple):
        """Traiter un datagramme reçu"""
        ip, port = addr
        serial = datagram.get_device_serial()
        
        if not serial:
            return
        
        # Obtenir ou créer l'EVSE
        evse = self.evses.get(serial)
        if not evse:
            evse = EVSE(self, serial, ip, port)
            self.evses[serial] = evse
            _LOGGER.info(f"Nouvelle EVSE découverte: {serial} @ {ip}")
            await self._notify_callbacks('evse_added', evse)
        else:
            # Mettre à jour l'IP si changée
            if evse.update_ip(ip, port):
                await self._notify_callbacks('evse_changed', evse)
        
        # Traiter le datagramme spécifique
        if isinstance(datagram, RequestLogin):
            await self._handle_login(evse, datagram)
        elif isinstance(datagram, SingleACStatus):
            await self._handle_status(evse, datagram)
        elif isinstance(datagram, CurrentChargeRecord):
            await self._handle_charge_record(evse, datagram)
        elif isinstance(datagram, Heading):
            await self._handle_heading(evse, datagram)
        elif isinstance(datagram, PasswordErrorResponse):
            _LOGGER.error(f"Erreur de mot de passe pour {serial}")
            evse._logged_in = False
        elif isinstance(datagram, UnknownCommand341):
            _LOGGER.debug(f"Commande 341 reçue de {serial}, données: {datagram.raw_data.hex()}")
            # Pas de traitement spécial nécessaire pour l'instant
    
    async def _handle_login(self, evse: EVSE, datagram: RequestLogin):
        """Traiter une réponse de login"""
        evse.info.brand = datagram.brand
        evse.info.model = datagram.model
        evse.info.hardware_version = datagram.hardware_version
        evse.info.software_version = datagram.software_version
        evse.info.max_power = datagram.max_power
        evse.info.max_electricity = datagram.max_electricity
        evse.info.hot_line = datagram.hot_line
        evse.info.phases = datagram.phases
        evse.info.can_force_single_phase = datagram.can_force_single_phase
        evse.info.feature = datagram.feature
        evse.info.support_new = datagram.support_new
        
        # Confirmer le login
        confirm = LoginConfirm()
        confirm.set_device_serial(evse.info.serial)
        confirm.set_device_password(evse.password)
        await evse.send_datagram(confirm)
        
        evse._logged_in = True
        await self._notify_callbacks('evse_logged_in', evse)
    
    async def _handle_status(self, evse: EVSE, datagram: SingleACStatus):
        """Traiter un status AC"""
        if not evse.state:
            evse.state = EVSEState()
        
        evse.state.current_power = datagram.current_power
        evse.state.current_amount = datagram.current_amount
        evse.state.l1_voltage = datagram.l1_voltage
        evse.state.l1_electricity = datagram.l1_electricity
        evse.state.l2_voltage = datagram.l2_voltage
        evse.state.l2_electricity = datagram.l2_electricity
        evse.state.l3_voltage = datagram.l3_voltage
        evse.state.l3_electricity = datagram.l3_electricity
        evse.state.inner_temp = datagram.inner_temp
        evse.state.outer_temp = datagram.outer_temp
        evse.state.current_state = datagram.current_state
        evse.state.gun_state = datagram.gun_state
        evse.state.output_state = datagram.output_state
        evse.state.errors = datagram.errors
        
        # Répondre au status
        response = SingleACStatusResponse()
        response.set_device_serial(evse.info.serial)
        response.set_device_password(evse.password)
        await evse.send_datagram(response)
        
        await self._notify_callbacks('evse_state_changed', evse)
    
    async def _handle_charge_record(self, evse: EVSE, datagram: CurrentChargeRecord):
        """Traiter un enregistrement de charge"""
        if not evse.current_charge:
            evse.current_charge = EVSECurrentCharge()
        
        evse.current_charge.port = datagram.port
        evse.current_charge.current_state = datagram.current_state
        evse.current_charge.charge_id = datagram.charge_id
        evse.current_charge.start_type = datagram.start_type
        evse.current_charge.charge_type = datagram.charge_type
        evse.current_charge.reservation_date = datagram.reservation_date
        evse.current_charge.user_id = datagram.user_id
        evse.current_charge.max_electricity = datagram.max_electricity
        evse.current_charge.start_date = datagram.start_date
        evse.current_charge.duration_seconds = datagram.duration_seconds
        evse.current_charge.start_kwh_counter = datagram.start_kwh_counter
        evse.current_charge.current_kwh_counter = datagram.current_kwh_counter
        evse.current_charge.charge_kwh = datagram.charge_kwh
        evse.current_charge.charge_price = datagram.charge_price
        evse.current_charge.fee_type = datagram.fee_type
        evse.current_charge.charge_fee = datagram.charge_fee
        
        await self._notify_callbacks('evse_charge_changed', evse)
    
    async def _handle_heading(self, evse: EVSE, datagram: Heading):
        """Traiter un heading (keepalive)"""
        # Répondre pour maintenir la session
        response = HeadingResponse()
        response.set_device_serial(evse.info.serial)
        response.set_device_password(evse.password)
        await evse.send_datagram(response)
    
    async def send(self, datagram: Datagram, evse: EVSE) -> int:
        """Envoyer un datagramme"""
        if not self.running:
            raise RuntimeError("Communicateur non démarré")
        
        # Définir le serial et password si pas encore fait
        if not datagram.get_device_serial():
            datagram.set_device_serial(evse.info.serial)
        
        if datagram.get_device_password() is None and evse.password:
            datagram.set_device_password(evse.password)
        
        buffer = datagram.pack()
        
        # Envoyer via le socket
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            self.socket.sendto, 
            buffer, 
            (evse.info.ip, evse.info.port)
        )
        
        return len(buffer)
    
    async def _periodic_checks(self):
        """Vérifications périodiques"""
        while self.running:
            try:
                await asyncio.sleep(5)
                
                for evse in self.evses.values():
                    # Vérifier si on doit se reconnecter
                    if evse.is_logged_in() and evse.last_active_login:
                        time_since_login = datetime.now() - evse.last_active_login
                        if time_since_login.total_seconds() > 30:
                            # Relancer le login
                            if evse.password:
                                await evse.login(evse.password)
                    
                    # Demander l'état régulièrement
                    if evse.is_logged_in():
                        await evse.send_datagram(RequestChargeStatusRecord())
                
            except Exception as e:
                _LOGGER.error(f"Erreur dans les vérifications périodiques: {e}")
    
    async def _notify_callbacks(self, event: str, evse: EVSE):
        """Notifier les callbacks"""
        for callback in self.callbacks.values():
            try:
                await callback(event, evse)
            except Exception as e:
                _LOGGER.error(f"Erreur dans le callback: {e}")
    
    def add_callback(self, name: str, callback: Callable):
        """Ajouter un callback"""
        self.callbacks[name] = callback
    
    def remove_callback(self, name: str):
        """Supprimer un callback"""
        self.callbacks.pop(name, None)
    
    def get_evse(self, serial: str) -> Optional[EVSE]:
        """Obtenir une EVSE par son numéro de série"""
        return self.evses.get(serial)
    
    def get_all_evses(self) -> Dict[str, EVSE]:
        """Obtenir toutes les EVSEs"""
        return self.evses.copy()
    
    def close(self):
        """Fermer le communicateur et libérer les ressources"""
        _LOGGER.debug("Fermeture du communicateur UDP")
        
        # Arrêter la boucle d'écoute
        self.running = False
        
        # Fermer le socket
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                _LOGGER.debug(f"Erreur lors de la fermeture du socket: {e}")
            finally:
                self.socket = None
        
        # Annuler la tâche d'écoute si elle existe
        if hasattr(self, '_listen_task') and self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
        
        _LOGGER.debug("Communicateur UDP fermé")

# Singleton global
_communicator_instance: Optional[Communicator] = None

def get_communicator() -> Communicator:
    """Obtenir l'instance singleton du communicateur"""
    global _communicator_instance
    if _communicator_instance is None:
        _communicator_instance = Communicator()
    return _communicator_instance