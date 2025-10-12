#!/usr/bin/env python3
"""
Test simple du protocole EVSE Python
Version minimaliste pour validation rapide
"""

import asyncio
import sys
import os

# Ajouter le path vers le protocole
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

async def test_basic_import():
    """Test import basique"""
    try:
        print("🔍 Test import des modules...")
        
        # Test import datagram
        from protocol.datagram import Datagram
        print("  ✅ Datagram importé")
        
        # Test import communicator
        from protocol.communicator import Communicator, EVSE
        print("  ✅ Communicator importé")
        
        # Test import datagrams
        from protocol.datagrams import RequestLogin, Heading, SingleACStatus
        print("  ✅ Datagrams importés")
        
        return True, None
        
    except Exception as e:
        return False, str(e)

async def test_datagram_creation():
    """Test création de datagrammes"""
    try:
        print("🔧 Test création de datagrammes...")
        
        from protocol.datagrams import RequestLogin, Heading
        
        # Test création RequestLogin
        login = RequestLogin()
        print(f"  ✅ RequestLogin créé (command: 0x{login.COMMAND:04x})")
        
        # Test création Heading
        heading = Heading()
        print(f"  ✅ Heading créé (command: 0x{heading.COMMAND:04x})")
        
        return True, None
        
    except Exception as e:
        return False, str(e)

async def test_datagram_packing():
    """Test encodage/décodage"""
    try:
        print("📦 Test encodage/décodage...")
        
        from protocol.datagrams import RequestLogin
        
        # Créer un datagramme
        login = RequestLogin()
        login.serial = "1368844619649410"
        login.password = "123456"
        
        # Encoder
        packed = login.pack()
        print(f"  ✅ Datagramme encodé ({len(packed)} bytes)")
        print(f"     Hex: {packed.hex()}")
        
        return True, None
        
    except Exception as e:
        return False, str(e)

async def test_communicator_creation():
    """Test création communicateur"""
    try:
        print("📡 Test création communicateur...")
        
        from protocol.communicator import get_communicator
        
        # Créer communicateur
        comm = get_communicator()
        print("  ✅ Communicateur créé")
        print(f"     Port: {comm.port}")
        
        # Nettoyer
        await comm.stop()
        
        return True, None
        
    except Exception as e:
        return False, str(e)

async def test_network_socket():
    """Test création socket UDP"""
    try:
        print("🌐 Test socket UDP...")
        
        import socket
        
        # Créer socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Tester bind
        sock.bind(('', 0))  # Port automatique
        port = sock.getsockname()[1]
        print(f"  ✅ Socket UDP créé sur port {port}")
        
        sock.close()
        
        return True, None
        
    except Exception as e:
        return False, str(e)

async def main():
    """Tests principaux"""
    print("🧪 === TEST RAPIDE PROTOCOLE EVSE PYTHON ===\n")
    
    tests = [
        ("Import des modules", test_basic_import),
        ("Création datagrammes", test_datagram_creation),
        ("Encodage/décodage", test_datagram_packing),
        ("Communicateur", test_communicator_creation),
        ("Socket réseau", test_network_socket),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🔬 {test_name}...")
        try:
            success, error = await test_func()
            if success:
                print(f"   ✅ {test_name} OK\n")
                results.append((test_name, True, None))
            else:
                print(f"   ❌ {test_name} ERREUR: {error}\n")
                results.append((test_name, False, error))
        except Exception as e:
            print(f"   ❌ {test_name} EXCEPTION: {e}\n")
            results.append((test_name, False, str(e)))
    
    # Résumé
    print("=" * 50)
    print("📋 RÉSUMÉ DES TESTS:")
    
    passed = 0
    for test_name, success, error in results:
        status = "✅ OK" if success else "❌ KO"
        print(f"   {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 Résultat: {passed}/{len(tests)} tests réussis")
    
    if passed == len(tests):
        print("\n🎉 Tous les tests basiques passent !")
        print("   Vous pouvez maintenant tester avec un vrai EVSE:")
        print(f"   python test_python_protocol.py")
    else:
        print("\n⚠️ Certains tests échouent - vérifiez la configuration")
        print("   Erreurs détectées:")
        for test_name, success, error in results:
            if not success:
                print(f"     • {test_name}: {error}")

if __name__ == "__main__":
    asyncio.run(main())