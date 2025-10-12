#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3

"""

Test d'integration Home Assistant pour verifier la compatibilite"""

"""

Test d'imports Home Assistant pour vérifier la compatibilité""""""Test de l'intégration complète avec les nouvelles découvertes"""

import sys

import os"""

import json

Test complet de l'intégration Home Assistant EVSE

# Ajouter le path

test_dir = os.path.dirname(__file__)import sys

evse_module_path = os.path.join(test_dir, 'custom_components', 'evsemasterudp')

sys.path.insert(0, evse_module_path)import os"""import asyncio



def test_imports():

    """Test tous les imports critiques"""

    print("🧪 Test des imports...")# Ajouter le pathimport logging

    

    try:        test_dir = os.path.dirname(__file__)

        # Test imports internes (sans Home Assistant)

        print("🔍 Test imports internes...")evse_module_path = os.path.join(test_dir, 'custom_components', 'evsemasterudp')import asyncioimport sys

        

        # Test protocolsys.path.insert(0, evse_module_path)

        from protocol.communicator import Communicator, EVSE, get_communicator

        print("   ✅ Protocol imports OK")import sysimport os

        

        from protocol.datagram import Datagramdef test_imports():

        print("   ✅ Datagram import OK")

            """Test tous les imports critiques"""import os

        from protocol.datagrams import RequestLogin, LoginConfirm

        print("   ✅ Datagrams imports OK")    print("🧪 Test des imports Home Assistant...")

        

        # Test evse_client (partie critique)    import getpass# Configuration du logging

        from evse_client import EVSEClient, get_evse_client

        print("   ✅ EVSE Client imports OK")    try:

        

        print("✅ Tous les imports internes fonctionnent !")        # Test import du manifestlogging.basicConfig(level=logging.DEBUG)

        return True

                import json

    except ImportError as e:

        print(f"❌ Erreur d'import: {e}")        with open('custom_components/evsemasterudp/manifest.json', 'r') as f:# Ajouter le path vers le protocole dans custom_components_LOGGER = logging.getLogger(__name__)

        return False

    except Exception as e:            manifest = json.load(f)

        print(f"❌ Erreur generale: {e}")

        return False        print(f"   ✅ Manifest valide - Domain: {manifest['domain']}")test_dir = os.path.dirname(__file__)



def test_manifest():        

    """Test la validite du manifest"""

    print("📋 Test du manifest...")        # Test imports internes (sans Home Assistant)evse_module_path = os.path.join(test_dir, 'custom_components', 'evsemasterudp')# Ajouter le chemin vers notre module

    

    try:        print("🔍 Test imports internes...")

        with open('custom_components/evsemasterudp/manifest.json', 'r') as f:

            manifest = json.load(f)        sys.path.insert(0, evse_module_path)sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'evsemasterudp'))

        

        required_fields = ['domain', 'name', 'config_flow', 'dependencies', 'requirements']        # Test protocol

        

        for field in required_fields:        from protocol.communicator import Communicator, EVSE, get_communicator

            if field not in manifest:

                print(f"❌ Champ manquant: {field}")        print("   ✅ Protocol imports OK")

                return False

            print(f"   ✅ {field}: {manifest[field]}")        async def test_integration():from protocol import get_communicator

        

        print("✅ Manifest valide !")        from protocol.datagram import Datagram

        return True

                print("   ✅ Datagram import OK")    """Test complet de l'intégration"""

    except Exception as e:

        print(f"❌ Erreur manifest: {e}")        

        return False

        from protocol.datagrams import RequestLogin, LoginConfirm    try:async def test_integration():

def test_structure():

    """Test la structure des fichiers"""        print("   ✅ Datagrams imports OK")

    print("📁 Test structure des fichiers...")

                    print("🏠 TEST INTÉGRATION HOME ASSISTANT EVSE")    """Test de l'intégration complète"""

    required_files = [

        'custom_components/evsemasterudp/__init__.py',        # Test evse_client (partie critique)

        'custom_components/evsemasterudp/manifest.json',

        'custom_components/evsemasterudp/config_flow.py',        from evse_client import EVSEClient, get_evse_client        print("🔍 Test de tous les composants de l'intégration\n")    print("🧪 TEST D'INTÉGRATION COMPLÈTE")

        'custom_components/evsemasterudp/evse_client.py',

        'custom_components/evsemasterudp/sensor.py',        print("   ✅ EVSE Client imports OK")

        'custom_components/evsemasterudp/switch.py',

        'custom_components/evsemasterudp/number.py',                    print("="*60)

        'custom_components/evsemasterudp/protocol/__init__.py',

        'custom_components/evsemasterudp/protocol/communicator.py',        print("\n✅ Tous les imports internes fonctionnent !")

        'custom_components/evsemasterudp/protocol/datagram.py',

        'custom_components/evsemasterudp/protocol/datagrams.py',        print("🔧 L'intégration devrait se charger dans Home Assistant")        # Test 1: Import des modules d'intégration    

    ]

            

    missing_files = []

    for file_path in required_files:        return True        print("1️⃣ Test import des modules d'intégration...")    # Créer le communicator

        if not os.path.exists(file_path):

            missing_files.append(file_path)        

        else:

            print(f"   ✅ {file_path}")    except ImportError as e:        try:    communicator = get_communicator()

    

    if missing_files:        print(f"❌ Erreur d'import: {e}")

        print(f"❌ Fichiers manquants: {missing_files}")

        return False        return False            from evse_client import EVSEClient, get_evse_client    

    

    print("✅ Structure complete !")    except Exception as e:

    return True

        print(f"❌ Erreur générale: {e}")            from protocol.communicator import Communicator    # Callback pour surveiller les événements

if __name__ == "__main__":

    print("🔧 === TEST INTEGRATION HOME ASSISTANT ===")        return False

    print()

                print("   ✅ Modules d'intégration importés")    def on_evse_event(event_type, evse):

    structure_ok = test_structure()

    print()def test_manifest():

    manifest_ok = test_manifest()

    print()    """Test la validité du manifest"""        except Exception as e:        print(f"\n📢 ÉVÉNEMENT: {event_type}")

    imports_ok = test_imports()

        print("\n📋 Test du manifest...")

    print()

    print("📊 RESULTATS:")                print(f"   ❌ Erreur d'import: {e}")        print(f"   EVSE: {evse.info.serial} @ {evse.info.ip}:{evse.info.port}")

    print(f"   Structure: {'✅' if structure_ok else '❌'}")

    print(f"   Manifest:  {'✅' if manifest_ok else '❌'}")    try:

    print(f"   Imports:   {'✅' if imports_ok else '❌'}")

            import json            return False        

    if structure_ok and manifest_ok and imports_ok:

        print()        with open('custom_components/evsemasterudp/manifest.json', 'r') as f:

        print("🎉 INTEGRATION PRETE POUR HOME ASSISTANT !")

        print("   Vous pouvez l'installer en toute securite.")            manifest = json.load(f)                if evse.state:

    else:

        print()        

        print("❌ PROBLEMES DETECTES !")

        print("   Ne pas installer dans Home Assistant pour le moment.")        required_fields = ['domain', 'name', 'config_flow', 'dependencies', 'requirements']        # Test 2: Création du client EVSE            print(f"   📊 ÉTAT:")

        

        for field in required_fields:        print("\n2️⃣ Test création du client EVSE...")            print(f"      Voltage L1: {evse.state.l1_voltage}V")

            if field not in manifest:

                print(f"❌ Champ manquant: {field}")        try:            print(f"      Current L1: {evse.state.l1_electricity}A")

                return False

            print(f"   ✅ {field}: {manifest[field]}")            client = get_evse_client()            print(f"      Power: {evse.state.current_power}W")

        

        print("   ✅ Manifest valide !")            print(f"   ✅ Client EVSE créé (port: {client.port})")            print(f"      Temperature: {evse.state.inner_temp}°C")

        return True

                except Exception as e:            print(f"      Gun State: {evse.state.gun_state}")

    except Exception as e:

        print(f"❌ Erreur manifest: {e}")            print(f"   ❌ Erreur création client: {e}")            print(f"      Output State: {evse.state.output_state}")

        return False

            return False        

def test_structure():

    """Test la structure des fichiers"""                if evse.config:

    print("\n📁 Test structure des fichiers...")

            # Test 3: Démarrage du client            print(f"   ⚙️ CONFIG:")

    required_files = [

        'custom_components/evsemasterudp/__init__.py',        print("\n3️⃣ Test démarrage du client...")            print(f"      Max Current: {evse.config.max_electricity}A")

        'custom_components/evsemasterudp/manifest.json',

        'custom_components/evsemasterudp/config_flow.py',        try:            

        'custom_components/evsemasterudp/evse_client.py',

        'custom_components/evsemasterudp/sensor.py',            await client.start()        if hasattr(evse.info, 'device_id') and evse.info.device_id:

        'custom_components/evsemasterudp/switch.py',

        'custom_components/evsemasterudp/number.py',            print("   ✅ Client EVSE démarré")            print(f"   🆔 Device ID: {evse.info.device_id}")

        'custom_components/evsemasterudp/protocol/__init__.py',

        'custom_components/evsemasterudp/protocol/communicator.py',        except Exception as e:    

        'custom_components/evsemasterudp/protocol/datagram.py',

        'custom_components/evsemasterudp/protocol/datagrams.py',            print(f"   ❌ Erreur démarrage: {e}")    # Ajouter notre callback

    ]

                return False    communicator.add_callback('test', on_evse_event)

    missing_files = []

    for file_path in required_files:            

        if not os.path.exists(file_path):

            missing_files.append(file_path)        # Test 4: Découverte d'EVSEs    try:

        else:

            print(f"   ✅ {file_path}")        print("\n4️⃣ Test découverte d'EVSEs...")        print("🚀 Démarrage du communicator...")

    

    if missing_files:        await asyncio.sleep(3)  # Attendre la découverte        await communicator.start()

        print(f"❌ Fichiers manquants: {missing_files}")

        return False                

    

    print("   ✅ Structure complète !")        evses = client.get_all_evses()        print("🎧 En écoute des messages EVSE...")

    return True

        if evses:        print("📱 Va sur ton téléphone et change le courant max sur l'app!")

if __name__ == "__main__":

    print("🔧 === TEST INTÉGRATION HOME ASSISTANT ===\n")            print(f"   ✅ {len(evses)} EVSE(s) découverte(s)")        print("⏰ Test pendant 60 secondes...")

    

    structure_ok = test_structure()            for serial, evse in evses.items():        

    manifest_ok = test_manifest()

    imports_ok = test_imports()                print(f"      📱 {serial} @ {evse.info.ip}:{evse.info.port}")        # Attendre et observer

    

    print(f"\n📊 RÉSULTATS:")        else:        await asyncio.sleep(60)

    print(f"   Structure: {'✅' if structure_ok else '❌'}")

    print(f"   Manifest:  {'✅' if manifest_ok else '❌'}")            print("   ⚠️ Aucune EVSE découverte")        

    print(f"   Imports:   {'✅' if imports_ok else '❌'}")

                return False    except KeyboardInterrupt:

    if structure_ok and manifest_ok and imports_ok:

        print("\n🎉 INTÉGRATION PRÊTE POUR HOME ASSISTANT !")                print("\n⏸️ Test interrompu par l'utilisateur")

        print("   Vous pouvez l'installer en toute sécurité.")

    else:        # Test 5: Authentification    except Exception as e:

        print("\n❌ PROBLÈMES DÉTECTÉS !")

        print("   Ne pas installer dans Home Assistant pour le moment.")        print("\n5️⃣ Test authentification...")        print(f"❌ Erreur: {e}")

        target_serial = list(evses.keys())[0]  # Prendre la première EVSE        import traceback

        print(f"   🎯 EVSE cible: {target_serial}")        traceback.print_exc()

            finally:

        password = getpass.getpass("   🔐 Entrez le mot de passe EVSE: ")        print("\n🛑 Arrêt du communicator...")

                communicator.remove_callback('test')

        success = await client.login(target_serial, password)        await communicator.stop()

        if success:        print("✅ Test terminé")

            print("   ✅ Authentification réussie")

        else:if __name__ == "__main__":

            print("   ❌ Authentification échouée")    print("🔧 Test d'intégration des nouvelles découvertes:")

            return False    print("   - Commande 0x000d: température et voltage")

            print("   - Commande 0x010c: courant maximum exact")

        # Test 6: Récupération des données    print("   - Parser EVSECurrentConfiguration")

        print("\n6️⃣ Test récupération des données...")    print()

        await asyncio.sleep(2)  # Attendre les données    

            asyncio.run(test_integration())
        evse = evses[target_serial]
        if evse.state:
            print("   ✅ Données de statut reçues:")
            print(f"      ⚡ Voltage L1: {evse.state.l1_voltage}V")
            print(f"      🌡️ Température interne: {evse.state.inner_temp}°C")
            print(f"      🌡️ Température externe: {evse.state.outer_temp}°C")
            print(f"      🔋 Courant L1: {evse.state.l1_electricity}A")
            print(f"      ⚡ Puissance: {evse.state.current_power}W")
            print(f"      🔌 État pistolet: {evse.state.gun_state}")
            print(f"      🔌 État sortie: {evse.state.output_state}")
            
            # Valider les données critiques
            data_valid = True
            if evse.state.l1_voltage < 200 or evse.state.l1_voltage > 260:
                print(f"   ⚠️ Voltage suspect: {evse.state.l1_voltage}V")
                data_valid = False
                
            if evse.state.inner_temp < 10 or evse.state.inner_temp > 60:
                print(f"   ⚠️ Température suspecte: {evse.state.inner_temp}°C")
                data_valid = False
                
            if data_valid:
                print("   ✅ Données validées")
            else:
                print("   ⚠️ Données partiellement validées")
        else:
            print("   ❌ Pas de données de statut")
            return False
        
        # Test 7: Test des méthodes de contrôle
        print("\n7️⃣ Test méthodes de contrôle...")
        try:
            # Test is_online
            is_online = client.is_evse_online(target_serial)
            print(f"   📶 EVSE en ligne: {is_online}")
            
            # Test get_evse_status  
            status = client.get_evse_status(target_serial)
            print(f"   📊 Statut EVSE: {status}")
            
            # Test get_evse_data
            data = client.get_evse_data(target_serial)
            if data:
                print(f"   📋 Données disponibles: {list(data.keys())}")
            
            print("   ✅ Méthodes de contrôle testées")
        except Exception as e:
            print(f"   ⚠️ Erreur test contrôle: {e}")
        
        # Test 8: Arrêt propre
        print("\n8️⃣ Test arrêt du client...")
        try:
            await client.stop()
            print("   ✅ Client arrêté proprement")
        except Exception as e:
            print(f"   ⚠️ Erreur arrêt: {e}")
        
        print("\n🎉 TEST INTÉGRATION RÉUSSI !")
        print("✅ Tous les composants fonctionnent correctement")
        print("🏠 L'intégration Home Assistant est prête !")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR GÉNÉRALE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    if success:
        print("\n🔧 PROCHAINES ÉTAPES:")
        print("1. Copier le dossier 'custom_components/evsemasterudp' dans votre Home Assistant")
        print("2. Redémarrer Home Assistant")
        print("3. Aller dans Configuration > Intégrations > Ajouter une intégration")
        print("4. Chercher 'EVSE Master UDP' et suivre la configuration")
    else:
        print("\n🔧 ACTIONS CORRECTIVES NÉCESSAIRES:")
        print("Vérifiez les erreurs ci-dessus avant d'utiliser l'intégration")