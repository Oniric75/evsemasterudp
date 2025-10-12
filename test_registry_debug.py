#!/usr/bin/env python3
"""
Test debug des commandes enregistrées
"""

import sys
import os

# Ajouter le path
test_dir = os.path.dirname(__file__)
evse_module_path = os.path.join(test_dir, 'custom_components', 'evsemasterudp')
sys.path.insert(0, evse_module_path)

def test_registry():
    """Vérifier le registre des commandes"""
    try:
        # Importer pour déclencher l'enregistrement
        from protocol.datagram import DATAGRAM_TYPES
        import protocol.datagrams  # Force l'import pour l'enregistrement
        
        print("📋 Commandes enregistrées:")
        for cmd, cls in sorted(DATAGRAM_TYPES.items()):
            print(f"   0x{cmd:04x} ({cmd:5d}) -> {cls.__name__}")
        
        print(f"\n📊 Total: {len(DATAGRAM_TYPES)} commandes")
        
        # Vérifier spécifiquement 0x0002
        if 0x0002 in DATAGRAM_TYPES:
            print(f"✅ 0x0002 trouvée: {DATAGRAM_TYPES[0x0002].__name__}")
        else:
            print("❌ 0x0002 manquante!")
            
        # Vérifier 0x0005
        if 0x0005 in DATAGRAM_TYPES:
            print(f"✅ 0x0005 trouvée: {DATAGRAM_TYPES[0x0005].__name__}")
        else:
            print("❌ 0x0005 manquante!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_registry()