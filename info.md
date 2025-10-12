# EVSE Master UDP - Instructions post-installation

## 📥 Après l'installation

1. **Redémarrez Home Assistant** complètement (pas seulement recharger)
2. Allez dans **Paramètres > Appareils et services**
3. Cliquez sur **"+ Ajouter une intégration"**
4. Recherchez **"EVSE Master UDP"**
5. Suivez l'assistant de configuration

## ⚠️ Important

Cette intégration nécessite un **redémarrage complet** de Home Assistant après l'installation pour garantir un fonctionnement optimal.

## 🔧 Configuration

- **Serial** : Numéro de série de votre EVSE (ex: 1368845689849510)
- **Password** : Mot de passe de votre EVSE (défaut: 123456)
- **Port** : Port UDP (défaut: 28376)

## 🏠 Entités créées

- **Capteurs** : État, tension, température, puissance
- **Interrupteurs** : Démarrage/arrêt de charge
- **Contrôles** : Ampérage de charge, minuteur

## 🐛 Dépannage

Si vous rencontrez des problèmes de connexion :
1. Vérifiez que votre EVSE est sur le même réseau
2. Redémarrez Home Assistant
3. Consultez les logs dans **Paramètres > Système > Logs**