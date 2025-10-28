"""
Implementations of EVSE EmProto datagrams - Corrected version based on original TypeScript
"""
import struct
from typing import Optional, List
from .datagram import Datagram, register_datagram

###############################################################################
# UTILITIES (from TypeScript)
###############################################################################

def read_temperature(buffer: bytes, offset: int) -> float:
    """Read temperature using the TypeScript formula"""
    if len(buffer) < offset + 2:
        return -1.0
    
    temp_raw = struct.unpack('>H', buffer[offset:offset+2])[0]
    if temp_raw == 0xffff:
        return -1.0
    return round((temp_raw - 20000) * 0.01, 2)

def read_string(buffer: bytes, offset: int, length: int) -> str:
    """Read string using TypeScript logic"""
    if len(buffer) < offset + length:
        return ""
    return buffer[offset:offset+length].decode('ascii', errors='ignore').rstrip('\x00')

###############################################################################
# MAIN COMMANDS (sorted by importance)
###############################################################################

@register_datagram  
class Login(Datagram):
    """0x0001 - EVSE discovery broadcast (EVSE → App)"""
    COMMAND = 0x0001
    
    def __init__(self):
        super().__init__()
        self.type = 0
        self.brand = ""
        self.model = ""
        self.hardware_version = ""
        self.max_power = 0
        self.max_electricity = 0
        self.hot_line = ""
        self.p51 = 0
        # Derived attributes not present in protocol but expected by handlers
        self.phases = 1  # Default: single phase
        self.can_force_single_phase = False  # Default: no force
        self.feature = ""  # Supported features
        self.support_new = False  # Support for new functions
    
    def pack_payload(self) -> bytes:
        return b''  # App does not send this message

    def unpack_payload(self, buffer: bytes) -> None:
        """Parse according to SingleACStatus.ts"""
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
            
        # Extensions depending on buffer length (see TypeScript)
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
    """0x0004 - Real-time AC status (EVSE → App) - MAIN COMMAND FOR VOLTAGE/TEMPERATURE"""
    COMMAND = 0x0004
    
    def __init__(self):
        super().__init__()
        # Fields according to SingleACStatus.ts (exact order)
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
        self.errors: list = []           # Error bitfield
        # Optional three-phase
        self.l2_voltage: float = 0.0
        self.l2_electricity: float = 0.0
        self.l3_voltage: float = 0.0
        self.l3_electricity: float = 0.0
    
    def pack_payload(self) -> bytes:
        return b''  # App does not send this message

    def unpack_payload(self, buffer: bytes) -> None:
        """Parse according to SingleACStatus.ts - EXACT COPY"""
        if len(buffer) < 25:
            raise ValueError("Buffer too short for SingleACStatus")

        # Exact order from TypeScript
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
        
        # Errors (32-bit bitfield)
        error_bits = struct.unpack('>I', buffer[21:25])[0]
        self.errors = []
        for i in range(32):
            if error_bits & (1 << i):
                self.errors.append(i)
        
        # Optional three-phase (if buffer long enough)
        if len(buffer) >= 33:
            self.l2_voltage = struct.unpack('>H', buffer[25:27])[0] * 0.1
            self.l2_electricity = struct.unpack('>H', buffer[27:29])[0] * 0.01
            self.l3_voltage = struct.unpack('>H', buffer[29:31])[0] * 0.1  
            self.l3_electricity = struct.unpack('>H', buffer[31:33])[0] * 0.01

@register_datagram
class SingleACStatusResponse(Datagram):
    """0x8004 (32772) - SingleACStatus response (App → EVSE)"""
    COMMAND = 32772
    
    def pack_payload(self) -> bytes:
        return bytes([0x01])
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass  # App to EVSE

###############################################################################
# AUTHENTICATION COMMANDS
###############################################################################

@register_datagram
class RequestLogin(Datagram):
    """0x8002 (32770) - Login request (App → EVSE)"""
    COMMAND = 0x8002
    
    def pack_payload(self) -> bytes:
        return b'\x00'  # One byte 0x00 as per TypeScript

    def unpack_payload(self, buffer: bytes) -> None:
        pass  # Unused: this is an app->EVSE datagram

@register_datagram
class LoginResponse(Datagram):
    """0x0002 - Discovery response (EVSE → App)"""
    COMMAND = 0x0002
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
    # Same structure as Login - broadcast/discovery response
        pass

@register_datagram
class LoginConfirm(Datagram):
    """0x8001 (32769) - Login confirmation (App → EVSE)"""
    COMMAND = 32769
    
    def pack_payload(self) -> bytes:
        return b'\x00'  # One byte 0x00 as per TypeScript
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class PasswordErrorResponse(Datagram):
    """0x0155 (341) - Password error (EVSE → App)"""
    COMMAND = 341
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

###############################################################################
# SESSION COMMANDS
###############################################################################

@register_datagram
class Heading(Datagram):
    """0x0003 - Heartbeat to maintain session (App → EVSE)"""
    COMMAND = 0x0003
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram  
class HeadingResponse(Datagram):
    """0x8003 (32771) - Heartbeat response (EVSE → App)"""
    COMMAND = 32771
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

###############################################################################
# CONFIGURATION COMMANDS
###############################################################################

@register_datagram
class SetAndGetChargeFeeResponse(Datagram):
    """0x0104 (260) - Charge fee response (EVSE → App)"""
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
    """0x8106 (33030) - Request version (App → EVSE)"""
    COMMAND = 33030
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class GetVersionResponse(Datagram):
    """0x0106 (262) - Version response (EVSE → App)"""
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
    """0x8007 (32775) - Start charging (App → EVSE)"""
    COMMAND = 32775
    
    def __init__(self):
        super().__init__()
        self.line_id = 1
        self.user_id = "emmgr"
        self.charge_id = ""
        self.reservation_date = 0  # timestamp
        self.start_type = 1
        self.charge_type = 1
        self.max_duration_minutes = 65535
        self.max_energy_kwh = 65535  # in hundredths of kWh
        self.param3 = 65535
        self.max_electricity = 6  # Amperes
        self.single_phase = False
    
    def pack_payload(self) -> bytes:
        # 47-byte buffer according to TypeScript
        buffer = bytearray(47)

        # Safety values
        if not (6 <= self.max_electricity <= 32):
            raise ValueError("maxElectricity must be 6-32A")

        # Generate a charge_id if empty
        if not self.charge_id:
            import time
            self.charge_id = f"{int(time.time())}"[:12].ljust(16, '0')

        # Current timestamp if no reservation
        if self.reservation_date == 0:
            import time
            self.reservation_date = int(time.time())

        # Fill the buffer
        buffer[0] = self.line_id

        # userId (16 bytes)
        user_bytes = self.user_id.encode('ascii')[:16]
        buffer[1:1+len(user_bytes)] = user_bytes

        # chargeId (16 bytes)
        charge_bytes = self.charge_id.encode('ascii')[:16]
        buffer[17:17+len(charge_bytes)] = charge_bytes

        # isReservation (0 = immediate)
        buffer[33] = 0

        # reservationDate (4 bytes, big endian)
        import struct
        buffer[34:38] = struct.pack('>I', self.reservation_date)

        # startType, chargeType
        buffer[38] = self.start_type
        buffer[39] = self.charge_type

        # params (big endian)
        buffer[40:42] = struct.pack('>H', self.max_duration_minutes)
        buffer[42:44] = struct.pack('>H', self.max_energy_kwh)
        buffer[44:46] = struct.pack('>H', self.param3)

        # maxElectricity
        buffer[46] = self.max_electricity

        return bytes(buffer)
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass  # App → EVSE only
    
    def set_max_electricity(self, amps: int):
        """Set the maximum current"""
        self.max_electricity = amps
        
    def set_single_phase(self, single_phase: bool):
        """Set single-phase mode"""
        self.single_phase = single_phase
        # Note: To be implemented if the protocol supports it
        
    def set_user_id(self, user_id: str):
        """Set user ID"""
        self.user_id = user_id[:16]  # Limit to 16 characters
        
    def set_charge_id(self, charge_id: str):
        """Set charge ID"""
        self.charge_id = charge_id[:16]  # Limit to 16 characters

@register_datagram
class ChargeStartResponse(Datagram):
    """0x0007 - Start charge response (EVSE → App)"""
    COMMAND = 7
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class ChargeStop(Datagram):
    """0x8008 (32776) - Stop charging (App → EVSE)"""
    COMMAND = 32776
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class ChargeStopResponse(Datagram):
    """0x0008 - Stop charge response (EVSE → App)"""
    COMMAND = 8
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

# ============================================================================
 # HISTORY COMMANDS
# ============================================================================

@register_datagram
class CurrentChargeRecord(Datagram):
    """0x0009 - Current charge record (EVSE → App)"""
    COMMAND = 9
    
    def __init__(self):
        super().__init__()
        self.line_id: int = 1
        self.start_user_id: str = ""
        self.end_user_id: str = ""
        self.charge_id: str = ""
        self.has_reservation: int = 0
        self.start_type: int = 0
        self.charge_type: int = 0
        self.charge_param1: int = 0
        self.charge_param2: float = 0.0
        self.charge_param3: float = 0.0
        self.stop_reason: int = 0
        self.has_stop_charge: int = 0
        self.reservation_data: int = 0
        self.start_date: int = 0
        self.stop_date: int = 0
        self.charged_time: int = 0
        self.charge_start_power: float = 0.0
        self.charge_stop_power: float = 0.0
        self.charge_power: float = 0.0
        self.charge_price: float = 0.0
        self.fee_type: int = 0
        self.charge_fee: float = 0.0
        self.log_kw_length: int = 0
        self.log_kw: list = []
        self.log_charge_data_kwh: list = []
        self.log_charge_data_charge_fee: list = []
        self.log_charge_data_service_fee: list = []
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) < 97:
            return
            
        self.line_id = buffer[0]
        self.start_user_id = read_string(buffer, 1, 16)
        self.end_user_id = read_string(buffer, 17, 16)
        self.charge_id = read_string(buffer, 33, 16)
        self.has_reservation = buffer[49]
        self.start_type = buffer[50]
        self.charge_type = buffer[51]
        self.charge_param1 = struct.unpack('>H', buffer[52:54])[0]
        self.charge_param2 = struct.unpack('>H', buffer[54:56])[0] * 0.001
        self.charge_param3 = struct.unpack('>H', buffer[56:58])[0] * 0.01
        self.stop_reason = buffer[58]
        self.has_stop_charge = buffer[59]
        self.reservation_data = struct.unpack('>I', buffer[60:64])[0]
        self.start_date = struct.unpack('>I', buffer[64:68])[0]
        self.stop_date = struct.unpack('>I', buffer[68:72])[0]
        self.charged_time = struct.unpack('>I', buffer[72:76])[0]
        self.charge_start_power = struct.unpack('>I', buffer[76:80])[0] * 0.01
        self.charge_stop_power = struct.unpack('>I', buffer[80:84])[0] * 0.01
        self.charge_power = struct.unpack('>I', buffer[84:88])[0] * 0.01
        self.charge_price = struct.unpack('>I', buffer[88:92])[0] * 0.01
        self.fee_type = buffer[92]
        self.charge_fee = struct.unpack('>H', buffer[93:95])[0] * 0.01
        self.log_kw_length = struct.unpack('>H', buffer[95:97])[0]
        
        # Logs optionnels selon la longueur
        if len(buffer) >= 156:
            self.log_kw = []
            for i in range(60):
                self.log_kw.append(struct.unpack('>H', buffer[96 + i*2:98 + i*2])[0])
                
        if len(buffer) >= 252:
            self.log_charge_data_kwh = []
            for i in range(0, 96, 2):
                self.log_charge_data_kwh.append(struct.unpack('>H', buffer[156 + i:158 + i])[0])
                
        if len(buffer) >= 348:
            self.log_charge_data_charge_fee = []
            for i in range(0, 96, 2):
                self.log_charge_data_charge_fee.append(struct.unpack('>H', buffer[252 + i:254 + i])[0])
                
        if len(buffer) >= 446:
            self.log_charge_data_service_fee = []
            for i in range(0, 96, 2):
                self.log_charge_data_service_fee.append(struct.unpack('>H', buffer[348 + i:350 + i])[0])

@register_datagram
class RequestChargeStatusRecord(Datagram):
    """0x8009 (32777) - Request history (App → EVSE)"""
    COMMAND = 32777
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class RequestStatusRecord(Datagram):
    """0x000d (13) - Request status (obsolete?)"""
    COMMAND = 13
    
    def pack_payload(self) -> bytes:
        return b''
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

# ============================================================================
 # CHARGE STATUS COMMANDS
# ============================================================================

@register_datagram
class SingleACChargingStatusPublicAuto(Datagram):
    """0x0005 (5) - Automatic AC charging status (EVSE → App)"""
    COMMAND = 5
    
    def __init__(self):
        super().__init__()
        self.port = 0
        self.current_state = 0  # 13=finished, 14=charging
        self.charge_id = ""
        self.start_type = 0
        self.charge_type = 0
        self.max_duration_minutes = None  # type: Optional[int]
        self.max_energy_kwh = None  # type: Optional[float]
        self.charge_param3 = None  # type: Optional[float]
        self.reservation_date = 0  # timestamp
        self.user_id = ""
        self.max_electricity = 0
        self.start_date = 0  # timestamp
        self.duration_seconds = 0
        self.start_kwh_counter = 0.0
        self.current_kwh_counter = 0.0
        self.charge_kwh = 0.0
        self.charge_price = 0.0
        self.fee_type = 0
        self.charge_fee = 0.0
    
    def pack_payload(self) -> bytes:
        return b''  # App does not generate this message
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) < 74:
            return
            
        self.port = struct.unpack('B', buffer[0:1])[0]
        
    # Charging state (with variable position handling according to TypeScript)
        if len(buffer) <= 74 or buffer[74] not in [18, 19]:
            self.current_state = struct.unpack('B', buffer[1:2])[0]
        else:
            self.current_state = struct.unpack('B', buffer[74:75])[0]
            
        self.charge_id = read_string(buffer, 2, 16)
        self.start_type = struct.unpack('B', buffer[18:19])[0]
        self.charge_type = struct.unpack('B', buffer[19:20])[0]
        
    # Max duration (65535 = undefined)
        max_duration_raw = struct.unpack('>H', buffer[20:22])[0]
        self.max_duration_minutes = None if max_duration_raw == 65535 else max_duration_raw
        
    # Max energy (65535 = undefined)
        max_energy_raw = struct.unpack('>H', buffer[22:24])[0]
        self.max_energy_kwh = None if max_energy_raw == 65535 else max_energy_raw * 0.01
        
    # Parameter 3 (65535 = undefined)
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
    """0x0006 (6) - Charge status response (App → EVSE)"""
    COMMAND = 6
    
    def pack_payload(self) -> bytes:
        return b'\x00'  # Simple acknowledgment
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

# ============================================================================
 # IMPORTANT MISSING COMMANDS (according to TypeScript)
# ============================================================================

@register_datagram
class UploadLocalChargeRecord(Datagram):
    """0x000a (10) - Upload local charge record (EVSE → App)"""
    COMMAND = 10
    
    def pack_payload(self) -> bytes:
        return b''  # App does not generate this message
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass  # Simplified processing

@register_datagram
class CurrentChargeRecordResponse(Datagram):
    """0x800d (32781) - Current charge record response (App → EVSE)"""
    COMMAND = 32781
    
    def pack_payload(self) -> bytes:
        return b'\x00'  # Simple acknowledgment
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class SetAndGetOutputElectricity(Datagram):
    """0x8107 (33031) - Set/Get output current (App → EVSE)"""
    COMMAND = 33031
    
    def __init__(self):
        super().__init__()
        self.action = 0  # 0=GET, 1=SET
        self.electricity = 6  # Amperes (6-32A)
    
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
    """0x0107 (263) - Output current response (EVSE → App)"""
    COMMAND = 263
    
    def __init__(self):
        super().__init__()
        self.action = 0  # 0=GET, 1=SET
        self.electricity = 16  # Amperes (6-32A)
    
    def pack_payload(self) -> bytes:
        return b''  # App does not generate this message
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 2:
            self.action = buffer[0]
            self.electricity = buffer[1]

@register_datagram
class SetAndGetSystemTime(Datagram):
    """0x8101 (33025) - Définir/Obtenir heure système (App → EVSE)"""
    COMMAND = 33025
    
    def pack_payload(self) -> bytes:
    # Send current Unix timestamp
        import time
        timestamp = int(time.time())
        return struct.pack('>I', timestamp)
    
    def unpack_payload(self, buffer: bytes) -> None:
        pass

@register_datagram
class SetAndGetSystemTimeResponse(Datagram):
    """0x0101 (257) - System time response (EVSE → App)"""
    COMMAND = 257
    
    def __init__(self):
        super().__init__()
        self.timestamp = 0
    
    def pack_payload(self) -> bytes:
        return b''  # App does not generate this message
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 4:
            self.timestamp = struct.unpack('>I', buffer[0:4])[0]

@register_datagram
class SetAndGetOffLineCharge(Datagram):
    """0x810d (33037) - Set/Get offline charge (App → EVSE)"""
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
    """0x010c (268) - Offline charge response (EVSE → App)"""
    COMMAND = 268
    
    def __init__(self):
        super().__init__()
        self.offline_enabled = False
    
    def pack_payload(self) -> bytes:
        return b''  # App does not generate this message
    
    def unpack_payload(self, buffer: bytes) -> None:
        if len(buffer) >= 1:
            self.offline_enabled = struct.unpack('B', buffer[0:1])[0] == 1