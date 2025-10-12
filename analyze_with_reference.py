#!/usr/bin/env python3
"""Analyse spécialisée des données 0x000d avec les valeurs de référence de l'app"""

import struct

# Données 0x000d capturées précédemment
data_hex = "0109320000000000000000000159105b0c0101020c00000000000000000000000003ff0000000000"
data_bytes = bytes.fromhex(data_hex)

# Valeurs de référence de l'application
ref_voltage = 236  # Moyenne de 235-237V
ref_temp = 28      # 28°C selon l'app
ref_current_max = 32  # 32A max
ref_current_set = 6   # 6A configuré

print(f"📊 Analyse 0x000d avec référence app")
print(f"   Référence: {ref_voltage}V, {ref_temp}°C, {ref_current_set}/{ref_current_max}A")
print(f"   Data ({len(data_bytes)} bytes): {data_hex}")
print()

print("🎯 Recherche par correspondance avec valeurs de référence:")

# Recherche de la tension (235-237V)
print(f"\n⚡ Recherche tension (~{ref_voltage}V):")
for i in range(0, len(data_bytes)-1, 2):
    val = struct.unpack('>H', data_bytes[i:i+2])[0]
    
    # Test différents encodages
    candidates = [
        (val, 'direct'),
        (val / 10.0, 'div10'),
        (val / 100.0, 'div100'),
        (val * 10, 'mul10'),
    ]
    
    for test_val, method in candidates:
        if abs(test_val - ref_voltage) <= 5:  # ±5V de tolérance
            print(f"  🎯 MATCH! Offset {i:2d}: {val} -> {test_val:.1f}V ({method})")

# Recherche de la température (28°C)
print(f"\n🌡️ Recherche température (~{ref_temp}°C):")
for i, byte in enumerate(data_bytes):
    if abs(byte - ref_temp) <= 3:  # ±3°C de tolérance
        print(f"  🎯 MATCH! Offset {i:2d}: {byte}°C")

# Recherche des courants (6A et 32A)
print(f"\n🔌 Recherche courants ({ref_current_set}A configuré, {ref_current_max}A max):")
for i in range(0, len(data_bytes)-1, 2):
    val = struct.unpack('>H', data_bytes[i:i+2])[0]
    
    # Test différents encodages pour le courant
    candidates = [
        (val, 'direct'),
        (val / 10.0, 'div10'),
        (val / 100.0, 'div100'),
        (val / 1000.0, 'div1000'),
    ]
    
    for test_val, method in candidates:
        if abs(test_val - ref_current_set) <= 1 or abs(test_val - ref_current_max) <= 1:
            print(f"  🎯 MATCH! Offset {i:2d}: {val} -> {test_val:.3f}A ({method})")

# Recherche byte par byte pour courants
print(f"\n🔌 Recherche courants (byte simple):")
for i, byte in enumerate(data_bytes):
    if byte == ref_current_set or byte == ref_current_max:
        print(f"  🎯 MATCH! Offset {i:2d}: {byte}A")

print(f"\n📍 Analyse détaillée par offset:")
print("Offset | Byte | Uint16BE | Interprétation possible")
print("-------|------|----------|----------------------")

for i in range(len(data_bytes)):
    byte_val = data_bytes[i]
    
    uint16_val = "---"
    if i < len(data_bytes) - 1:
        uint16_val = f"{struct.unpack('>H', data_bytes[i:i+2])[0]:5d}"
    
    interpretation = ""
    
    # Température candidat
    if 20 <= byte_val <= 40:
        interpretation += f"Temp:{byte_val}°C "
    
    # Courant candidat
    if byte_val in [6, 32]:
        interpretation += f"Current:{byte_val}A "
    
    # État candidat
    if byte_val in [0, 1, 2, 3]:
        interpretation += f"State:{byte_val} "
    
    print(f"  {i:2d}   | 0x{byte_val:02x} |  {uint16_val} | {interpretation}")

print(f"\n🔍 Pattern recognition:")
print("1. Offset 2 = 0x32 (50) - Trop élevé pour 28°C, mais 50/2 = 25°C proche")
print("2. Les uint16 ne correspondent pas directement aux tensions attendues")
print("3. Les courants 6A/32A ne sont pas évidents en direct")
print("4. Il faut peut-être analyser des données en cours de charge pour voir les variations")