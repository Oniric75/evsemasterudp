# EVSE Master UDP - Home Assistant Integration

> **🌐 This README is available in two languages / Ce README est disponible en deux langues :**
> - [🇺🇸 **English Version**](#-english-version) (below / ci-dessous)
> - [🇫🇷 **Version Française**](#-version-française) (scroll down / plus bas)

---

## 📋 Table of Contents / Table des Matières
- [🇺🇸 English Version](#-english-version)
- [🇫🇷 Version Française](#-version-française)

---

# 🇺🇸 English Version

🔌 **Home Assistant Integration for EVSE Master UDP compatible charging stations**

This integration allows you to control and monitor your EVSE charging station from Home Assistant via the UDP protocol used by the "EVSE Master" mobile application.

## ⚠️ Important Warnings

> **EQUIPMENT PROTECTION**: Repeated charge starts can prematurely wear out your charging station's contactors. This integration includes automatic protections, but **use is at your own risk**.

**Built-in protections**:
- 🛡️ **Rapid change protection**: Prevents too frequent starts/stops (5 min minimum delay)
- 🔒 **16A safety fallback**: In case of error, automatically limits to 16A
- ⏱️ **Minimum delay between cycles**: Respects minimum time between operations

**Recommendations**:
- Avoid frequent starts/stops (< 5 minutes interval)
- Plan your automations to avoid rapid cycles
- Monitor your equipment's health status

## 🏗️ Compatibility

**Tested and compatible charging stations**:
- **Morec** (all stations using the "EVSE Master" app)
- **Generic EVSE stations** using UDP protocol on port 28376
- **Chinese stations** configurable via EVSE Master app

## 🚀 Installation

### Method 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the 3 dots in the top right → "Custom repositories"
4. Add `https://github.com/Oniric75/evsemasterudp` as a repository of type "Integration"
5. Search for "EVSE Master UDP" in HACS
6. Install the integration
7. Restart Home Assistant

### Method 2: Manual Installation

1. Download the [latest release](https://github.com/Oniric75/evsemasterudp/releases)
2. Extract the `evsemasterudp` folder to `custom_components/`
3. Restart Home Assistant

## ⚙️ Configuration

1. Go to **Configuration** → **Integrations**
2. Click **"Add Integration"**
3. Search for **"EVSE Master UDP"**
4. Follow the configuration wizard:
   - Automatic discovery will detect your charging station
   - Enter your EVSE station password
   - Configure update frequency (recommended: 30 seconds)

## 📊 Created Entities

### Sensors
- `sensor.evse_status` - General station status
- `sensor.evse_power` - Current power (W)
- `sensor.evse_current` - Current amperage (A)
- `sensor.evse_voltage` - Voltage (V)
- `sensor.evse_temperature` - Station temperature (°C)
- `sensor.evse_session_energy` - Current session energy (kWh)
- `sensor.evse_total_energy` - Total energy (kWh)

### Switches
- `switch.evse_charging` - Charging on/off control
- `switch.evse_offline_charge` - Offline charging mode

### Number Controls
- `number.evse_max_current` - Maximum current (A)
- `number.evse_charge_fee` - Charging rate
- `number.evse_service_fee` - Service fee

## 🛠️ Features

- 🔍 **Automatic discovery** of EVSE stations on local network
- 🔐 **Secure authentication** with password
- 📊 **Real-time monitoring** of charging status
- ⚡ **Charging control** (start/stop)
- 🔢 **Parameter configuration** (max current, temperature, etc.)
- 📈 **Charging session history**
- 🛡️ **Built-in protections** against premature wear

## 🔧 Advanced Configuration

### Available settings in the interface:
- **Update frequency**: 15-300 seconds (default: 30s)
- **Connection timeout**: 5-30 seconds (default: 10s)
- **Rapid change protection**: enabled by default
- **Minimum delay between cycles**: 5 minutes (configurable)

## 📚 Automation Examples

### Charging start based on electricity rates

```yaml
automation:
  - alias: "EVSE charge during off-peak hours"
    trigger:
      - platform: time
        at: "22:30:00"  # Off-peak hours start
    condition:
      - condition: state
        entity_id: binary_sensor.vehicle_connected
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.evse_charging
```

### Automatic stop at 80% battery

```yaml
automation:
  - alias: "Stop charge at 80%"
    trigger:
      - platform: numeric_state
        entity_id: sensor.vehicle_battery_level
        above: 80
    action:
      - service: switch.turn_off
        entity_id: switch.evse_charging
```

## 🆘 Support and Issues

- 📋 [Report a bug](https://github.com/Oniric75/evsemasterudp/issues)
- 💬 [Discussions](https://github.com/Oniric75/evsemasterudp/discussions)
- 📖 [Wiki and documentation](https://github.com/Oniric75/evsemasterudp/wiki)

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Development

<details>
<summary>Developer Information</summary>

### Project Structure

```
evsemasterudp/
├── __init__.py          # Integration entry point
├── manifest.json        # Integration metadata
├── config_flow.py       # Configuration interface
├── evse_client.py       # Main EVSE client
├── sensor.py           # Sensors
├── switch.py           # Switches
├── number.py           # Number controls
├── protocol/           # Protocol implementation
│   ├── __init__.py
│   ├── communicator.py # UDP communication
│   ├── datagram.py    # Datagram structure
│   └── datagrams.py   # Message types
└── tests/             # Unit tests
    ├── test_basic.py
    ├── test_discovery.py
    └── test_full.py
```

### EVSE Master UDP Protocol

- **Default port**: 28376
- **Communication**: Bidirectional UDP
- **Authentication**: Plain text password
- **Discovery**: Automatic broadcast

### Development Testing

```bash
# Activate virtual environment
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Basic tests
python tests/test_basic.py

# Discovery test
python tests/test_discovery.py

# Full test with real station
python tests/test_full.py
```

### Development Requirements

- Python 3.11+
- Home Assistant Core 2024.1+
- A compatible EVSE station on the local network

### Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

</details>

---

# 🇫🇷 Version Française

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


