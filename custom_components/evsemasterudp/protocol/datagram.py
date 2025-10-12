"""
Classe de base pour les datagrammes EVSE EmProto
"""
import struct
from abc import ABC, abstractmethod
from typing import Optional, Dict, Type, List
import logging

_LOGGER = logging.getLogger(__name__)

class Datagram(ABC):
    """Classe de base pour tous les datagrammes EVSE"""
    
    COMMAND: int = 0
    PACKET_HEADER = 0x0601
    PACKET_TAIL = 0x0f02
    
    def __init__(self):
        self.key_type: int = 0x00
        self.device_serial: Optional[str] = None
        self.device_password: Optional[str] = None
    
    def get_command(self) -> int:
        """Obtenir le numéro de commande du datagramme"""
        return self.__class__.COMMAND
    
    @abstractmethod
    def pack_payload(self) -> bytes:
        """Empaqueter le payload spécifique au datagramme"""
        pass
    
    @abstractmethod
    def unpack_payload(self, buffer: bytes) -> None:
        """Désempaqueter le payload spécifique au datagramme"""
        pass
    
    def pack(self) -> bytes:
        """Empaqueter le datagramme complet"""
        command = self.get_command()
        if not command:
            raise ValueError(f"Commande manquante pour le type {self.__class__.__name__}")
        
        payload = self.pack_payload()
        
        # Créer le buffer complet (25 bytes header + payload)
        buffer_size = 25 + len(payload)
        buffer = bytearray(buffer_size)
        
        # Header (2 bytes)
        struct.pack_into('>H', buffer, 0, self.PACKET_HEADER)
        
        # Length (2 bytes)
        struct.pack_into('>H', buffer, 2, buffer_size)
        
        # Key type (1 byte)
        struct.pack_into('B', buffer, 4, self.key_type)
        
        # Device serial (8 bytes hex)
        if self.device_serial:
            serial_bytes = bytes.fromhex(self.device_serial)
            buffer[5:5+len(serial_bytes)] = serial_bytes
        
        # Device password (6 bytes ASCII)
        if self.device_password is not None:
            password_bytes = self.device_password.encode('ascii')[:6]
            buffer[13:13+len(password_bytes)] = password_bytes
        
        # Command (2 bytes)
        struct.pack_into('>H', buffer, 19, command)
        
        # Payload
        buffer[21:21+len(payload)] = payload
        
        # Checksum (2 bytes) - somme de tous les bytes sauf les 4 derniers
        checksum = sum(buffer[:-4]) % 0xFFFF
        struct.pack_into('>H', buffer, buffer_size - 4, checksum)
        
        # Tail (2 bytes)
        struct.pack_into('>H', buffer, buffer_size - 2, self.PACKET_TAIL)
        
        return bytes(buffer)
    
    def unpack(self, buffer: bytes) -> int:
        """Désempaqueter un datagramme depuis un buffer"""
        payload_length = self._validate_datagram(buffer)
        
        command = struct.unpack('>H', buffer[19:21])[0]
        if command != self.get_command():
            raise ValueError(f"Commande inattendue {command} pour le type {self.__class__.__name__}")
        
        self.key_type = buffer[4]
        self.device_serial = buffer[5:13].hex()
        
        # Password (peut être null)
        password_bytes = buffer[13:19]
        if all(b == 0 for b in password_bytes):
            self.device_password = None
        else:
            self.device_password = password_bytes.decode('ascii', errors='ignore').rstrip('\x00')
        
        # Extraire et désempaqueter le payload
        payload = buffer[21:21 + payload_length]
        self.unpack_payload(payload)
        
        return payload_length + 25
    
    def _validate_datagram(self, buffer: bytes) -> int:
        """Valider le datagramme et retourner la longueur du payload"""
        if len(buffer) < 25:
            raise ValueError("Datagramme trop court")
        
        header = struct.unpack('>H', buffer[0:2])[0]
        if header != self.PACKET_HEADER:
            raise ValueError("Header magique manquant")
        
        length = struct.unpack('>H', buffer[2:4])[0]
        if length > len(buffer):
            raise ValueError("Longueur invalide")
        
        # Vérifier le checksum
        computed_checksum = sum(buffer[:length-4]) % 0xFFFF
        checksum = struct.unpack('>H', buffer[length-4:length-2])[0]
        if computed_checksum != checksum:
            raise ValueError("Checksum invalide")
        
        return length - 25
    
    def read_string(self, buffer: bytes, offset: int, length: int) -> str:
        """Lire une chaîne depuis le buffer"""
        end = offset + length
        string_bytes = buffer[offset:end]
        # Retirer les bytes null à la fin
        null_pos = string_bytes.find(b'\x00')
        if null_pos != -1:
            string_bytes = string_bytes[:null_pos]
        return string_bytes.decode('ascii', errors='ignore')
    
    def read_temperature(self, buffer: bytes, offset: int) -> float:
        """Lire une température depuis le buffer"""
        temp_raw = struct.unpack('>H', buffer[offset:offset+2])[0]
        return (temp_raw - 100) / 10.0
    
    def set_device_serial(self, serial: str) -> 'Datagram':
        """Définir le numéro de série de l'appareil"""
        self.device_serial = serial
        return self
    
    def set_device_password(self, password: Optional[str]) -> 'Datagram':
        """Définir le mot de passe de l'appareil"""
        self.device_password = password
        return self
    
    def get_device_serial(self) -> Optional[str]:
        """Obtenir le numéro de série de l'appareil"""
        return self.device_serial
    
    def get_device_password(self) -> Optional[str]:
        """Obtenir le mot de passe de l'appareil"""
        return self.device_password
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(command={self.get_command()})"


class UnknownCommandBase(Datagram):
    """Classe de base pour les commandes inconnues"""
    COMMAND = 0x0000  # Sera remplacé dynamiquement
    
    def __init__(self):
        super().__init__()
        self.raw_data: bytes = b''
    
    def pack_payload(self) -> bytes:
        # Retourner les données brutes telles quelles
        return self.raw_data
    
    def unpack_payload(self, buffer: bytes) -> None:
        # Conserver les données brutes pour debug
        self.raw_data = buffer


# Registre des types de datagrammes
DATAGRAM_TYPES: Dict[int, Type[Datagram]] = {}

def register_datagram(cls: Type[Datagram]) -> Type[Datagram]:
    """Décorateur pour enregistrer un type de datagramme"""
    if cls.COMMAND in DATAGRAM_TYPES:
        existing = DATAGRAM_TYPES[cls.COMMAND]
        raise ValueError(f"Commande {cls.COMMAND} déjà utilisée par {existing.__name__}")
    DATAGRAM_TYPES[cls.COMMAND] = cls
    return cls

def parse_datagrams(buffer: bytes) -> List[Datagram]:
    """Parser plusieurs datagrammes depuis un buffer"""
    datagrams = []
    offset = 0
    
    while len(buffer) - offset >= 25:
        # Vérifier le header
        header = struct.unpack('>H', buffer[offset:offset+2])[0]
        if header != Datagram.PACKET_HEADER:
            _LOGGER.warning(f"Header magique manquant: {header:04x}")
            break
        
        # Obtenir la commande
        command = struct.unpack('>H', buffer[offset+19:offset+21])[0]
        datagram_class = DATAGRAM_TYPES.get(command)
        
        if not datagram_class:
            _LOGGER.warning(f"Commande inconnue reçue: {command} (0x{command:04x}) - Peut-être une nouvelle commande EVSE non encore implémentée")
            # Créer une classe générique pour les commandes inconnues
            datagram_class = type(f'UnknownCommand{command}', (UnknownCommandBase,), {'COMMAND': command})
        
        # Créer et désempaqueter le datagramme
        try:
            datagram = datagram_class()
            length = datagram.unpack(buffer[offset:])
            datagrams.append(datagram)
            offset += length
        except Exception as e:
            _LOGGER.error(f"Erreur lors du parsing du datagramme {command}: {e}")
            break
    
    return datagrams