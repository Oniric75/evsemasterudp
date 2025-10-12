# EVSE Master UDP - Home Assistant Integration# EVSE Master UDP - Home Assistant Integration



> **🙏 ACKNOWLEDGMENT / REMERCIEMENTS**  > **🙏 ACKNOWLEDGMENT / REMERCIEMENTS**  

> This project is based on the excellent work of [johnwoo-nl/emproto](https://github.com/johnwoo-nl/emproto). Without their invaluable reverse-engineering of the EVSE Master UDP protocol, this Home Assistant integration would not have been possible. Full credit and thanks to the original author! 🌟  > This project is based on the excellent work of [johnwoo-nl/emproto](https://github.com/johnwoo-nl/emproto). Without their invaluable reverse-engineering of the EVSE Master UDP protocol, this Home Assistant integration would not have been possible. Full credit and thanks to the original author! 🌟  

> > 

> Ce projet est basé sur l'excellent travail de [johnwoo-nl/emproto](https://github.com/johnwoo-nl/emproto). Sans leur précieux reverse-engineering du protocole UDP EVSE Master, cette intégration Home Assistant n'aurait pas été possible. Tout le crédit et nos remerciements à l'auteur original ! 🌟> Ce projet est basé sur l'excellent travail de [johnwoo-nl/emproto](https://github.com/johnwoo-nl/emproto). Sans leur précieux reverse-engineering du protocole UDP EVSE Master, cette intégration Home Assistant n'aurait pas été possible. Tout le crédit et nos remerciements à l'auteur original ! 🌟



------



🔌 **Home Assistant Integration for EVSE Master UDP compatible charging stations**🔌 **Home Assistant Integration for EVSE Master UDP compatible charging stations**



Cette intégration permet de contrôler et surveiller votre borne de recharge EVSE depuis Home Assistant via le protocole UDP utilisé par l'application mobile "EVSE Master".Cette intégration permet de contrôler et surveiller votre borne de recharge EVSE depuis Home Assistant via le protocole UDP utilisé par l'application mobile "EVSE Master".



## 🚀 Installation Rapide## 🚀 Installation Rapide



1. **Copier les fichiers** :1. **Copier les fichiers** :

   ```bash   ```bash

   cp -r custom_components/evsemasterudp /config/custom_components/   cp -r custom_components/evsemasterudp /config/custom_components/

   ```   ```



2. **Redémarrer Home Assistant**2. **Redémarrer Home Assistant**



3. **Ajouter l'intégration** :3. **Ajouter l'intégration** :

   - Configuration → Intégrations → Ajouter   - Configuration → Intégrations → Ajouter

   - Rechercher : "EVSE Master UDP"   - Rechercher : "EVSE Master UDP"



4. **Configurer** :4. **Configurer** :

   - Numéro de série : trouvé sur votre borne   - Numéro de série : trouvé sur votre borne

   - Mot de passe : défini dans l'app EVSE Master   - Mot de passe : défini dans l'app EVSE Master

   - Port : 28376 (défaut)   - Port : 28376 (défaut)



## 🏗️ Compatibilité## 🏗️ Compatibilité



**Bornes testées et compatibles** :**Bornes testées et compatibles** :

- **Morec** (toutes les bornes utilisant l'app "EVSE Master")- **Morec** (toutes les bornes utilisant l'app "EVSE Master")

- **Bornes EVSE génériques** utilisant le protocole UDP sur le port 28376- **Bornes EVSE génériques** utilisant le protocole UDP sur le port 28376

- **Bornes chinoises** configurables via l'app EVSE Master- **Bornes chinoises** configurables via l'app EVSE Master



## 📊 Entités Créées## 🚀 Installation



### Capteurs (Sensors)### Method 1: HACS (Recommended)

- `sensor.evse_status` - Statut général de la borne

- `sensor.evse_power` - Puissance actuelle (W)1. Open HACS in Home Assistant

- `sensor.evse_current` - Courant (A)2. Go to "Integrations"

- `sensor.evse_voltage` - Tension (V)3. Click the 3 dots in the top right → "Custom repositories"

- `sensor.evse_temperature` - Température de la borne (°C)4. Add `https://github.com/Oniric75/evsemasterudp` as a repository of type "Integration"

- `sensor.evse_session_energy` - Énergie de la session (kWh)5. Search for "EVSE Master UDP" in HACS

- `sensor.evse_total_energy` - Énergie totale (kWh)6. Install the integration

7. Restart Home Assistant

### Commutateurs (Switches)

- `switch.evse_charging` - Contrôle marche/arrêt de la charge### Method 2: Manual Installation

- `switch.evse_offline_charge` - Mode charge hors ligne

1. Download the [latest release](https://github.com/Oniric75/evsemasterudp/releases)

### Contrôles Numériques (Number)2. Extract the `evsemasterudp` folder to `custom_components/`

- `number.evse_max_current` - Courant maximum (A)3. Restart Home Assistant

- `number.evse_charge_fee` - Tarif de charge

- `number.evse_service_fee` - Frais de service## ⚙️ Configuration



## 🛠️ Fonctionnalités1. Go to **Configuration** → **Integrations**

2. Click **"Add Integration"**

- 🔍 **Découverte automatique** des bornes EVSE sur le réseau local3. Search for **"EVSE Master UDP"**

- 🔐 **Authentification sécurisée** avec mot de passe4. Follow the configuration wizard:

- 📊 **Surveillance en temps réel** du statut de charge   - Automatic discovery will detect your charging station

- ⚡ **Contrôle de la charge** (démarrage/arrêt)   - Enter your EVSE station password

- 🔢 **Configuration des paramètres** (courant max, température, etc.)   - Configure update frequency (recommended: 30 seconds)

- 📈 **Historique des sessions de charge**

- 🛡️ **Protections intégrées** contre l'usure prématurée## 📊 Created Entities



## ⚠️ Avertissements Importants### Sensors

- `sensor.evse_status` - General station status

> **PROTECTION DE L'ÉQUIPEMENT** : Les démarrages répétés de charge peuvent user prématurément les contacteurs de votre borne. Cette intégration inclut des protections automatiques, mais **l'utilisation se fait à vos risques et périls**.- `sensor.evse_power` - Current power (W)

- `sensor.evse_current` - Current amperage (A)

**Protections intégrées** :- `sensor.evse_voltage` - Voltage (V)

- 🛡️ **Protection contre les changements rapides** : Empêche les démarrages/arrêts trop fréquents (délai minimum de 5 min)- `sensor.evse_temperature` - Station temperature (°C)

- 🔒 **Sécurité de repli à 16A** : En cas d'erreur, limite automatiquement à 16A- `sensor.evse_session_energy` - Current session energy (kWh)

- ⏱️ **Délai minimum entre les cycles** : Respecte un temps minimum entre les opérations- `sensor.evse_total_energy` - Total energy (kWh)



**Recommandations** :### Switches

- Évitez les démarrages/arrêts fréquents (< 5 minutes d'intervalle)- `switch.evse_charging` - Charging on/off control

- Planifiez vos automatisations pour éviter les cycles rapides- `switch.evse_offline_charge` - Offline charging mode

- Surveillez l'état de santé de votre équipement

### Number Controls

## 🔧 Configuration Avancée- `number.evse_max_current` - Maximum current (A)

- `number.evse_charge_fee` - Charging rate

### Paramètres disponibles dans l'interface :- `number.evse_service_fee` - Service fee

- **Fréquence de mise à jour** : 15-300 secondes (défaut : 30s)

- **Mode de connexion** : Automatique ou manuel## 🛠️ Features

- **Gestion des erreurs** : Automatique ou manuelle

- 🔍 **Automatic discovery** of EVSE stations on local network

## 🐛 Résolution de Problèmes- 🔐 **Secure authentication** with password

- 📊 **Real-time monitoring** of charging status

### Borne non détectée- ⚡ **Charging control** (start/stop)

1. Vérifiez que la borne est allumée- 🔢 **Parameter configuration** (max current, temperature, etc.)

2. Confirmez que Home Assistant et la borne sont sur le même réseau- 📈 **Charging session history**

3. Vérifiez que le port 28376 n'est pas bloqué par le pare-feu- 🛡️ **Built-in protections** against premature wear



### Authentification échouée## 🔧 Advanced Configuration

1. Vérifiez le mot de passe dans l'app EVSE Master

2. Confirmez le numéro de série de la borne### Available settings in the interface:

3. Redémarrez la borne si nécessaire- **Update frequency**: 15-300 seconds (default: 30s)

- **Connection timeout**: 5-30 seconds (default: 10s)

### Données non mises à jour- **Rapid change protection**: enabled by default

1. Vérifiez la connexion réseau- **Minimum delay between cycles**: 5 minutes (configurable)

2. Ajustez la fréquence de mise à jour

3. Consultez les logs de Home Assistant## 📚 Automation Examples



## 📝 Licence### Charging start based on electricity rates



Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.```yaml

automation:

## 🤝 Contribution  - alias: "EVSE charge during off-peak hours"

    trigger:

Les contributions sont les bienvenues ! N'hésitez pas à :      - platform: time

1. Fork le projet        at: "22:30:00"  # Off-peak hours start

2. Créer une branche pour votre fonctionnalité    condition:

3. Commiter vos changements      - condition: state

4. Ouvrir une Pull Request        entity_id: binary_sensor.vehicle_connected

        state: "on"

## 📞 Support    action:

      - service: switch.turn_on

- **Issues** : [GitHub Issues](https://github.com/Oniric75/evsemasterudp/issues)        entity_id: switch.evse_charging

- **Discussions** : [GitHub Discussions](https://github.com/Oniric75/evsemasterudp/discussions)```

- **Documentation** : Ce README et les commentaires dans le code

### Automatic stop at 80% battery

---

```yaml

## 🛠️ Développementautomation:

  - alias: "Stop charge at 80%"

### Structure du Projet    trigger:

```      - platform: numeric_state

custom_components/evsemasterudp/        entity_id: sensor.vehicle_battery_level

├── __init__.py              # Point d'entrée de l'intégration        above: 80

├── manifest.json            # Métadonnées de l'intégration    action:

├── config_flow.py           # Interface de configuration      - service: switch.turn_off

├── evse_client.py           # Client principal EVSE        entity_id: switch.evse_charging

├── sensor.py                # Capteurs Home Assistant```

├── switch.py                # Commutateurs Home Assistant

├── number.py                # Contrôles numériques Home Assistant## 🆘 Support and Issues

└── protocol/                # Implémentation du protocole UDP

    ├── __init__.py- 📋 [Report a bug](https://github.com/Oniric75/evsemasterudp/issues)

    ├── communicator.py      # Communicateur UDP- 💬 [Discussions](https://github.com/Oniric75/evsemasterudp/discussions)

    ├── datagram.py          # Classes de base des datagrammes- 📖 [Wiki and documentation](https://github.com/Oniric75/evsemasterudp/wiki)

    └── datagrams.py         # Implémentation des datagrammes EVSE

```## 📄 License



### TestsThis project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

```bash

# Tests de base---

python tests/test_basic.py

## 👨‍💻 Development

# Test de découverte

python tests/test_discovery.py<details>

<summary>Developer Information</summary>

# Test complet

python tests/test_full.py### Project Structure

```

```

---evsemasterudp/

├── __init__.py          # Integration entry point

*Made with ❤️ for the Home Assistant community*├── manifest.json        # Integration metadata
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


