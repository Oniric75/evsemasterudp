#!/usr/bin/env python3
"""
Test complet d'authentification et communication EVSE
"""

import asyncio
import sys
import os
import getpass

# Ajouter le path vers le protocole dans custom_components
# Utilise le chemin relatif depuis ce fichier
test_dir = os.path.dirname(__file__)
project_root = os.path.dirname(test_dir)
evse_module_path = os.path.join(project_root, 'custom_components', 'evsemasterudp')
sys.path.insert(0, evse_module_path)

async def test_full_communication():
    """Test communication complète avec EVSE"""
    try:
        from protocol.communicator import Communicator
        from protocol.datagrams import RequestLogin, Heading
        
        print("🔍 Démarrage découverte et communication EVSE...")
        comm = Communicator()
        port = await comm.start()
        print(f"   ✅ Écoute sur port {port}")
        
        print("⏳ Attente de découverte EVSE (5s)...")
        
        # Attendre découverte
        evse = None
        for i in range(5):
            await asyncio.sleep(1.0)
            if comm.evses:
                evse = list(comm.evses.values())[0]
                print(f"   🎯 EVSE trouvée: {evse.info.serial} @ {evse.info.ip}")
                break
        
        if not evse:
            print("❌ Aucun EVSE découvert")
            return False
        
        # Demander le mot de passe de manière interactive
        print(f"\n🔑 EVSE détecté: {evse.info.serial}")
        password = getpass.getpass("🔐 Entrez le mot de passe EVSE: ")
        print(f"   ✅ Mot de passe saisi")

        # Test authentification avec la nouvelle méthode
        print("🔐 Test authentification...")
        auth_success = await evse.login(password)
        
        if auth_success:
            print("   🎉 Authentification réussie !")
        else:
            print("   ❌ Authentification échouée")
        
        # Test récupération du statut (seulement si connecté)
        print("📊 Test récupération du statut...")
        if auth_success:
            # Attendre un peu pour que les données arrivent
            await asyncio.sleep(2.0)
        else:
            print("   ⚠️ Pas connecté - test du statut ignoré")
        
        # Attendre la réponse
        await asyncio.sleep(2.0)
        
        if evse.state:
            print("   🎉 Statut reçu !")
            print(f"      ⚡ Gun state: {evse.state.gun_state}")
            print(f"      🔌 Output state: {evse.state.output_state}")
            print(f"      📏 Voltage L1: {getattr(evse.state, 'l1_voltage', 'N/A')}V")
            print(f"      🔋 Current L1: {getattr(evse.state, 'l1_current', 'N/A')}A")
            print(f"      🌡️ Temp inner: {getattr(evse.state, 'inner_temp', 'N/A')}°C")
            print(f"      🌡️ Temp outer: {getattr(evse.state, 'outer_temp', 'N/A')}°C")
        else:
            print("   ⚠️ Aucun statut reçu")
        
        print("\n🛑 Arrêt du communicateur...")
        await comm.stop()
        print("   ✅ Arrêté")
        
        # Évaluer le succès réel du test
        data_received = evse.state is not None if hasattr(evse, 'state') else False
        
        print(f"\n📊 RÉSULTATS RÉELS:")
        print(f"   🔐 Authentification: {'✅ Réussie' if auth_success else '❌ Échouée'}")
        print(f"   📡 Données reçues: {'✅ Oui' if data_received else '❌ Non'}")
        
        if data_received:
            print(f"   📋 DONNÉES RÉCUPÉRÉES:")
            print(f"      ⚡ Voltage L1: {getattr(evse.state, 'l1_voltage', 'N/A')}V")
            print(f"      🌡️ Température: {getattr(evse.state, 'inner_temp', 'N/A')}°C") 
            print(f"      🔋 Current L1: {getattr(evse.state, 'l1_current', 'N/A')}A")
        
        return auth_success and data_received
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Test complet communication EVSE Python")
    print("🔌 Test: Découverte → Authentification → Statut")
    print("📱 Le test va découvrir votre EVSE et vous demander le mot de passe\n")
    
    success = asyncio.run(test_full_communication())
    
    if success:
        print("\n🎉 Test complet réussi ! Le protocole Python fonctionne parfaitement.")
        print("   ✅ Découverte automatique")
        print("   ✅ Authentification réussie") 
        print("   ✅ Données reçues (voltage, température, current)")
        print("\n🏠 Votre intégration Home Assistant est prête !")
    else:
        print("\n❌ Test échoué - vérifiez:")
        print("   🔐 Le mot de passe EVSE")
        print("   📡 La connexion réseau")
        print("   🔌 L'état de l'EVSE")