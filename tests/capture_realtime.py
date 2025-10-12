#!/usr/bin/env python3
"""Capture des données temps réel avec login pour analyser le protocole 0x000d"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'evsemasterudp'))

import asyncio
import logging
import struct
from datetime import datetime
from protocol.communicator import Communicator

# Configurer les logs pour voir ce qui se passe
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class DataAnalyzer:
    def __init__(self):
        self.samples = []
        
    def analyze_0x000d(self, data_hex: str, timestamp: datetime):
        """Analyser en détail une trame 0x000d"""
        data_bytes = bytes.fromhex(data_hex)
        
        sample = {
            'timestamp': timestamp,
            'raw': data_hex,
            'bytes': data_bytes,
            'length': len(data_bytes)
        }
        
        if len(data_bytes) >= 40:
            # Extraire les candidats pour chaque type de donnée
            sample.update({
                'byte_2_temp_candidate': data_bytes[2],  # 28°C selon l'app
                'voltage_candidates': [],
                'current_candidates': [],
                'byte_17_state': data_bytes[17],  # États potentiels
                'byte_18_19_current': struct.unpack('>H', data_bytes[18:20])[0] if len(data_bytes) >= 20 else 0,
            })
            
            # Chercher les candidats tension (235-237V selon l'app)
            for i in range(0, len(data_bytes)-1, 2):
                val = struct.unpack('>H', data_bytes[i:i+2])[0]
                # Tension directe
                if 230 <= val <= 240:
                    sample['voltage_candidates'].append((i, val, 'direct'))
                # Tension * 10
                elif 2300 <= val <= 2400:
                    sample['voltage_candidates'].append((i, val/10, 'div10'))
                # Tension * 100
                elif 23000 <= val <= 24000:
                    sample['voltage_candidates'].append((i, val/100, 'div100'))
            
            # Chercher les candidats courant (6A max selon l'app)
            for i in range(0, len(data_bytes)-1, 2):
                val = struct.unpack('>H', data_bytes[i:i+2])[0]
                # Courant en mA
                if 0 <= val <= 6000:
                    sample['current_candidates'].append((i, val/1000, 'milliamps'))
                # Courant en cA (centi-ampères)
                elif 0 <= val <= 600:
                    sample['current_candidates'].append((i, val/100, 'centiamps'))
        
        self.samples.append(sample)
        return sample
    
    def print_analysis(self, sample):
        """Afficher l'analyse d'un échantillon"""
        print(f"\n📊 Analyse à {sample['timestamp'].strftime('%H:%M:%S')}")
        print(f"   Raw ({sample['length']} bytes): {sample['raw']}")
        
        if 'byte_2_temp_candidate' in sample:
            print(f"   🌡️ Température candidat (byte 2): {sample['byte_2_temp_candidate']}°C")
            
        if sample.get('voltage_candidates'):
            print("   ⚡ Candidats tension:")
            for offset, voltage, method in sample['voltage_candidates']:
                print(f"      Offset {offset:2d}: {voltage:6.1f}V ({method})")
        
        if sample.get('current_candidates'):
            print("   🔌 Candidats courant:")
            for offset, current, method in sample['current_candidates']:
                print(f"      Offset {offset:2d}: {current:6.3f}A ({method})")
                
        print(f"   🎛️ État byte 17: 0x{sample.get('byte_17_state', 0):02x}")
        print(f"   📈 Current offset 18-19: {sample.get('byte_18_19_current', 0)} (raw)")

async def capture_realtime_data():
    """Capturer les données temps réel avec authentification"""
    print("🔍 Capture des données temps réel EVSE avec analyse détaillée")
    
    analyzer = DataAnalyzer()
    comm = Communicator()
    
    # Hook pour capturer les données 0x000d brutes
    original_parse = None
    
    def capture_0x000d(self, buffer, serial, command):
        if command == 0x000d:
            timestamp = datetime.now()
            data_hex = buffer.hex()
            print(f"\n🎯 Données 0x000d capturées à {timestamp.strftime('%H:%M:%S.%f')[:-3]}")
            sample = analyzer.analyze_0x000d(data_hex, timestamp)
            analyzer.print_analysis(sample)
    
    try:
        await comm.start()
        print("✅ Communicateur démarré")
        
        # Attendre découverte
        await asyncio.sleep(3)
        
        evses = comm.get_all_evses()
        if not evses:
            print("❌ Aucune EVSE trouvée")
            return
            
        serial = list(evses.keys())[0]
        evse = evses[serial]
        
        print(f"📱 EVSE trouvée: {serial}")
        print(f"   IP: {evse.info.ip}")
        print(f"   Model: {evse.info.model}")
        
        # Hook pour capturer avant parsing
        old_handle_message = comm._handle_message
        
        async def hooked_handle_message(buffer, addr):
            # Analyser le message avant traitement normal
            if len(buffer) >= 25:  # Taille minimale d'un message
                try:
                    # Extraire la commande
                    command = struct.unpack('>H', buffer[21:23])[0]
                    if command == 0x000d:
                        payload_start = 25
                        payload_end = len(buffer) - 4  # Enlever checksum + tail
                        if payload_end > payload_start:
                            payload = buffer[payload_start:payload_end]
                            capture_0x000d(None, payload, serial, command)
                except:
                    pass
            
            # Appeler le handler original
            return await old_handle_message(buffer, addr)
        
        comm._handle_message = hooked_handle_message
        
        # Login
        print("🔑 Tentative de login...")
        success = await evse.login("123456")
        print(f"   Login: {'✅ Réussi' if success else '❌ Échoué'}")
        
        if success:
            print("\n⏳ Écoute des données temps réel pendant 60 secondes...")
            print("   (Basé sur l'app: tension 235-237V, temp 28°C, max current 6/32A)")
            
            # Écouter pendant 60 secondes
            await asyncio.sleep(60)
            
            print(f"\n📊 Résumé: {len(analyzer.samples)} échantillons capturés")
            
            if analyzer.samples:
                print("\n🔍 Analyse comparative des échantillons:")
                for i, sample in enumerate(analyzer.samples[:5]):  # Premiers 5 échantillons
                    print(f"\nÉchantillon {i+1}:")
                    analyzer.print_analysis(sample)
                    
        else:
            print("❌ Impossible de se connecter - pas de données temps réel")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await comm.stop()

if __name__ == "__main__":
    asyncio.run(capture_realtime_data())