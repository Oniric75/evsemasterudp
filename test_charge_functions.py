#!/usr/bin/env python3
"""
Test complet des fonctions de charge en Python
"""
import asyncio
import logging
import sys
import os

# Ajouter le chemin pour importer les modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'evsemasterudp'))

from protocol.communicator import Communicator, EVSE

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

async def test_charge_functions():
    """Test des fonctions de charge"""
    
    # Configuration
    EVSE_SERIAL = "1368845689849510"
    EVSE_PASSWORD = "091082"
    TEST_CURRENT = 10  # Ampères
    
    print(f"🧪 Test complet des fonctions de charge en Python")
    print(f"📱 EVSE: {EVSE_SERIAL}")
    print(f"⚡ Test avec: {TEST_CURRENT}A")
    
    communicator = None
    try:
        # Créer le communicateur
        communicator = Communicator()
        await communicator.start()
        print("✅ Communicator démarré")
        
        # Attendre découverte
        print("🔍 Attente découverte EVSE...")
        for i in range(30):  # 30 secondes max
            await asyncio.sleep(1)
            if EVSE_SERIAL in communicator.evses:
                break
        
        if EVSE_SERIAL not in communicator.evses:
            print("❌ EVSE non trouvée après 30 secondes")
            return False
            
        evse = communicator.evses[EVSE_SERIAL]
        print("🎯 EVSE découverte: " + EVSE_SERIAL)
        
        # Connexion
        print("🔐 Authentification...")
        success = await evse.login(EVSE_PASSWORD)
        if not success:
            print("❌ Échec authentification")
            return False
        print("✅ Authentification réussie")
        
        # Attendre stabilisation
        await asyncio.sleep(2)
        
        # Test 1: Modifier le courant maximum
        print(f"\n🔧 TEST 1: Modification du courant max à {TEST_CURRENT}A")
        print(f"   Courant actuel: {evse.config.max_electricity}A")
        
        success = await evse.set_max_electricity(TEST_CURRENT)
        if success:
            await asyncio.sleep(2)
            print(f"   ✅ Nouveau courant: {evse.config.max_electricity}A")
        else:
            print("   ❌ Échec modification courant")
            return False
        
        # Test 2: Test de charge start
        print(f"\n🚀 TEST 2: Démarrage de charge avec {TEST_CURRENT}A")
        print(f"   État actuel: {evse.state.current_state if evse.state else 'Inconnu'}")
        
        success = await evse.charge_start(
            max_amps=TEST_CURRENT,
            user_id="PythonTest",
            charge_id="TEST001"
        )
        
        if success:
            print("   ✅ Commande charge_start envoyée")
            await asyncio.sleep(3)
            
            if evse.state:
                print(f"   📊 Nouvel état: {evse.state.current_state}")
                print(f"   📊 État pistolet: {evse.state.gun_state}")
                print(f"   📊 État sortie: {evse.state.output_state}")
            
        else:
            print("   ⚠️ Échec charge_start (peut être normal si pas de voiture)")
        
        # Test 3: Test de charge stop
        print(f"\n🛑 TEST 3: Arrêt de charge")
        
        success = await evse.charge_stop(user_id="PythonTest")
        
        if success:
            print("   ✅ Commande charge_stop envoyée")
            await asyncio.sleep(2)
            
            if evse.state:
                print(f"   📊 État final: {evse.state.current_state}")
        else:
            print("   ⚠️ Échec charge_stop")
        
        print("\n🎉 Tests terminés avec succès!")
        print("📱 Vérifiez l'app EVSE Master pour confirmer les changements")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if communicator:
            communicator.stop()
            print("🛑 Communicator arrêté")

if __name__ == "__main__":
    result = asyncio.run(test_charge_functions())
    sys.exit(0 if result else 1)