#!/usr/bin/env python3
"""
Test de découverte automatique EVSE
"""

import asyncio
import sys
import os

# Ajouter le path vers le protocole
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

async def test_discovery():
    """Test découverte automatique"""
    try:
        from protocol import get_communicator
        
        print("🔍 Démarrage découverte EVSE...")
        comm = get_communicator()
        port = await comm.start()
        print(f"   ✅ Écoute sur port {port}")
        
        print("⏳ Attente de broadcasts EVSE (15s)...")
        
        # Attendre que des EVSE soient découvertes
        for i in range(15):
            await asyncio.sleep(1.0)
            
            if comm.evses:
                print(f"\n🎉 EVSE découvertes: {len(comm.evses)}")
                for serial, evse in comm.evses.items():
                    print(f"   📱 {serial} @ {evse.info.ip}:{evse.info.port}")
                    print(f"      🏷️ Brand: {getattr(evse.info, 'brand', 'N/A')}")
                    print(f"      🏷️ Model: {getattr(evse.info, 'model', 'N/A')}")
                break
            else:
                print(f"   ⏳ {i+1}/15s - Aucun EVSE trouvé...")
        
        if not comm.evses:
            print("   ❌ Aucun EVSE découvert")
        
        print("\n🛑 Arrêt du communicateur...")
        await comm.stop()
        print("   ✅ Arrêté")
        
        return len(comm.evses) > 0
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Test de découverte automatique EVSE")
    print("📡 Ce test écoute les broadcasts de découverte sur le réseau")
    print("🔌 Assurez-vous que votre EVSE est connectée et allumée\n")
    
    success = asyncio.run(test_discovery())
    
    if success:
        print("\n🎉 Découverte réussie ! L'EVSE a été détectée automatiquement.")
    else:
        print("\n⚠️ Aucun EVSE découvert automatiquement.")
        print("   Vérifiez que:")
        print("   • L'EVSE est sur le même réseau (192.168.42.x)")
        print("   • Le port UDP 28376 n'est pas bloqué") 
        print("   • L'EVSE envoie bien des broadcasts")