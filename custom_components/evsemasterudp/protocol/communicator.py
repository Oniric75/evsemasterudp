"""
UDP Communicator for EmProto EVSEs
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
    SetAndGetOutputElectricity, SetAndGetOutputElectricityResponse,
    Login, LoginResponse, SingleACChargingStatusPublicAuto, SingleACChargingStatusResponse
)

_LOGGER = logging.getLogger(__name__)

class EVSEInfo:
    """Information about an EVSE"""
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
        self.device_id = ""  # Device ID extracted from command 0x010c

class EVSEConfig:
    """EVSE configuration"""
    def __init__(self):
        self.name = ""
        self.language = 254
        self.offline_charge = 0
        self.max_electricity = 6
        self.temperature_unit = 1

class EVSEState:
    """Electrical state of an EVSE"""
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
    """Current charging session"""
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
    """Representation of an EVSE"""
    
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
        self._last_response = None  # To wait for authentication responses
        
        # Possible states according to the protocol
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
        """Update IP and port"""
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
        """Check if the EVSE is online"""
        # Consider offline after 90 seconds (adjusted for 60s poll interval)
        return (datetime.now() - self.last_seen).total_seconds() < 90
    
    def is_logged_in(self) -> bool:
        """Check if logged in to the EVSE"""
        return self._logged_in and self.is_online()
    
    def get_meta_state(self) -> str:
        """Get the meta state of the EVSE"""
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

        # Align with TypeScript reference mapping:
        # 0 = unknown, 1 = disconnected, 2 = connected (unlocked), 3 = negotiating?, 4 = connected locked.
        gun_state = getattr(self.state, "gun_state", 0)
        if gun_state in (2, 3, 4):
            return "PLUGGED_IN"
        return "IDLE"
    
    async def send_datagram(self, datagram: Datagram) -> int:
        """Send a datagram to the EVSE"""
        if isinstance(datagram, HeadingResponse):
            self.last_active_login = datetime.now()
        
        return await self.communicator.send(datagram, self)
    
    async def login(self, password: str) -> bool:
        """Log in to the EVSE following the TypeScript sequence"""
        try:
            _LOGGER.info(f"Attempting to connect to {self.info.serial} with password")
            
            # 0. Reset connection state before starting
            self._logged_in = False
            self.last_active_login = None
            
            # 1. Send RequestLogin with password
            login_request = RequestLogin()
            login_request.set_device_serial(self.info.serial)
            login_request.set_device_password(password)
            
            await self.send_datagram(login_request)
            _LOGGER.debug(f"RequestLogin sent to {self.info.serial}")
            
            # 2. Wait for LoginResponse or PasswordErrorResponse (max 3 seconds)
            response = await self._wait_for_response([LoginResponse.COMMAND, PasswordErrorResponse.COMMAND], 3.0)
            
            if response and response.get_command() == PasswordErrorResponse.COMMAND:
                _LOGGER.error(f"Incorrect password for {self.info.serial}")
                return False
            
            if not response or response.get_command() != LoginResponse.COMMAND:
                _LOGGER.error(f"No login response from {self.info.serial}")
                return False
            
            # 3. Password correct, save and send LoginConfirm
            self.password = password
            _LOGGER.info(f"Password accepted for {self.info.serial}")
            
            # 4. Send LoginConfirm to finalize
            login_confirm = LoginConfirm()
            login_confirm.set_device_serial(self.info.serial)
            login_confirm.set_device_password(password)
            
            await self.send_datagram(login_confirm)
            _LOGGER.debug(f"LoginConfirm sent to {self.info.serial}")
            
            # 5. Mark as connected
            self._logged_in = True
            self.last_active_login = datetime.now()
            _LOGGER.info(f"Connection established with {self.info.serial}")
            
            # 6. Request configuration (like TypeScript)
            try:
                await self._fetch_config()
            except Exception as e:
                _LOGGER.warning(f"Unable to retrieve config for {self.info.serial}: {e}")
            
            return True
                
        except Exception as e:
            _LOGGER.error(f"Error while connecting to {self.info.serial}: {e}")
            return False
    
    async def _wait_for_response(self, expected_commands: list, timeout: float):
        """Wait for a response with specific commands"""
        start_time = asyncio.get_event_loop().time()
        
    # Ignore any previous response by resetting to zero
        self._last_response = None
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if a new response with an expected command was received
            if self._last_response and self._last_response.get_command() in expected_commands:
                response = self._last_response
                self._last_response = None  # Consume the response
                return response
            
            await asyncio.sleep(0.1)
        
        return None
    
    async def _fetch_config(self):
        """Fetch the EVSE configuration"""
        # Send a status request to retrieve data
        heading = Heading()
        heading.set_device_serial(self.info.serial)
        heading.set_device_password(self.password)
        await self.send_datagram(heading)
        _LOGGER.debug(f"Configuration request sent to {self.info.serial}")
    
    async def charge_start(self, max_amps: int = 6, single_phase: bool = False, 
                          user_id: str = "", charge_id: str = "") -> bool:
        """Start charging"""
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
                # Generate a unique ID
                import time
                charge_start.set_charge_id(f"{int(time.time())}")
            
            await self.send_datagram(charge_start)
            _LOGGER.info(f"Charge command sent: {max_amps}A")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Error while starting charge: {e}")
            return False
    
    async def charge_stop(self, user_id: str = "") -> bool:
        """Stop charging"""
        if not self.is_logged_in():
            raise RuntimeError("Non connecté à l'EVSE")
        
        try:
            charge_stop = ChargeStop()
            charge_stop.set_device_serial(self.info.serial)
            charge_stop.set_device_password(self.password)
            charge_stop.user_id = user_id
            
            await self.send_datagram(charge_stop)
            _LOGGER.info("Charge stop command sent")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Error while stopping charge: {e}")
            return False
    
    async def set_max_electricity(self, amps: int) -> bool:
        """Set the maximum current"""
        if not self.is_logged_in():
            _LOGGER.error(f"EVSE {self.info.serial} not connected")
            return False
        
        try:
            _LOGGER.info(f"Setting max current to {amps}A for {self.info.serial}")
            
            set_current = SetAndGetOutputElectricity()
            set_current.set_device_serial(self.info.serial)
            set_current.set_device_password(self.password)
            set_current.action = 1  # SET action
            set_current.electricity = amps
            
            await self.send_datagram(set_current)
            _LOGGER.debug(f"SetAndGetOutputElectricity sent to {self.info.serial}")
            
            # Wait for SetAndGetOutputElectricityResponse
            response = await self._wait_for_response([SetAndGetOutputElectricityResponse.COMMAND], 5.0)
            
            if not response:
                _LOGGER.error(f"No response for set_max_electricity from {self.info.serial}")
                return False
                
            if hasattr(response, 'electricity') and response.electricity == amps:
                self.config.max_electricity = amps
                _LOGGER.info(f"Max current confirmed at {amps}A for {self.info.serial}")
                return True
            else:
                _LOGGER.error(f"Current not confirmed: requested {amps}A, received {getattr(response, 'electricity', 'unknown')}")
                return False
            
        except Exception as e:
            _LOGGER.error(f"Error while setting current for {self.info.serial}: {e}")
            return False
    
    async def set_name(self, name: str) -> bool:
        """Set the EVSE name"""
        if not self.is_logged_in():
            raise RuntimeError("Non connecté à l'EVSE")
        
        try:
            # TODO: Reimplement SetAndGetNickName
            # set_name = SetAndGetNickName()
            # set_name.set_device_serial(self.info.serial)
            # set_name.set_device_password(self.password)
            # set_name.name = name
            # await self.send_datagram(set_name)
            # self.config.name = name
            _LOGGER.info(f"Name configuration to be implemented: {name}")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Error while setting name: {e}")
            return False
    
    async def sync_time(self) -> bool:
        """Synchronize EVSE time"""
        if not self.is_logged_in():
            raise RuntimeError("Non connecté à l'EVSE")
        
        try:
            # TODO: Reimplement SetAndGetSystemTime
            # sync_time = SetAndGetSystemTime()
            # sync_time.set_device_serial(self.info.serial)
            # sync_time.set_device_password(self.password)
            # await self.send_datagram(sync_time)
            _LOGGER.info("Time synchronization to be implemented")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Error during synchronization: {e}")
            return False

class Communicator:
    """Main UDP communicator"""
    
    def __init__(self, port: int = 28376):
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.evses: Dict[str, EVSE] = {}
        self.callbacks: Dict[str, Callable] = {}
        self._periodic_task: Optional[asyncio.Task] = None
    
    async def start(self) -> int:
        """Start the communicator"""
        if self.running:
            return self.port
        
        try:
            # Create the UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', self.port))
            
            # Enable broadcast if possible
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except OSError:
                _LOGGER.warning("Broadcast not supported")
            
            self.running = True
            _LOGGER.info(f"Communicator started on port {self.port}")
            
            # Start asyncio tasks
            asyncio.create_task(self._listen_loop())
            self._periodic_task = asyncio.create_task(self._periodic_checks())
            
            return self.port
            
        except Exception as e:
            _LOGGER.error(f"Erreur lors du démarrage: {e}")
            raise
    
    async def stop(self):
        """Stop the communicator"""
        self.running = False
        
        if self._periodic_task:
            self._periodic_task.cancel()
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        _LOGGER.info("Communicator stopped")
    
    async def _listen_loop(self):
        """UDP listen loop"""
        while self.running and self.socket:
            try:
                await asyncio.sleep(0.01)  # Avoid blocking
                
                try:
                    # Check that the socket still exists
                    if not self.socket:
                        break
                        
                    data, addr = self.socket.recvfrom(1024)
                    await self._handle_message(data, addr)
                except socket.error:
                    # No data available
                    continue
                    
            except Exception as e:
                if self.running and self.socket:  # Only log if we should still be running
                    _LOGGER.error(f"Error in listen loop: {e}")
                await asyncio.sleep(1)
        
        _LOGGER.debug("UDP listen loop ended")
    
    async def _handle_message(self, data: bytes, addr: tuple):
        """Handle a received message"""
        try:
            datagrams = parse_datagrams(data)
            
            for datagram in datagrams:
                await self._process_datagram(datagram, addr)
                
        except Exception as e:
            _LOGGER.debug(f"Error while handling message: {e}")
    
    async def _process_datagram(self, datagram: Datagram, addr: tuple):
        """Handle a received datagram"""
        ip, port = addr
        serial = datagram.get_device_serial()
        
        if not serial:
            return
        
        # Get or create the EVSE
        evse = self.evses.get(serial)
        if not evse:
            evse = EVSE(self, serial, ip, port)
            self.evses[serial] = evse
            _LOGGER.info(f"New EVSE discovered: {serial} @ {ip}")
            await self._notify_callbacks('evse_added', evse)
        else:
            # Update IP if changed
            if evse.update_ip(ip, port):
                await self._notify_callbacks('evse_changed', evse)
        # Update last_seen and store the response for authentication
        evse.last_seen = datetime.now()
        evse._last_response = datagram  # Store for _wait_for_response
        # Handle the specific datagram
        if isinstance(datagram, Login):
            await self._handle_login(evse, datagram)
        elif isinstance(datagram, LoginResponse):
            await self._handle_login_response(evse, datagram)
        elif isinstance(datagram, SingleACStatus):
            await self._handle_status(evse, datagram)
        elif isinstance(datagram, SingleACChargingStatusPublicAuto):
            await self._handle_charging_status(evse, datagram)
        # elif isinstance(datagram, EVSERealTimeStatus):
        #     await self._handle_realtime_status(evse, datagram)
        # elif isinstance(datagram, EVSECurrentConfiguration):
        #     await self._handle_current_configuration(evse, datagram)
        elif isinstance(datagram, CurrentChargeRecord):
            await self._handle_charge_record(evse, datagram)
        elif isinstance(datagram, Heading):
            await self._handle_heading(evse, datagram)
        elif isinstance(datagram, SetAndGetOutputElectricityResponse):
            await self._handle_output_electricity_response(evse, datagram)
        elif isinstance(datagram, PasswordErrorResponse):
            # PasswordErrorResponses are handled in the login() method via _wait_for_response
            # Ignore those arriving here to avoid misleading error logs
            _LOGGER.debug(f"PasswordErrorResponse received for {serial} (handled by auth logic)")
        # elif isinstance(datagram, UnknownCommand341):
        #     _LOGGER.debug(f"Commande 341 reçue de {serial}, données: {datagram.raw_data.hex()}")
        #     # Pas de traitement spécial nécessaire pour l'instant
    
    async def _handle_login_response(self, evse: EVSE, datagram: LoginResponse):
        """Handle a successful login response (0x0002)"""
        _LOGGER.info(f"LoginResponse received from {evse.info.serial}")
        # This response indicates the password was correct
        # The real login will be completed by LoginConfirm in the login() method
    
    async def _handle_login(self, evse: EVSE, datagram: Login):
        """Handle an EVSE discovery broadcast"""
        evse.info.brand = datagram.brand
        evse.info.model = datagram.model
        evse.info.hardware_version = datagram.hardware_version
        evse.info.software_version = datagram.hardware_version  # Use hardware_version as fallback
        evse.info.max_power = datagram.max_power
        evse.info.max_electricity = datagram.max_electricity
        evse.info.hot_line = datagram.hot_line
        evse.info.phases = datagram.phases
        evse.info.can_force_single_phase = datagram.can_force_single_phase
        evse.info.feature = datagram.feature
        evse.info.support_new = datagram.support_new
        # Confirm login
        confirm = LoginConfirm()
        confirm.set_device_serial(evse.info.serial)
        confirm.set_device_password(evse.password)
        await evse.send_datagram(confirm)
        evse._logged_in = True
        await self._notify_callbacks('evse_logged_in', evse)
    
    async def _handle_status(self, evse: EVSE, datagram: SingleACStatus):
        """Handle an AC status"""
        if not evse.state:
            evse.state = EVSEState()
        
        # Copy data from SingleACStatus to EVSEState
        evse.state.current_power = datagram.current_power
        evse.state.current_amount = datagram.total_kwh_counter  # Corriger le mapping
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
        _LOGGER.debug(f"Status received for {evse.info.serial}: L1={datagram.l1_voltage}V, Temp={datagram.inner_temp}°C")
        # Respond to status
        response = SingleACStatusResponse()
        response.set_device_serial(evse.info.serial)
        response.set_device_password(evse.password)
        await evse.send_datagram(response)
        await self._notify_callbacks('evse_state_changed', evse)
    
    async def _handle_charging_status(self, evse: EVSE, datagram: SingleACChargingStatusPublicAuto):
        """Handle automatic AC charging status (command 0x0005)"""
        _LOGGER.debug(f"Charge status received for {evse.info.serial}")
        # Update charge information if available
        if not evse.current_charge:
            evse.current_charge = EVSECurrentCharge()
        # Copy charge status data
        evse.current_charge.charge_id = datagram.charge_id
        evse.current_charge.current_state = datagram.current_state
        evse.current_charge.start_type = datagram.start_type
        evse.current_charge.charge_type = datagram.charge_type
        evse.current_charge.max_duration_minutes = datagram.max_duration_minutes
        evse.current_charge.max_energy_kwh = datagram.max_energy_kwh
        evse.current_charge.max_electricity = datagram.max_electricity
        evse.current_charge.start_date = datagram.start_date
        evse.current_charge.duration_seconds = datagram.duration_seconds
        evse.current_charge.start_kwh_counter = datagram.start_kwh_counter
        evse.current_charge.current_kwh_counter = datagram.current_kwh_counter
        evse.current_charge.charge_kwh = datagram.charge_kwh
        evse.current_charge.charge_price = datagram.charge_price
        evse.current_charge.charge_fee = datagram.charge_fee
        # Send acknowledgment (as in TypeScript)
        response = SingleACChargingStatusResponse()
        response.set_device_serial(evse.info.serial)
        response.set_device_password(evse.password)
        await evse.send_datagram(response)
        await self._notify_callbacks('evse_charge_status_changed', evse)
    
    # MÉTHODES TEMPORAIREMENT DÉSACTIVÉES - À RÉIMPLÉMENTER
    
    # async def _handle_realtime_status(self, evse: EVSE, datagram: EVSERealTimeStatus):
    #     """Traiter les données de statut temps réel (commande 0x000d) - DÉSACTIVÉ"""
    #     pass
    
    # async def _handle_current_configuration(self, evse: EVSE, datagram: EVSECurrentConfiguration):
    #     """Traiter la configuration de courant (commande 0x010c) - DÉSACTIVÉ"""
    #     pass
    
    async def _handle_charge_record(self, evse: EVSE, datagram: CurrentChargeRecord):
        """Handle a charge record"""
        if not evse.current_charge:
            evse.current_charge = EVSECurrentCharge()
        
        # Map protocol attributes to internal structure
        evse.current_charge.port = datagram.line_id  # line_id → port
        # current_state does not exist in CurrentChargeRecord, keep existing value
        evse.current_charge.charge_id = datagram.charge_id
        evse.current_charge.start_type = datagram.start_type
        evse.current_charge.charge_type = datagram.charge_type
        evse.current_charge.reservation_date = datagram.reservation_data  # reservation_data → reservation_date
        evse.current_charge.user_id = datagram.start_user_id  # start_user_id → user_id
        # max_electricity does not exist in CurrentChargeRecord, keep existing value
        evse.current_charge.start_date = datagram.start_date
        evse.current_charge.duration_seconds = datagram.charged_time  # charged_time → duration_seconds
        evse.current_charge.start_kwh_counter = datagram.charge_start_power  # charge_start_power → start_kwh_counter
        evse.current_charge.current_kwh_counter = datagram.charge_stop_power  # charge_stop_power → current_kwh_counter
        evse.current_charge.charge_kwh = datagram.charge_power  # charge_power → charge_kwh
        evse.current_charge.charge_price = datagram.charge_price
        evse.current_charge.fee_type = datagram.fee_type
        evse.current_charge.charge_fee = datagram.charge_fee
        evse._last_response = datagram  # Store for _wait_for_response
        await self._notify_callbacks('evse_charge_changed', evse)
    
    async def _handle_heading(self, evse: EVSE, datagram: Heading):
        """Handle a heading (keepalive)"""
        # Respond to maintain the session
        response = HeadingResponse()
        response.set_device_serial(evse.info.serial)
        response.set_device_password(evse.password)
        await evse.send_datagram(response)
    
    async def _handle_output_electricity_response(self, evse: EVSE, datagram: SetAndGetOutputElectricityResponse):
        """Handle a current configuration response"""
        _LOGGER.debug(f"Output current response received from {evse.info.serial}: {datagram.electricity}A")
        # The response is automatically stored in evse._last_response for _wait_for_response
        # Update local configuration if it's a SET confirmation
        if hasattr(datagram, 'action') and datagram.action == 1:  # SET action
            evse.config.max_electricity = datagram.electricity
            await self._notify_callbacks('evse_changed', evse)
    
    async def send(self, datagram: Datagram, evse: EVSE) -> int:
        """Send a datagram"""
        if not self.running:
            raise RuntimeError("Communicateur non démarré")
        
    # Set serial and password if not already done
        if not datagram.get_device_serial():
            datagram.set_device_serial(evse.info.serial)
        
        if datagram.get_device_password() is None and evse.password:
            datagram.set_device_password(evse.password)
        
        buffer = datagram.pack()
        
    # Send via the socket
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            self.socket.sendto, 
            buffer, 
            (evse.info.ip, evse.info.port)
        )
        
        return len(buffer)
    
    async def _periodic_checks(self):
        """Periodic checks"""
        while self.running:
            try:
                await asyncio.sleep(5)
                
                for evse in self.evses.values():
                    # Check if we need to reconnect
                    if evse.is_logged_in() and evse.last_active_login:
                        time_since_login = datetime.now() - evse.last_active_login
                        if time_since_login.total_seconds() > 30:
                            # Relaunch login
                            if evse.password:
                                await evse.login(evse.password)
                    
                    # Request status regularly
                    if evse.is_logged_in():
                        await evse.send_datagram(RequestChargeStatusRecord())
                
            except Exception as e:
                _LOGGER.error(f"Error in periodic checks: {e}")
    
    async def _notify_callbacks(self, event: str, evse: EVSE):
        """Notify callbacks"""
        for callback in self.callbacks.values():
            try:
                await callback(event, evse)
            except Exception as e:
                _LOGGER.error(f"Error in callback: {e}")
    
    def add_callback(self, name: str, callback: Callable):
        """Add a callback"""
        self.callbacks[name] = callback
    
    def remove_callback(self, name: str):
        """Remove a callback"""
        self.callbacks.pop(name, None)
    
    def get_evse(self, serial: str) -> Optional[EVSE]:
        """Get an EVSE by its serial number"""
        return self.evses.get(serial)
    
    def get_all_evses(self) -> Dict[str, EVSE]:
        """Get all EVSEs"""
        return self.evses.copy()
    
    def close(self):
        """Close the communicator and release resources"""
        _LOGGER.debug("Closing UDP communicator")
        
    # Stop the listen loop
        self.running = False
        
    # Close the socket
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                _LOGGER.debug(f"Error while closing socket: {e}")
            finally:
                self.socket = None
        
    # Cancel the listen task if it exists
        if hasattr(self, '_listen_task') and self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
        
    _LOGGER.debug("UDP communicator closed")

# Global singleton
_communicator_instance: Optional[Communicator] = None

def get_communicator() -> Communicator:
    """Get the singleton instance of the communicator"""
    global _communicator_instance
    if _communicator_instance is None:
        _communicator_instance = Communicator()
    return _communicator_instance