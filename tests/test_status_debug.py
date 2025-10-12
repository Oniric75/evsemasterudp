#!/usr/bin/env python3
"""Test spécifique pour debug des données de statut"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'evsemasterudp'))

import asyncio
import logging
from protocol.communicator import Communicator

# Configurer les logs pour voir ce qui se passe
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_status_debug():
    """Test debug spécifique pour le statut"""
    print("🔍 Debug spécifique du statut EVSE")
    
    comm = Communicator()
    
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
        
        # Login
        print("🔑 Tentative de login...")
        success = await evse.login("123456")
        print(f"   Login: {'✅ Réussi' if success else '❌ Échoué'}")
        
        if not success:
            return
            
        # Demander le statut avec Heading
        print("📊 Demande de statut avec Heading...")
        from protocol.datagrams import Heading
        heading_request = Heading()
        success = await evse.send_datagram(heading_request)
        print(f"   Heading request: {'✅ Envoyé' if success else '❌ Échoué'}")
        
        # Attendre plus longtemps pour la réponse
        await asyncio.sleep(5)
        
        # Essayer aussi RequestChargeStatusRecord
        print("📊 Demande de statut avec RequestChargeStatusRecord...")
        from protocol.datagrams import RequestChargeStatusRecord
        status_request = RequestChargeStatusRecord()
        status_request.set_device_serial(serial)
        success = await evse.send_datagram(status_request)
        print(f"   Status request: {'✅ Envoyé' if success else '❌ Échoué'}")
        
        # Attendre un peu pour la réponse
        await asyncio.sleep(2)
        
        # Vérifier l'état
        print("\n🔍 État actuel de l'EVSE:")
        print(f"   Online: {evse.is_online()}")
        print(f"   Logged in: {evse.is_logged_in()}")
        print(f"   Meta state: {evse.get_meta_state()}")
        print(f"   State object: {evse.state}")
        
        if evse.state:
            print(f"   Power: {evse.state.current_power}W")
            print(f"   Voltage L1: {evse.state.l1_voltage}V")
            print(f"   Current L1: {evse.state.l1_electricity}A")
            print(f"   Temperature: {evse.state.inner_temp}°C")
        else:
            print("   ❌ Pas de données de statut")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await comm.stop()

if __name__ == "__main__":
    asyncio.run(test_status_debug())