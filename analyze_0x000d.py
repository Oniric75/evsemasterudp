#!/usr/bin/env python3
"""Analyseur spécifique des données 0x000d"""

data_hex = "0109320000000000000000000159105b0c0101020c00000000000000000000000003ff0000000000"
data_bytes = bytes.fromhex(data_hex)

print(f"📊 Analyse des données 0x000d ({len(data_bytes)} bytes)")
print(f"Raw: {data_hex}")
print()

print("📍 Analyse byte par byte:")
for i, byte in enumerate(data_bytes):
    print(f"  [{i:2d}] 0x{byte:02x} ({byte:3d}) {chr(byte) if 32 <= byte <= 126 else '.'}")

print()
print("📍 Analyse par groupe de 2 bytes (uint16):")
for i in range(0, len(data_bytes)-1, 2):
    val = (data_bytes[i] << 8) | data_bytes[i+1]
    print(f"  [{i:2d}-{i+1:2d}] 0x{val:04x} ({val:5d})")

print()
print("📍 Analyse par groupe de 4 bytes (uint32):")
for i in range(0, len(data_bytes)-3, 4):
    val = (data_bytes[i] << 24) | (data_bytes[i+1] << 16) | (data_bytes[i+2] << 8) | data_bytes[i+3]
    print(f"  [{i:2d}-{i+3:2d}] 0x{val:08x} ({val:10d})")

print()
print("📍 Recherche de valeurs tension typiques (200-250V):")
for i in range(0, len(data_bytes)-1, 2):
    val = (data_bytes[i] << 8) | data_bytes[i+1]
    if 200 <= val <= 250:
        print(f"  Tension possible à offset {i}: {val}V")

print()
print("📍 Recherche de valeurs courant typiques (0-32A * 1000 = 0-32000):")
for i in range(0, len(data_bytes)-1, 2):
    val = (data_bytes[i] << 8) | data_bytes[i+1]
    if 0 <= val <= 32000:
        amps = val / 1000.0
        if 0.1 <= amps <= 32:
            print(f"  Courant possible à offset {i}: {val} -> {amps}A")

print()
print("📍 Recherche de températures typiques (0-100°C):")
for i, byte in enumerate(data_bytes):
    if 0 <= byte <= 100:
        print(f"  Température possible à offset {i}: {byte}°C")