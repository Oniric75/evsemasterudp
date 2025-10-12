# EVSE Master UDP - Home Assistant Integration

> **🙏 ACKNOWLEDGMENT / REMERCIEMENTS**
> 
> This project is based on the excellent work of [johnwoo-nl/emproto](https://github.com/johnwoo-nl/emproto). Without their invaluable reverse-engineering of the EVSE Master UDP protocol, this Home Assistant integration would not have been possible. Full credit and thanks to the original author! 🌟
> 
> Ce projet est basé sur l'excellent travail de [johnwoo-nl/emproto](https://github.com/johnwoo-nl/emproto). Sans leur précieux reverse-engineering du protocole UDP EVSE Master, cette intégration Home Assistant n'aurait pas été possible. Tout le crédit et nos remerciements à l'auteur original ! 🌟

---

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
   - Enter your EVSE station serial number (found on device label)
   - Enter your EVSE station password (set in EVSE Master app)
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

## 🐛 Troubleshooting

### Station not detected
1. Verify that the station is powered on
2. Confirm that Home Assistant and the station are on the same network
3. Check that port 28376 is not blocked by firewall

### Authentication failed
1. Verify the password in the EVSE Master app
2. Confirm the station serial number
3. Restart the station if necessary

### Connection lost
1. Check network stability
2. Increase update frequency in configuration
3. Verify there are no network conflicts

## 🆘 Support and Issues

- 📋 [Report a bug](https://github.com/Oniric75/evsemasterudp/issues)
- 💬 [Discussions](https://github.com/Oniric75/evsemasterudp/discussions)
- 📖 [Wiki and documentation](https://github.com/Oniric75/evsemasterudp/wiki)

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

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
   - Entrez le numéro de série de votre borne (trouvé sur l'étiquette de l'appareil)
   - Entrez le mot de passe de votre borne (défini dans l'app EVSE Master)
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

## 🐛 Résolution de Problèmes

### Borne non détectée
1. Vérifiez que la borne est allumée
2. Confirmez que Home Assistant et la borne sont sur le même réseau
3. Vérifiez que le port 28376 n'est pas bloqué par le pare-feu

### Authentification échouée
1. Vérifiez le mot de passe dans l'app EVSE Master
2. Confirmez le numéro de série de la borne
3. Redémarrez la borne si nécessaire

### Perte de connexion
1. Vérifiez la stabilité du réseau
2. Augmentez la fréquence de mise à jour dans la configuration
3. Vérifiez qu'il n'y a pas de conflits réseau

## 🆘 Support et Problèmes

- 📋 [Signaler un bug](https://github.com/Oniric75/evsemasterudp/issues)
- 💬 [Discussions](https://github.com/Oniric75/evsemasterudp/discussions)
- 📖 [Wiki et documentation](https://github.com/Oniric75/evsemasterudp/wiki)

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👨‍💻 Development / Développement

<details>
<summary>🇺🇸 Developer Information / 🇫🇷 Informations pour les développeurs</summary>

### Project Structure / Structure du Projet

```
evsemasterudp/
├── __init__.py          # Integration entry point / Point d'entrée
├── manifest.json        # Integration metadata / Métadonnées
├── config_flow.py       # Configuration interface / Interface de config
├── evse_client.py       # Main EVSE client / Client principal EVSE
├── sensor.py           # Sensors / Capteurs
├── switch.py           # Switches / Interrupteurs
├── number.py           # Number controls / Contrôles numériques
├── protocol/           # Protocol implementation / Implémentation protocole
│   ├── __init__.py
│   ├── communicator.py # UDP communication / Communication UDP
│   ├── datagram.py    # Datagram structure / Structure datagrammes
│   └── datagrams.py   # Message types / Types de messages
└── tests/             # Unit tests / Tests unitaires
    ├── test_basic.py
    ├── test_discovery.py
    └── test_full.py
```

### EVSE Master UDP Protocol / Protocole UDP EVSE Master

- **Default port / Port par défaut** : 28376
- **Communication** : Bidirectional UDP / UDP bidirectionnel
- **Authentication / Authentification** : Plain text password / Mot de passe texte
- **Discovery / Découverte** : Automatic broadcast / Broadcast automatique

### Development Testing / Tests de Développement

```bash
# Activate virtual environment / Activer l'environnement virtuel
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Basic tests / Tests basiques
python tests/test_basic.py

# Discovery test / Test de découverte
python tests/test_discovery.py

# Full test with real station / Test complet avec vraie borne
python tests/test_full.py
```

### Development Requirements / Prérequis pour le Développement

- Python 3.11+
- Home Assistant Core 2024.1+
- A compatible EVSE station on the local network / Une borne EVSE compatible sur le réseau local

### Protocol Coverage / Couverture du Protocole

This integration implements **75.7% of the TypeScript reference protocol** (30/37 commands):
Cette intégration implémente **75,7% du protocole de référence TypeScript** (30/37 commandes) :

#### ✅ Implemented Commands / Commandes Implémentées (30)
- Authentication: Login sequence (0x8002, 0x0002, 0x0001)
- Status monitoring: Various status commands (0x0003, 0x0004, 0x0005, 0x000d)
- Control: Charging control (0x8104, 0x0104, 0x8105, 0x0105)
- Configuration: Current, fees, system settings (0x8106-0x810d, 0x0106-0x010c)
- Data transfer: Local charge records (0x000a, 0x800a)

#### ❌ Not Implemented / Non Implémentées (7)
- Interface configuration (0x810a, 0x010a, 0x810b, 0x010b)
- Language settings (0x8109, 0x0109)
- Nickname management (0x8108, 0x0108)
- Temperature unit settings (0x810f, 0x010f)

### Contributing / Contributions

Contributions are welcome! / Les contributions sont les bienvenues !

1. Fork the project / Fork le projet
2. Create a feature branch / Créez une branche feature  
   `git checkout -b feature/amazing-feature`
3. Commit your changes / Committez vos changements  
   `git commit -m 'Add amazing feature'`
4. Push to the branch / Pushez vers la branche  
   `git push origin feature/amazing-feature`
5. Open a Pull Request / Ouvrez une Pull Request

### Release Process / Processus de Release

1. Update version in `manifest.json`
2. Create annotated tag: `git tag -a vX.Y.Z -m "Release notes"`
3. Push tag: `git push origin vX.Y.Z`
4. Create GitHub release with changelog

### Testing Guidelines / Directives de Test

- Always test with real EVSE hardware when possible
- Include protocol packet captures for new features
- Test authentication edge cases
- Verify Home Assistant compatibility with recent versions

</details>

---

## 🙏 Acknowledgments / Remerciements

This project is based on the original work of [johnwoo-nl/emproto](https://github.com/johnwoo-nl/emproto) and has been ported and extended for Home Assistant.

Ce projet est basé sur le travail original de [johnwoo-nl/emproto](https://github.com/johnwoo-nl/emproto) et a été porté et étendu pour Home Assistant.