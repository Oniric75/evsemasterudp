#!/usr/bin/env python3
"""Analyse détaillée des broadcasts 0x0001 pour chercher les données de statut"""

# Payload des broadcasts qu'on a vus (150 bytes) :
payload_hex = "0145565345000000000000000000000000535157343900000000000000000000003331333235312e31313841303035330000001cc0205757572e455653452e434f4d00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

data_bytes = bytes.fromhex(payload_hex)

print(f"📊 Analyse du payload 0x0001 ({len(data_bytes)} bytes)")
print(f"Raw: {payload_hex}")
print()

print("📍 Parsing selon le protocole RequestLogin/Discovery:")

offset = 0

# Type (1 byte)
type_val = data_bytes[offset]
print(f"Type: {type_val}")
offset += 1

# Brand (16 bytes string)
brand = data_bytes[offset:offset+16].decode('ascii', errors='ignore').rstrip('\x00')
print(f"Brand: '{brand}'")
offset += 16

# Model (16 bytes string)
model = data_bytes[offset:offset+16].decode('ascii', errors='ignore').rstrip('\x00')
print(f"Model: '{model}'")
offset += 16

# Hardware version (16 bytes string)
hw_version = data_bytes[offset:offset+16].decode('ascii', errors='ignore').rstrip('\x00')
print(f"Hardware version: '{hw_version}'")
offset += 16

# Max power (4 bytes u32)
import struct
max_power = struct.unpack('>I', data_bytes[offset:offset+4])[0]
print(f"Max power: {max_power}W")
offset += 4

# Max electricity (1 byte)
max_electricity = data_bytes[offset]
print(f"Max electricity: {max_electricity}A")
offset += 1

# Hot line (16 bytes string)
hotline = data_bytes[offset:offset+16].decode('ascii', errors='ignore').rstrip('\x00')
print(f"Hotline: '{hotline}'")
offset += 16

print(f"\nOffset après parsing standard: {offset}")
print(f"Bytes restants: {len(data_bytes) - offset}")

if offset < len(data_bytes):
    remaining = data_bytes[offset:]
    print(f"Données restantes: {remaining.hex()}")
    
    print("\n🔍 Analyse des données restantes pour chercher des valeurs de statut:")
    
    # Chercher des candidats tension (235-237V selon l'app)
    print("\n⚡ Recherche de tension (235-237V):")
    for i in range(0, len(remaining)-1, 2):
        val = struct.unpack('>H', remaining[i:i+2])[0]
        # Tension directe
        if 230 <= val <= 240:
            print(f"  Offset {offset+i}: {val}V (direct)")
        # Tension / 10
        elif 2300 <= val <= 2400:
            print(f"  Offset {offset+i}: {val} -> {val/10}V (div10)")
        # Autres divisions
        elif val > 240:
            voltage_div10 = val / 10.0
            voltage_div100 = val / 100.0
            if 200 <= voltage_div10 <= 300:
                print(f"  Offset {offset+i}: {val} -> {voltage_div10}V (div10)")
            elif 200 <= voltage_div100 <= 300:
                print(f"  Offset {offset+i}: {val} -> {voltage_div100}V (div100)")
    
    # Chercher des candidats température (28°C selon l'app)
    print("\n🌡️ Recherche de température (28°C):")
    for i, byte in enumerate(remaining):
        if 25 <= byte <= 35:  # Autour de 28°C
            print(f"  Offset {offset+i}: {byte}°C")
    
    # Chercher des candidats courant max (6/32A selon l'app)
    print("\n🔌 Recherche de courant max (6A ou 32A):")
    for i, byte in enumerate(remaining):
        if byte in [6, 32]:
            print(f"  Offset {offset+i}: {byte}A")
            
    # Analyser par groupes de 4 bytes
    print("\n📊 Analyse par uint32:")
    for i in range(0, len(remaining)-3, 4):
        val = struct.unpack('>I', remaining[i:i+4])[0]
        print(f"  Offset {offset+i}-{offset+i+3}: 0x{val:08x} ({val})")
        
print()        
print("🎯 Hypothèses:")
print("1. Les données de statut temps réel (tension, température) ne sont peut-être pas dans les broadcasts")
print("2. Il faut peut-être déclencher une action spécifique (brancher un câble, démarrer une charge)")
print("3. Les données pourraient être envoyées sur demande uniquement")
print("4. Le format 0x000d qu'on a vu avant contenait les vraies données temps réel")