"""
Implémentations des datagrammes EVSE EmProto
Port des datagrammes TypeScript vers Python
"""
import struct
from typing import Optional
from datetime import datetime
from .datagram import Datagram, register_datagram

# ============================================================================
# HEADING - Keepalive
# ============================================================================

@register_datagram
class Heading(Datagram):
    """Datagramme de keepalive envoyé par l'EVSE"""
    COMMAND = 0x0003
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Pas de payload
        pass

@register_datagram
class HeadingResponse(Datagram):
    """Réponse au datagramme Heading"""
    COMMAND = 32771  # 0x8003
    
    def pack_payload(self) -> bytes:
        return b'\x00'
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Pas utilisé - c'est une réponse
        pass

# ============================================================================
# LOGIN - Authentification
# ============================================================================

@register_datagram
class RequestLogin(Datagram):
    """Demande de connexion à l'EVSE (envoyé par le client) et broadcast de découverte (reçu de l'EVSE)"""
    COMMAND = 0x0001
    
    def __init__(self):
        super().__init__()
        # Attributs pour les broadcasts de découverte
        self.type: int = 0
        self.brand: str = ""
        self.model: str = ""
        self.hardware_version: str = ""
        self.max_power: int = 0
        self.max_electricity: int = 0
        self.hot_line: str = ""
        self.phases: int = 0
        self.p51: int = 0
        self.can_force_single_phase: bool = False
        self.feature: int = 0
        self.support_new: int = 0
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Si on reçoit un paquet 0x0001 avec payload, c'est un broadcast de découverte
        if len(buffer) > 0:
            # C'est un broadcast de découverte, traiter comme un Login
            self._parse_discovery_broadcast(buffer)
    
    def _parse_discovery_broadcast(self, buffer: bytes) -> None:
        """Parser un broadcast de découverte EVSE"""
        if len(buffer) < 1:
            return
            
        offset = 0
        
        # Type (1 byte)
        self.type = buffer[offset]
        offset += 1
        
        # Brand (16 bytes string)
        if offset + 16 <= len(buffer):
            self.brand = self.read_string(buffer, offset, 16)
            offset += 16
        else:
            self.brand = ""
        
        # Model (16 bytes string)  
        if offset + 16 <= len(buffer):
            self.model = self.read_string(buffer, offset, 16)
            offset += 16
        else:
            self.model = ""
            
        # Hardware version (16 bytes string)
        if offset + 16 <= len(buffer):
            self.hardware_version = self.read_string(buffer, offset, 16)
            offset += 16
        else:
            self.hardware_version = ""
            
        # Max power (4 bytes u32)
        if offset + 4 <= len(buffer):
            self.max_power = struct.unpack('>I', buffer[offset:offset+4])[0]
            offset += 4
        else:
            self.max_power = 0
            
        # Max electricity (1 byte)
        if offset + 1 <= len(buffer):
            self.max_electricity = buffer[offset]
            offset += 1
        else:
            self.max_electricity = 0
            
        # Hot line (16 bytes string)
        if offset + 16 <= len(buffer):
            self.hot_line = self.read_string(buffer, offset, 16)
            offset += 16
        else:
            self.hot_line = ""

@register_datagram
class LoginConfirm(Datagram):
    """Confirmation de connexion"""
    COMMAND = 0x8001
    
    def pack_payload(self) -> bytes:
        return b'\x00'
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Pas utilisé - c'est une commande sortante
        pass

@register_datagram
class PasswordErrorResponse(Datagram):
    """Erreur de mot de passe"""
    COMMAND = 0x8002
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Pas de payload spécifique
        pass

# ============================================================================
# STATUS - État de l'EVSE
# ============================================================================

@register_datagram
class SingleACStatus(Datagram):
    """État de l'EVSE (AC monophasé)"""
    COMMAND = 0x0004
    
    def __init__(self):
        super().__init__()
        self.current_power: float = 0
        self.current_amount: float = 0
        self.l1_voltage: float = 0
        self.l1_electricity: float = 0
        self.l2_voltage: float = 0
        self.l2_electricity: float = 0
        self.l3_voltage: float = 0
        self.l3_electricity: float = 0
        self.inner_temp: float = 0
        self.outer_temp: float = 0
        self.current_state: int = 0
        self.gun_state: int = 0
        self.output_state: int = 0
        self.errors: list = []
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) < 48:
            raise ValueError("Buffer trop court pour SingleACStatus")
        
        self.current_power = struct.unpack('>I', buffer[0:4])[0] / 1000.0
        self.current_amount = struct.unpack('>I', buffer[4:8])[0] / 1000.0
        self.l1_voltage = struct.unpack('>H', buffer[8:10])[0] / 10.0
        self.l1_electricity = struct.unpack('>H', buffer[10:12])[0] / 100.0
        self.l2_voltage = struct.unpack('>H', buffer[12:14])[0] / 10.0
        self.l2_electricity = struct.unpack('>H', buffer[14:16])[0] / 100.0
        self.l3_voltage = struct.unpack('>H', buffer[16:18])[0] / 10.0
        self.l3_electricity = struct.unpack('>H', buffer[18:20])[0] / 100.0
        
        self.inner_temp = self.read_temperature(buffer, 20)
        self.outer_temp = self.read_temperature(buffer, 22)
        
        self.current_state = buffer[24]
        self.gun_state = buffer[25]
        self.output_state = buffer[26]
        
        # Erreurs (tableau variable)
        error_count = buffer[27] if len(buffer) > 27 else 0
        self.errors = []
        for i in range(error_count):
            if len(buffer) > 28 + i:
                self.errors.append(buffer[28 + i])

@register_datagram
class SingleACStatusResponse(Datagram):
    """Réponse au status AC"""
    COMMAND = 32772  # 0x8004
    
    def pack_payload(self) -> bytes:
        return b'\x01'
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Pas utilisé - c'est une réponse
        pass

# ============================================================================
# CHARGE CONTROL - Contrôle de la charge
# ============================================================================

@register_datagram
class ChargeStart(Datagram):
    """Démarrer la charge"""
    COMMAND = 32775  # 0x800B
    
    def __init__(self):
        super().__init__()
        self.line_id: int = 1
        self.user_id: str = ""
        self.charge_id: str = ""
        self.max_electricity: int = 6
        self.single_phase: bool = False
        self.max_energy_kwh: Optional[float] = None
        self.param3: int = 0
    
    def pack_payload(self) -> bytes:
        buffer = bytearray(47)
        
        buffer[0] = self.line_id
        
        # User ID (16 bytes)
        user_bytes = self.user_id.encode('ascii')[:16]
        buffer[1:1+len(user_bytes)] = user_bytes
        
        # Charge ID (16 bytes)
        charge_bytes = self.charge_id.encode('ascii')[:16]
        buffer[17:17+len(charge_bytes)] = charge_bytes
        
        # Réservation (8 bytes) - timestamp ou 0
        struct.pack_into('>Q', buffer, 33, 0)
        
        # Paramètres
        buffer[41] = 1  # Start type
        
        # Max energy (kWh * 100) ou 65535 si illimité
        max_energy = int(self.max_energy_kwh * 100) if self.max_energy_kwh else 65535
        struct.pack_into('>H', buffer, 42, max_energy)
        
        struct.pack_into('>H', buffer, 44, self.param3)
        buffer[46] = self.max_electricity
        
        return bytes(buffer)
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Pas utilisé - c'est une commande sortante
        pass
    
    def set_line_id(self, line_id: int) -> 'ChargeStart':
        self.line_id = line_id
        return self
    
    def set_user_id(self, user_id: str) -> 'ChargeStart':
        self.user_id = user_id
        return self
    
    def set_charge_id(self, charge_id: str) -> 'ChargeStart':
        self.charge_id = charge_id
        return self
    
    def set_max_electricity(self, amps: int) -> 'ChargeStart':
        self.max_electricity = amps
        return self
    
    def set_single_phase(self, single_phase: bool) -> 'ChargeStart':
        self.single_phase = single_phase
        return self

@register_datagram
class ChargeStop(Datagram):
    """Arrêter la charge"""
    COMMAND = 32776  # 0x800C
    
    def __init__(self):
        super().__init__()
        self.line_id: int = 1
        self.user_id: str = ""
    
    def pack_payload(self) -> bytes:
        buffer = bytearray(17)
        buffer[0] = self.line_id
        
        user_bytes = self.user_id.encode('ascii')[:16]
        buffer[1:1+len(user_bytes)] = user_bytes
        
        return bytes(buffer)
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Pas utilisé - c'est une commande sortante
        pass

# ============================================================================
# CURRENT CHARGE RECORD - Enregistrement de charge
# ============================================================================

@register_datagram
class CurrentChargeRecord(Datagram):
    """Enregistrement de charge actuelle"""
    COMMAND = 0x0009
    
    def __init__(self):
        super().__init__()
        self.port: int = 1
        self.current_state: int = 0
        self.charge_id: str = ""
        self.start_type: int = 0
        self.charge_type: int = 0
        self.reservation_date: datetime = datetime.fromtimestamp(0)
        self.user_id: str = ""
        self.max_electricity: int = 0
        self.start_date: datetime = datetime.fromtimestamp(0)
        self.duration_seconds: int = 0
        self.start_kwh_counter: float = 0
        self.current_kwh_counter: float = 0
        self.charge_kwh: float = 0
        self.charge_price: float = 0
        self.fee_type: int = 0
        self.charge_fee: float = 0
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) < 97:
            raise ValueError("Buffer trop court pour CurrentChargeRecord")
        
        self.port = buffer[0]
        self.current_state = buffer[24]  # Position dans le buffer original
        self.charge_id = self.read_string(buffer, 33, 16)
        self.start_type = buffer[50]
        self.charge_type = buffer[51]
        
        # Dates (timestamps en secondes)
        reservation_ts = struct.unpack('>Q', buffer[1:9])[0]
        self.reservation_date = datetime.fromtimestamp(reservation_ts) if reservation_ts > 0 else datetime.fromtimestamp(0)
        
        self.user_id = self.read_string(buffer, 9, 16)
        self.max_electricity = buffer[25]
        
        start_ts = struct.unpack('>Q', buffer[26:34])[0]
        self.start_date = datetime.fromtimestamp(start_ts) if start_ts > 0 else datetime.fromtimestamp(0)
        
        self.duration_seconds = struct.unpack('>I', buffer[34:38])[0]
        self.start_kwh_counter = struct.unpack('>I', buffer[38:42])[0] / 1000.0
        self.current_kwh_counter = struct.unpack('>I', buffer[42:46])[0] / 1000.0
        self.charge_kwh = struct.unpack('>I', buffer[46:50])[0] / 1000.0
        self.charge_price = struct.unpack('>I', buffer[52:56])[0] / 10000.0
        self.fee_type = buffer[56]
        self.charge_fee = struct.unpack('>I', buffer[57:61])[0] / 10000.0

@register_datagram
class RequestChargeStatusRecord(Datagram):
    """Demander l'état de charge"""
    COMMAND = 32781  # 0x800D
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Pas utilisé
        pass

# ============================================================================
# VERSION - Information version
# ============================================================================

@register_datagram
class GetVersion(Datagram):
    """Obtenir la version"""
    COMMAND = 33030  # 0x8106
    
    def __init__(self):
        super().__init__()
        self.hardware_version: str = ""
        self.software_version: str = ""
        self.feature: int = 0
        self.support_new: int = 0
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) < 37:
            raise ValueError("Buffer trop court pour GetVersion")
        
        self.hardware_version = self.read_string(buffer, 0, 16)
        self.software_version = self.read_string(buffer, 16, 16)
        self.feature = struct.unpack('>I', buffer[32:36])[0]
        self.support_new = buffer[36]

# ============================================================================
# CONFIGURATION - Paramètres EVSE
# ============================================================================

@register_datagram
class SetAndGetOutputElectricity(Datagram):
    """Définir/obtenir le courant de sortie"""
    COMMAND = 0x0101
    
    def __init__(self):
        super().__init__()
        self.max_electricity: int = 6
    
    def pack_payload(self) -> bytes:
        return struct.pack('B', self.max_electricity)
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 1:
            self.max_electricity = buffer[0]

@register_datagram
class SetAndGetNickName(Datagram):
    """Définir/obtenir le nom de l'EVSE"""
    COMMAND = 0x0102
    
    def __init__(self):
        super().__init__()
        self.name: str = ""
    
    def pack_payload(self) -> bytes:
        name_bytes = self.name.encode('utf-8')[:32]
        buffer = bytearray(32)
        buffer[:len(name_bytes)] = name_bytes
        return bytes(buffer)
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 32:
            self.name = self.read_string(buffer, 0, 32)

@register_datagram
class SetAndGetSystemTime(Datagram):
    """Définir/obtenir l'heure système"""
    COMMAND = 0x010A
    
    def __init__(self):
        super().__init__()
        self.timestamp: int = 0
    
    def pack_payload(self) -> bytes:
        # Timestamp actuel en secondes
        import time
        self.timestamp = int(time.time())
        return struct.pack('>I', self.timestamp)
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 4:
            self.timestamp = struct.unpack('>I', buffer[0:4])[0]


class UnknownCommand341(Datagram):
    """Commande inconnue 341 (0x0155) - Réponse automatique"""
    COMMAND = 0x0155
    
    def __init__(self):
        super().__init__()
        self.raw_data: bytes = b''
    
    def pack_payload(self) -> bytes:
        # Réponse vide pour l'instant
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Conserver les données brutes pour debug
        self.raw_data = buffer