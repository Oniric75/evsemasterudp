#!/usr/bin/env python3
"""
Analyseur de paquets UDP pour comparer TypeScript vs Python
"""

import socket
import struct
import sys
import time
from typing import List, Tuple

def parse_packet(data: bytes, source: str) -> str:
    """Analyser un paquet UDP EVSE"""
    if len(data) < 25:
        return f"[{source}] Paquet trop court: {len(data)} bytes"
    
    try:
        # Header (2 bytes)
        header = struct.unpack('>H', data[0:2])[0]
        
        # Length (2 bytes)  
        length = struct.unpack('>H', data[2:4])[0]
        
        # Key type (1 byte)
        key_type = data[4]
        
        # Device serial (8 bytes hex)
        serial_bytes = data[5:13]
        serial = serial_bytes.hex()
        
        # Device password (6 bytes ASCII)
        password_bytes = data[13:19]
        password = password_bytes.decode('ascii', errors='ignore').rstrip('\x00')
        
        # Command (2 bytes)
        command = struct.unpack('>H', data[19:21])[0]
        
        # Payload
        payload = data[21:length-4] if length > 25 else b''
        
        # Checksum (2 bytes)
        checksum = struct.unpack('>H', data[length-4:length-2])[0]
        
        # Tail (2 bytes)
        tail = struct.unpack('>H', data[length-2:length])[0]
        
        # Calculer checksum attendu
        expected_checksum = sum(data[:length-4]) % 0xFFFF
        checksum_ok = checksum == expected_checksum
        
        result = f"""[{source}] Paquet EVSE:
  📊 Header: 0x{header:04x} | Length: {length} | KeyType: 0x{key_type:02x}
  📱 Serial: {serial} | Password: '{password}'
  🔧 Command: 0x{command:04x} | Payload: {len(payload)} bytes
  ✅ Checksum: 0x{checksum:04x} {'✓' if checksum_ok else '✗ (attendu: 0x' + f'{expected_checksum:04x})'} | Tail: 0x{tail:04x}
  📦 Raw: {data.hex()}
  📝 Payload hex: {payload.hex()}"""
        
        return result
        
    except Exception as e:
        return f"[{source}] Erreur parsing: {e} | Raw: {data.hex()}"

def listen_udp(port: int = 28376, timeout: int = 30):
    """Écouter les paquets UDP"""
    print(f"🎧 Écoute des paquets UDP sur port {port} (timeout: {timeout}s)")
    print("📝 Démarrez la version TypeScript dans un autre terminal pour comparer\n")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.settimeout(timeout)
    
    packets_received = 0
    start_time = time.time()
    
    try:
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                packets_received += 1
                
                print(f"\n📨 Paquet {packets_received} reçu de {addr[0]}:{addr[1]}")
                print(parse_packet(data, f"{addr[0]}:{addr[1]}"))
                print("-" * 80)
                
            except socket.timeout:
                print("⏱️ Timeout - aucun paquet reçu")
                break
                
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt par l'utilisateur")
    finally:
        sock.close()
    
    print(f"\n📊 Total: {packets_received} paquets reçus en {time.time() - start_time:.1f}s")

def test_python_packet():
    """Tester la génération de paquet Python"""
    print("🐍 Test génération paquet Python")
    
    # Ajouter le path
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'home_assistant', 'custom_components', 'evsemasterudp'))
    
    try:
        from protocol.datagrams import RequestLogin
        
        # Créer un RequestLogin
        login = RequestLogin()
        login.device_serial = "1368844619649410"
        login.device_password = "123456"
        
        # Encoder
        packet = login.pack()
        
        print(f"\n📦 Paquet Python généré:")
        print(parse_packet(packet, "Python"))
        
        return packet
        
    except Exception as e:
        print(f"❌ Erreur génération Python: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_with_typescript():
    """Comparer avec un paquet TypeScript de référence"""
    print("\n🔍 === COMPARAISON TYPESCRIPT vs PYTHON ===")
    
    # Test paquet Python
    python_packet = test_python_packet()
    
    print("\n📋 Pour comparer avec TypeScript:")
    print("1. Lancez: npx tsx clitest/index.ts 1368844619649410=123456")
    print("2. Dans un autre terminal: python capture_packets.py")
    print("3. Comparez les paquets générés")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "listen":
            listen_udp()
        elif sys.argv[1] == "test":
            test_python_packet()
        elif sys.argv[1] == "compare":
            compare_with_typescript()
        else:
            print("Usage: python capture_packets.py [listen|test|compare]")
    else:
        print("""
🔍 Analyseur de paquets EVSE

USAGE:
  python capture_packets.py listen    # Écouter les paquets UDP
  python capture_packets.py test      # Tester génération Python
  python capture_packets.py compare   # Comparer TS vs Python

WORKFLOW DE DÉBOGAGE:
1. python capture_packets.py test     # Voir paquet Python
2. python capture_packets.py listen   # Écouter réseau  
3. npx tsx clitest/index.ts ...       # Lancer TS dans autre terminal
4. Comparer les différences
        """)