#!/usr/bin/env python3
"""
Test de la fonction set_max_electricity en Python
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

async def test_set_max_electricity():
    """Test de modification du courant maximum"""
    
    # Configuration
    EVSE_SERIAL = "1368845689849510"
    EVSE_PASSWORD = "091082"  # Correct password
    NEW_CURRENT = 8  # Ampères
    
    print(f"🧪 Test de modification du courant maximum via Python")
    print(f"📱 EVSE: {EVSE_SERIAL}")
    print(f"⚡ Nouveau courant max: {NEW_CURRENT}A")
    
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
        print("✅ EVSE cible trouvée !")
        
        # Connexion
        print("🔐 Authentification...")
        success = await evse.login(EVSE_PASSWORD)
        if not success:
            print("❌ Échec authentification")
            return False
        print("✅ Authentification réussie")
        
        # Attendre un peu pour la stabilisation
        await asyncio.sleep(2)
        
        # Lire config actuelle
        print("📊 Configuration actuelle:")
        print(f"   Courant max actuel: {evse.config.max_electricity}A")
        
        # Modifier le courant
        print(f"⚙️ Modification du courant max à {NEW_CURRENT}A...")
        success = await evse.set_max_electricity(NEW_CURRENT)
        
        if success:
            print("✅ Commande envoyée")
            
            # Attendre un peu puis relire
            await asyncio.sleep(3)
            
            print("📊 Nouvelle configuration:")
            print(f"   Courant max: {evse.config.max_electricity}A")
            
            if evse.config.max_electricity == NEW_CURRENT:
                print("🎉 SUCCESS: Le courant a été modifié avec succès!")
                print("📱 Vérifiez maintenant dans l'app EVSE Master si la valeur a changé")
                return True
            else:
                print(f"⚠️ WARNING: Courant local modifié mais pas confirmé par l'EVSE")
                return False
        else:
            print("❌ Échec de la commande")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if communicator:
            communicator.stop()
            print("🛑 Communicator arrêté")
        print("🏁 Test terminé")

if __name__ == "__main__":
    result = asyncio.run(test_set_max_electricity())
    sys.exit(0 if result else 1)