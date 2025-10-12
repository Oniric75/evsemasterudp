"""
Implémentations des datagrammes EVSE EmProto - Version corrigée selon TypeScript original
"""
import struct
from typing import Optional, List
from .datagram import Datagram, register_datagram

# ============================================================================
# UTILITAIRES (selon TypeScript)
# ============================================================================

def read_temperature(buffer: bytes, offset: int) -> float:
    """Lecture température selon la formule TypeScript"""
    if len(buffer) < offset + 2:
        return -1.0
    
    temp_raw = struct.unpack('>H', buffer[offset:offset+2])[0]
    if temp_raw == 0xffff:
        return -1.0
    return round((temp_raw - 20000) * 0.01, 2)

def read_string(buffer: bytes, offset: int, length: int) -> str:
    """Lecture string selon TypeScript"""
    if len(buffer) < offset + length:
        return ""
    return buffer[offset:offset+length].decode('ascii', errors='ignore').rstrip('\x00')

# ============================================================================
# COMMANDES PRINCIPALES (triées par ordre d'importance)
# ============================================================================

@register_datagram  
class Login(Datagram):
    """0x0001 - Broadcast de découverte EVSE (EVSE → App)"""
    COMMAND = 0x0001
    
    def __init__(self):
        super().__init__()
        self.type: int = 0
        self.brand: str = ""
        self.model: str = ""
        self.hardware_version: str = ""
        self.max_power: int = 0
        self.max_electricity: int = 0
        self.hot_line: str = ""
        self.p51: int = 0
    
    def pack_payload(self) -> bytes:
        return b''  # App n'envoie pas ce message
    
    def unpack_payload(self, buffer: bytes) -> None:
        """Parser selon SingleACStatus.ts"""
        if len(buffer) < 54:
            return
            
        self.type = buffer[0]
        self.brand = read_string(buffer, 1, 16)
        self.model = read_string(buffer, 17, 16) 
        self.hardware_version = read_string(buffer, 33, 16)
        self.max_power = struct.unpack('>I', buffer[49:53])[0]
        self.max_electricity = buffer[53]
        
        if len(buffer) > 54:
            self.hot_line = read_string(buffer, 54, 16)
            
        # Extensions selon la longueur du buffer (voir TypeScript)
        if len(buffer) >= 118:
            if len(buffer) == 118:
                self.hot_line += read_string(buffer, 70, 48)
            elif len(buffer) >= 119:
                self.hot_line += read_string(buffer, 71, 48)
                
        if len(buffer) == 151:
            self.brand += read_string(buffer, 119, 16)
            self.model += read_string(buffer, 135, 16)
            
        if len(buffer) >= 71 and self.type in [25, 9, 10]:
            self.p51 = buffer[70]

@register_datagram
class SingleACStatus(Datagram):
    """0x0004 - Statut temps réel AC (EVSE → App) - COMMANDE PRINCIPALE POUR VOLTAGE/TEMPÉRATURE"""
    COMMAND = 0x0004
    
    def __init__(self):
        super().__init__()
        # Champs selon SingleACStatus.ts (ordre exact)
        self.line_id: int = 0
        self.l1_voltage: float = 0.0          # V * 0.1
        self.l1_electricity: float = 0.0      # A * 0.01  
        self.current_power: int = 0           # W
        self.total_kwh_counter: float = 0.0   # kWh * 0.01
        self.inner_temp: float = 0.0          # °C (formule spéciale)
        self.outer_temp: float = 0.0          # °C (formule spéciale)
        self.emergency_btn_state: int = 0
        self.gun_state: int = 0
        self.output_state: int = 0
        self.current_state: int = 0
        self.errors: List[int] = []           # Bitfield des erreurs
        # Optionnels triphasé
        self.l2_voltage: float = 0.0
        self.l2_electricity: float = 0.0
        self.l3_voltage: float = 0.0
        self.l3_electricity: float = 0.0
    
    def pack_payload(self) -> bytes:
        return b''  # App n'envoie pas ce message
    
    def unpack_payload(self, buffer: bytes) -> None:
        """Parser selon SingleACStatus.ts - EXACT COPY"""
        if len(buffer) < 25:
            raise ValueError("Buffer too short for SingleACStatus")
            
        # Ordre exact selon TypeScript
        self.line_id = buffer[0]
        self.l1_voltage = struct.unpack('>H', buffer[1:3])[0] * 0.1
        self.l1_electricity = struct.unpack('>H', buffer[3:5])[0] * 0.01
        self.current_power = struct.unpack('>I', buffer[5:9])[0]
        self.total_kwh_counter = struct.unpack('>I', buffer[9:13])[0] * 0.01
        self.inner_temp = read_temperature(buffer, 13)
        self.outer_temp = read_temperature(buffer, 15)
        self.emergency_btn_state = buffer[17]
        self.gun_state = buffer[18]
        self.output_state = buffer[19]
        self.current_state = buffer[20]
        
        # Erreurs (bitfield 32-bit)
        error_bits = struct.unpack('>I', buffer[21:25])[0]
        self.errors = []
        for i in range(32):
            if error_bits & (1 << i):
                self.errors.append(i)
        
        # Triphasé optionnel (si buffer assez long)
        if len(buffer) >= 33:
            self.l2_voltage = struct.unpack('>H', buffer[25:27])[0] * 0.1
            self.l2_electricity = struct.unpack('>H', buffer[27:29])[0] * 0.01
            self.l3_voltage = struct.unpack('>H', buffer[29:31])[0] * 0.1  
            self.l3_electricity = struct.unpack('>H', buffer[31:33])[0] * 0.01

@register_datagram
class SingleACStatusResponse(Datagram):
    """0x8004 (32772) - Réponse SingleACStatus (App → EVSE)"""
    COMMAND = 32772
    
    def pack_payload(self) -> bytes:
        return bytes([0x01])
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass  # App vers EVSE

# ============================================================================
# COMMANDES D'AUTHENTIFICATION
# ============================================================================

@register_datagram
class RequestLogin(Datagram):
    """0x8002 (32770) - Demande de connexion (App → EVSE)"""
    COMMAND = 0x8002
    
    def pack_payload(self) -> bytes:
        return b'\x00'  # Un byte 0x00 selon TypeScript
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass  # Unused: this is an app->EVSE datagram

@register_datagram
class LoginResponse(Datagram):
    """0x0002 - Réponse de découverte (EVSE → App)"""
    COMMAND = 0x0002
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Même structure que Login - broadcast/discovery response
        pass

@register_datagram
class LoginConfirm(Datagram):
    """0x8001 (32769) - Confirmation de connexion (App → EVSE)"""
    COMMAND = 32769
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class PasswordErrorResponse(Datagram):
    """0x0155 (341) - Erreur de mot de passe (EVSE → App)"""
    COMMAND = 341
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

# ============================================================================
# COMMANDES DE SESSION
# ============================================================================

@register_datagram
class Heading(Datagram):
    """0x0003 - Heartbeat pour maintenir session (App → EVSE)"""
    COMMAND = 0x0003
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram  
class HeadingResponse(Datagram):
    """0x8003 (32771) - Réponse heartbeat (EVSE → App)"""
    COMMAND = 32771
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

# ============================================================================
# COMMANDES DE CONFIGURATION
# ============================================================================

@register_datagram
class SetAndGetChargeFeeResponse(Datagram):
    """0x0104 (260) - Réponse tarif de charge (EVSE → App)"""
    COMMAND = 260
    
    def __init__(self):
        super().__init__()
        self.action: int = 0
        self.electricity: int = 6
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 2:
            self.action = buffer[0]
            self.electricity = buffer[1]

@register_datagram
class GetVersion(Datagram):
    """0x8106 (33030) - Demander version (App → EVSE)"""
    COMMAND = 33030
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class GetVersionResponse(Datagram):
    """0x0106 (262) - Réponse version (EVSE → App)"""
    COMMAND = 262
    
    def __init__(self):
        super().__init__()
        self.hardware_version: str = ""
        self.software_version: str = ""
        self.feature: int = 0
        self.support_new: int = 0
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 37:
            self.hardware_version = read_string(buffer, 0, 16)
            self.software_version = read_string(buffer, 16, 32)
            self.feature = struct.unpack('>I', buffer[32:36])[0]
            self.support_new = buffer[36]

# ============================================================================
# COMMANDES DE CHARGE  
# ============================================================================

@register_datagram
class ChargeStart(Datagram):
    """0x8007 (32775) - Démarrer charge (App → EVSE)"""
    COMMAND = 32775
    
    def pack_payload(self) -> bytes:
        return b''  # TODO: implémenter selon besoins
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class ChargeStartResponse(Datagram):
    """0x0007 - Réponse démarrage charge (EVSE → App)"""
    COMMAND = 7
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class ChargeStop(Datagram):
    """0x8008 (32776) - Arrêter charge (App → EVSE)"""
    COMMAND = 32776
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class ChargeStopResponse(Datagram):
    """0x0008 - Réponse arrêt charge (EVSE → App)"""
    COMMAND = 8
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

# ============================================================================
# COMMANDES D'HISTORIQUE
# ============================================================================

@register_datagram
class CurrentChargeRecord(Datagram):
    """0x0009 - Enregistrement charge actuel (EVSE → App)"""
    COMMAND = 9
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class RequestChargeStatusRecord(Datagram):
    """0x8009 (32777) - Demander historique (App → EVSE)"""
    COMMAND = 32777
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class RequestStatusRecord(Datagram):
    """0x000d (13) - Demander statut (obsolète ?)"""
    COMMAND = 13
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

# ============================================================================
# COMMANDES DE STATUT DE CHARGE
# ============================================================================

@register_datagram
class SingleACChargingStatusPublicAuto(Datagram):
    """0x0005 (5) - Statut de charge automatique AC (EVSE → App)"""
    COMMAND = 5
    
    def __init__(self):
        super().__init__()
        self.port: int = 0
        self.current_state: int = 0  # 13=finished, 14=charging
        self.charge_id: str = ""
        self.start_type: int = 0
        self.charge_type: int = 0
        self.max_duration_minutes: Optional[int] = None
        self.max_energy_kwh: Optional[float] = None
        self.charge_param3: Optional[float] = None
        self.reservation_date: int = 0  # timestamp
        self.user_id: str = ""
        self.max_electricity: int = 0
        self.start_date: int = 0  # timestamp
        self.duration_seconds: int = 0
        self.start_kwh_counter: float = 0.0
        self.current_kwh_counter: float = 0.0
        self.charge_kwh: float = 0.0
        self.charge_price: float = 0.0
        self.fee_type: int = 0
        self.charge_fee: float = 0.0
    
    def pack_payload(self) -> bytes:
        return b''  # App ne génère pas ce message
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) < 74:
            return
            
        self.port = struct.unpack('B', buffer[0:1])[0]
        
        # État de charge (avec gestion de position variable selon TypeScript)
        if len(buffer) <= 74 or buffer[74] not in [18, 19]:
            self.current_state = struct.unpack('B', buffer[1:2])[0]
        else:
            self.current_state = struct.unpack('B', buffer[74:75])[0]
            
        self.charge_id = read_string(buffer, 2, 16)
        self.start_type = struct.unpack('B', buffer[18:19])[0]
        self.charge_type = struct.unpack('B', buffer[19:20])[0]
        
        # Durée max (65535 = non défini)
        max_duration_raw = struct.unpack('>H', buffer[20:22])[0]
        self.max_duration_minutes = None if max_duration_raw == 65535 else max_duration_raw
        
        # Énergie max (65535 = non défini) 
        max_energy_raw = struct.unpack('>H', buffer[22:24])[0]
        self.max_energy_kwh = None if max_energy_raw == 65535 else max_energy_raw * 0.01
        
        # Paramètre 3 (65535 = non défini)
        param3_raw = struct.unpack('>H', buffer[24:26])[0]
        self.charge_param3 = None if param3_raw == 65535 else param3_raw * 0.01
        
        self.reservation_date = struct.unpack('>I', buffer[26:30])[0]
        self.user_id = read_string(buffer, 30, 16)
        self.max_electricity = struct.unpack('B', buffer[46:47])[0]
        self.start_date = struct.unpack('>I', buffer[47:51])[0]
        self.duration_seconds = struct.unpack('>I', buffer[51:55])[0]
        self.start_kwh_counter = struct.unpack('>I', buffer[55:59])[0] * 0.01
        self.current_kwh_counter = struct.unpack('>I', buffer[59:63])[0] * 0.01
        self.charge_kwh = struct.unpack('>I', buffer[63:67])[0] * 0.01
        self.charge_price = struct.unpack('>I', buffer[67:71])[0] * 0.01
        self.fee_type = struct.unpack('B', buffer[71:72])[0]
        self.charge_fee = struct.unpack('>H', buffer[72:74])[0] * 0.01

@register_datagram
class SingleACChargingStatusResponse(Datagram):
    """0x0006 (6) - Réponse au statut de charge (App → EVSE)"""
    COMMAND = 6
    
    def pack_payload(self) -> bytes:
        return b'\x00'  # Accusé de réception simple
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

# ============================================================================
# COMMANDES MANQUANTES IMPORTANTES (selon TypeScript)
# ============================================================================

@register_datagram
class UploadLocalChargeRecord(Datagram):
    """0x000a (10) - Upload d'enregistrement de charge local (EVSE → App)"""
    COMMAND = 10
    
    def pack_payload(self) -> bytes:
        return b''  # App ne génère pas ce message
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass  # Traitement simplifié

@register_datagram
class CurrentChargeRecordResponse(Datagram):
    """0x800d (32781) - Réponse à l'enregistrement de charge actuel (App → EVSE)"""
    COMMAND = 32781
    
    def pack_payload(self) -> bytes:
        return b'\x00'  # Accusé de réception simple
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class SetAndGetOutputElectricity(Datagram):
    """0x8107 (33031) - Définir/Obtenir courant de sortie (App → EVSE)"""
    COMMAND = 33031
    
    def __init__(self):
        super().__init__()
        self.action: int = 0  # 0=GET, 1=SET
        self.electricity: int = 6  # Ampères (6-32A)
    
    def pack_payload(self) -> bytes:
        buffer = bytearray([self.action, 0x00])
        if self.action == 1:  # SET
            if not (6 <= self.electricity <= 32):
                raise ValueError("Current must be 6-32A")
            buffer[1] = self.electricity
        return bytes(buffer)
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 2:
            self.action = buffer[0]
            self.electricity = buffer[1]

@register_datagram
class SetAndGetOutputElectricityResponse(Datagram):
    """0x0107 (263) - Réponse courant de sortie (EVSE → App)"""
    COMMAND = 263
    
    def __init__(self):
        super().__init__()
        self.max_current: int = 16
    
    def pack_payload(self) -> bytes:
        return b''  # App ne génère pas ce message
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 1:
            self.max_current = struct.unpack('B', buffer[0:1])[0]

@register_datagram
class SetAndGetSystemTime(Datagram):
    """0x8101 (33025) - Définir/Obtenir heure système (App → EVSE)"""
    COMMAND = 33025
    
    def pack_payload(self) -> bytes:
        # Envoyer timestamp Unix actuel
        import time
        timestamp = int(time.time())
        return struct.pack('>I', timestamp)
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class SetAndGetSystemTimeResponse(Datagram):
    """0x0101 (257) - Réponse heure système (EVSE → App)"""
    COMMAND = 257
    
    def __init__(self):
        super().__init__()
        self.timestamp: int = 0
    
    def pack_payload(self) -> bytes:
        return b''  # App ne génère pas ce message
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 4:
            self.timestamp = struct.unpack('>I', buffer[0:4])[0]

@register_datagram
class SetAndGetOffLineCharge(Datagram):
    """0x810d (33037) - Définir/Obtenir charge hors ligne (App → EVSE)"""
    COMMAND = 33037
    
    def __init__(self):
        super().__init__()
        self.offline_enabled: bool = False
    
    def pack_payload(self) -> bytes:
        return struct.pack('B', 1 if self.offline_enabled else 0)
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 1:
            self.offline_enabled = struct.unpack('B', buffer[0:1])[0] == 1

@register_datagram
class SetAndGetOffLineChargeResponse(Datagram):
    """0x010c (268) - Réponse charge hors ligne (EVSE → App)"""
    COMMAND = 268
    
    def __init__(self):
        super().__init__()
        self.offline_enabled: bool = False
    
    def pack_payload(self) -> bytes:
        return b''  # App ne génère pas ce message
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 1:
            self.offline_enabled = struct.unpack('B', buffer[0:1])[0] == 1