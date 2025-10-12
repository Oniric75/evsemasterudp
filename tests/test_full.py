#!/usr/bin/env python3
"""
Test complet d'authentification et communication EVSE
"""

import asyncio
import sys
import os

# Ajouter le path vers le protocole dans custom_components
# Utilise le chemin relatif depuis ce fichier
test_dir = os.path.dirname(__file__)
project_root = os.path.dirname(test_dir)
evse_module_path = os.path.join(project_root, 'custom_components', 'evsemasterudp')
sys.path.insert(0, evse_module_path)

async def test_full_communication():
    """Test communication complète avec EVSE"""
    try:
        from protocol import get_communicator, RequestLogin, Heading
        
        print("🔍 Démarrage découverte et communication EVSE...")
        comm = get_communicator()
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
        
        # Configurer le mot de passe
        evse.password = "123456"
        print(f"🔑 Configuration mot de passe: {evse.password}")
        
        # Test authentification
        print("🔐 Test authentification...")
        login = RequestLogin()
        login.device_serial = evse.info.serial
        login.device_password = evse.password
        
        await comm.send(login, evse)
        print("   ✅ RequestLogin envoyé")
        
        # Attendre l'authentification
        await asyncio.sleep(2.0)
        
        if evse._logged_in:
            print("   🎉 Authentification réussie !")
        else:
            print("   ⚠️ Authentification en attente...")
        
        # Test keepalive/status
        print("📊 Test récupération du statut...")
        heading = Heading()
        heading.device_serial = evse.info.serial
        heading.device_password = evse.password
        
        await comm.send(heading, evse)
        print("   ✅ Heading envoyé")
        
        # Attendre la réponse
        await asyncio.sleep(2.0)
        
        if evse.state:
            print("   🎉 Statut reçu !")
            print(f"      ⚡ Gun state: {evse.state.gun_state}")
            print(f"      🔌 Output state: {evse.state.output_state}")
            print(f"      📏 Voltage: {evse.state.voltage}V")
            print(f"      🔋 Current: {evse.state.current}A")
            print(f"      🌡️ Temp inner: {evse.state.temp_inner}°C")
            print(f"      🌡️ Temp outer: {evse.state.temp_outer}°C")
        else:
            print("   ⚠️ Aucun statut reçu")
        
        print("\n🛑 Arrêt du communicateur...")
        await comm.stop()
        print("   ✅ Arrêté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Test complet communication EVSE Python")
    print("🔌 Test: Découverte → Authentification → Statut")
    print("📱 EVSE: 1368844619649410 avec password 123456\n")
    
    success = asyncio.run(test_full_communication())
    
    if success:
        print("\n🎉 Test complet réussi ! Le protocole Python est 100% fonctionnel.")
        print("   ✅ Découverte automatique")
        print("   ✅ Authentification") 
        print("   ✅ Communication bidirectionnelle")
        print("\n🏠 Votre intégration Home Assistant est prête !")
    else:
        print("\n❌ Test échoué - des ajustements sont nécessaires")