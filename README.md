# EVSE Master UDP - Home Assistant Integration

🔌 **Intégration Home Assistant pour bornes de recharge compatibles EVSE Master UDP**

Cette intégration permet de contrôler et surveiller votre borne de recharge EVSE depuis Home Assistant via le protocole UDP utilisé par l'application mobile "EVSE Master".

## ⚠️ Avertissements Importants

> **PROTECTION DE L'ÉQUIPEMENT** : Les démarrages répétés de charge peuvent user prématurément les contacteurs de votre borne. Cette intégration inclut des protections automatiques, mais **l'utilisation reste à vos propres risques**.

**Protections intégrées** :
- 🛡️ **Protection contre les changements rapides** : Empêche les démarrages/arrêts trop fréquents (délai minimum 5 min)
- 🔒 **Fallback de sécurité 16A** : En cas d'erreur, limite automatiquement à 16A
- ⏱️ **Délai minimum entre cycles** : Respecte un temps minimum entre les opérations

**Recommandations** :
- Évitez les démarrages/arrêts fréquents (< 5 minutes d'intervalle)
- Planifiez vos automations pour éviter les cycles rapides
- Surveillez l'état de santé de votre équipement

## 🏗️ Compatibilité

**Bornes testées et compatibles** :
- **Morec** (toutes les bornes utilisant l'app "EVSE Master")
- **Bornes EVSE génériques** utilisant le protocole UDP sur le port 28376
- **Bornes chinoises** configurables via l'app EVSE Master

## 🚀 Installation

### Méthode 1 : HACS (Recommandée)

1. Ouvrez HACS dans Home Assistant
2. Allez dans "Intégrations"
3. Cliquez sur les 3 points en haut à droite → "Dépôts personnalisés"
4. Ajoutez `https://github.com/Oniric75/evsemasterudp` comme dépôt de type "Integration"
5. Recherchez "EVSE Master UDP" dans HACS
6. Installez l'intégration
7. Redémarrez Home Assistant

### Méthode 2 : Installation Manuelle

1. Téléchargez la [dernière release](https://github.com/Oniric75/evsemasterudp/releases)
2. Extrayez le dossier `evsemasterudp` dans `custom_components/`
3. Redémarrez Home Assistant

## ⚙️ Configuration

1. Allez dans **Configuration** → **Intégrations**
2. Cliquez sur **"Ajouter une intégration"**
3. Recherchez **"EVSE Master UDP"**
4. Suivez l'assistant de configuration :
   - La découverte automatique détectera votre borne
   - Entrez le mot de passe de votre borne EVSE
   - Configurez la fréquence de mise à jour (recommandé : 30 secondes)

## 📊 Entités Créées

### Capteurs (Sensors)
- `sensor.evse_status` - Statut général de la borne
- `sensor.evse_power` - Puissance actuelle (W)
- `sensor.evse_current` - Courant actuel (A)
- `sensor.evse_voltage` - Tension (V)
- `sensor.evse_temperature` - Température de la borne (°C)
- `sensor.evse_session_energy` - Énergie de la session en cours (kWh)
- `sensor.evse_total_energy` - Énergie totale (kWh)

### Interrupteurs (Switches)
- `switch.evse_charging` - Contrôle marche/arrêt de la charge
- `switch.evse_offline_charge` - Mode charge hors ligne

### Contrôles Numériques (Numbers)
- `number.evse_max_current` - Courant maximum (A)
- `number.evse_charge_fee` - Tarif de charge
- `number.evse_service_fee` - Frais de service

## 🛠️ Fonctionnalités

- 🔍 **Découverte automatique** des bornes EVSE sur le réseau local
- 🔐 **Authentification sécurisée** avec mot de passe
- 📊 **Surveillance en temps réel** du statut de charge
- ⚡ **Contrôle de la charge** (démarrage/arrêt)
- 🔢 **Configuration des paramètres** (courant max, température, etc.)
- 📈 **Historique des sessions** de charge
- 🛡️ **Protections intégrées** contre l'usure prématurée

## 🔧 Configuration Avancée

### Paramètres disponibles dans l'interface :
- **Fréquence de mise à jour** : 15-300 secondes (défaut: 30s)
- **Timeout de connexion** : 5-30 secondes (défaut: 10s)
- **Protection contre les changements rapides** : activée par défaut
- **Délai minimum entre cycles** : 5 minutes (configurable)

## 📚 Exemples d'Automatisations

### Démarrage de charge basé sur les tarifs électriques

```yaml
automation:
  - alias: "Charge EVSE heures creuses"
    trigger:
      - platform: time
        at: "22:30:00"  # Début heures creuses
    condition:
      - condition: state
        entity_id: binary_sensor.vehicle_connected
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.evse_charging
```

### Arrêt automatique à 80% de batterie

```yaml
automation:
  - alias: "Arrêt charge 80%"
    trigger:
      - platform: numeric_state
        entity_id: sensor.vehicle_battery_level
        above: 80
    action:
      - service: switch.turn_off
        entity_id: switch.evse_charging
```

## 🆘 Support et Problèmes

- 📋 [Signaler un bug](https://github.com/Oniric75/evsemasterudp/issues)
- 💬 [Discussions](https://github.com/Oniric75/evsemasterudp/discussions)
- 📖 [Wiki et documentation](https://github.com/Oniric75/evsemasterudp/wiki)

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👨‍💻 Développement

<details>
<summary>Informations pour les développeurs</summary>

### Structure du Projet

```
evsemasterudp/
├── __init__.py          # Point d'entrée de l'intégration
├── manifest.json        # Métadonnées de l'intégration
├── config_flow.py       # Interface de configuration
├── evse_client.py       # Client principal EVSE
├── sensor.py           # Capteurs
├── switch.py           # Interrupteurs
├── number.py           # Contrôles numériques
├── protocol/           # Implémentation du protocole
│   ├── __init__.py
│   ├── communicator.py # Communication UDP
│   ├── datagram.py    # Structure des datagrammes
│   └── datagrams.py   # Types de messages
└── tests/             # Tests unitaires
    ├── test_basic.py
    ├── test_discovery.py
    └── test_full.py
```

### Protocole UDP EVSE Master

- **Port par défaut** : 28376
- **Communication** : Bidirectionnelle UDP
- **Authentification** : Mot de passe en clair
- **Découverte** : Broadcast automatique

### Tests de Développement

```bash
# Activer l'environnement virtuel
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Tests basiques
python tests/test_basic.py

# Test de découverte
python tests/test_discovery.py

# Test complet avec vraie borne
python tests/test_full.py
```

### Prérequis pour le Développement

- Python 3.11+
- Home Assistant Core 2024.1+
- Une borne EVSE compatible sur le réseau local

### Contributions

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/amazing-feature`)
3. Committez vos changements (`git commit -m 'Add amazing feature'`)
4. Pushez vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

</details>

---

## 🙏 Remerciements

Ce projet est basé sur le travail original de [johnwoo-nl/emproto](https://github.com/johnwoo-nl/emproto) et a été porté et étendu pour Home Assistant.


