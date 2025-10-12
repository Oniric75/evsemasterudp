#!/usr/bin/env python3
"""
Test debug temporaire avec vraies infos
"""

import asyncio
import sys
import os

# Ajouter le path vers le protocole
test_dir = os.path.dirname(__file__)
evse_module_path = os.path.join(test_dir, 'custom_components', 'evsemasterudp')
sys.path.insert(0, evse_module_path)

async def test_debug():
    """Test avec vraies infos"""
    try:
        from protocol.communicator import Communicator
        
        print("🔍 Test debug avec vraies infos...")
        comm = Communicator()
        await comm.start()
        print("   ✅ Écoute démarrée")
        
        # Attendre découverte
        print("⏳ Attente découverte (3s)...")
        await asyncio.sleep(3)
        
        if not comm.evses:
            print("❌ Aucun EVSE découvert")
            return
            
        evse = list(comm.evses.values())[0]
        print(f"   🎯 EVSE: {evse.info.serial} @ {evse.info.ip}")
        
        # Test authentification avec vraies infos
        print("🔐 Test authentification...")
        success = await evse.login("091082")
        
        if success:
            print("   ✅ Authentification réussie !")
            
            # Test récupération de données
            print("📊 Test récupération données...")
            await asyncio.sleep(2)
            
            # Forcer une demande de statut
            try:
                await evse.request_status()
                print("   ✅ Demande de statut envoyée")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"   ⚠️ Erreur demande statut: {e}")
                
        else:
            print("   ❌ Authentification échouée")
            
        await comm.stop()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_debug())