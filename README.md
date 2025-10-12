# EVSE Master UDP - Intégration Home Assistant# EVSE Master UDP - Intégration Home Assistant



🔌 **Intégration Home Assistant native pour les bornes de recharge compatibles EVSE Master UDP**🔌 **Intégration Home Assistant pour bornes EVSE compatibles EVSE Master**



Cette intégration permet de contrôler et surveiller votre borne de recharge EVSE via le protocole UDP utilisé par l'application mobile "EVSE Master".## À propos



## 🚨 AVERTISSEMENT IMPORTANT - PROTECTION DE L'ÉQUIPEMENTCette intégration permet de contrôler les bornes de recharge EVSE depuis Home Assistant. Elle est compatible avec :



⚠️ **USURE DE L'ÉQUIPEMENT** : Les démarrages répétés de charge peuvent user prématurément les contacteurs de votre borne de recharge. Cette intégration inclut des protections automatiques :- **Morec** (tous modèles compatibles EVSE Master)

- **EVSE génériques** utilisant le protocole UDP EmProto 

- 🛡️ **Protection contre les changements rapides** : Empêche les démarrages/arrêts trop fréquents- **Bornes chinoises** configurables via l'app EVSE Master

- 🔒 **Fallback de sécurité 16A** : En cas d'erreur, limite automatiquement à 16A

- ⏱️ **Délai minimum entre cycles** : Respecte un temps minimum entre les opérations⚠️ **AVERTISSEMENT IMPORTANT - Protection des équipements** :



**L'utilisation de cette intégration est à vos propres risques.** Les auteurs déclinent toute responsabilité en cas de dommage à votre équipement.Chaque démarrage/arrêt de charge sollicite les **relais AC** de la borne et les **contacteurs haute tension DC** du véhicule. Des cycles répétés trop rapidement peuvent **user prématurément ces composants électriques critiques**.



## 🏗️ Compatibilité**💡 Recommandations** :

- Évitez les démarrages/arrêts fréquents (< 5 minutes d'intervalle)

✅ **Bornes testées et compatibles** :- Utilisez la protection intégrée "Fast Change Protection" (configurée par défaut à 5 min)

- Morec (toutes les bornes utilisant l'app "EVSE Master")- Planifiez vos automations pour éviter les cycles rapides

- Toutes les bornes EVSE utilisant le protocole UDP sur le port 28376

## Structure du projet

## 🏠 Installation dans Home Assistant

```

### Méthode HACS (Recommandée)📁 emproto/

├── 📁 home_assistant/

1. Ouvrez HACS dans Home Assistant│   └── 📁 custom_components/

2. Allez dans "Intégrations"│       └── 📁 evsemasterudp/          # 🏠 INTÉGRATION HOME ASSISTANT

3. Cliquez sur les 3 points en haut à droite → "Dépôts personnalisés" │           ├── __init__.py

4. Ajoutez ce dépôt : `https://github.com/votre-username/evsemasterudp`│           ├── manifest.json

5. Sélectionnez la catégorie "Intégration"│           ├── config_flow.py

6. Recherchez "EVSE Master UDP" et installez│           ├── evse_client.py

7. Redémarrez Home Assistant│           ├── sensor.py

│           ├── switch.py

### Installation manuelle│           ├── number.py

│           └── 📁 protocol/           # 🐍 PROTOCOLE PYTHON

1. Téléchargez ce dépôt│               ├── __init__.py

2. Copiez le dossier vers `custom_components/evsemasterudp/` dans votre configuration HA│               ├── datagram.py

3. Redémarrez Home Assistant│               ├── datagrams.py

│               └── communicator.py

## ⚙️ Configuration├── 🧪 test_basic.py                   # Tests Python

├── 🧪 test_discovery.py

### Découverte automatique├── 🧪 test_full.py

L'intégration détecte automatiquement les bornes EVSE sur votre réseau local.├── 🧪 capture_packets.py

└── 📋 README.md

### Configuration manuelle```

Si la découverte automatique ne fonctionne pas :

## Installation rapide

1. Allez dans **Configuration** → **Intégrations**

2. Cliquez sur **Ajouter une intégration**### 1. Tester d'abord (RECOMMANDÉ)

3. Recherchez **EVSE Master UDP**

4. Saisissez :```bash

   - **Adresse IP** de votre borne# Cloner le projet

   - **Mot de passe** (configuré dans l'app EVSE Master)git clone https://github.com/johnwoo-nl/emproto.git

cd emproto

## 📊 Entités disponibles

# Créer environnement virtuel (aucune dépendance externe requise)

### Capteurspython -m venv .venv

- 🔌 **État de la borne** : `idle`, `plugged_in`, `charging`.venv\Scripts\activate  # Windows

- ⚡ **Puissance actuelle** (W)# source .venv/bin/activate  # Linux/Mac

- 🔋 **Tension** (V)

- 🌊 **Intensité** (A)# Tester la communication (modules Python standard uniquement)

- 📊 **Énergie de la session** (kWh)python test_basic.py      # ✅ Modules Python

- 🌡️ **Température**python test_discovery.py  # 🔍 Détection EVSE

- 🛡️ **Protection changements rapides** : Indique si la protection est activepython test_full.py       # 🔗 Communication complète

```

### Contrôles

- 🔄 **Interrupteur de charge** : Démarrer/Arrêter la charge### 2. Installer dans Home Assistant

- ⚡ **Réglage intensité** : 6A à 32A (avec protection 16A)

```bash

## 🔧 Fonctionnalités avancées# Copier l'intégration

cp -r home_assistant/custom_components/evsemasterudp /config/custom_components/

### Protection contre les changements rapides

- Empêche les cycles start/stop trop fréquents (< 30 secondes)# Redémarrer Home Assistant

- Protège les contacteurs de la borne contre l'usure# Ajouter l'intégration : Configuration → Intégrations → "EVSE Master UDP"

- Visible via le capteur "Protection changements rapides"```



### Fallback de sécurité## Configuration

- En cas d'erreur lors du réglage d'intensité, revient automatiquement à 16A

- Garantit un fonctionnement sûr même en cas de problème**Informations requises :**

- **Numéro de série** : Trouvé dans l'app EVSE Master

## 🧪 Tests et développement- **Mot de passe** : Configuré dans l'app EVSE Master  

- **Port UDP** : 28376 (par défaut)

Les tests sont disponibles dans le dossier `tests/` :

**Exemple :**

```bash- Série : `1368844619649410`

# Test basique des fonctionnalités- Password : `123456`

python tests/test_basic.py

## Entités créées

# Test de découverte automatique  

python tests/test_discovery.py### Capteurs

- `sensor.evse_XXXXX_etat` - État (idle/plugged_in/charging)

# Test complet de communication- `sensor.evse_XXXXX_puissance` - Puissance (W)

python tests/test_full.py- `sensor.evse_XXXXX_courant` - Courant (A)

- `sensor.evse_XXXXX_tension` - Tension (V)

# Capture de paquets pour debug- `sensor.evse_XXXXX_energie` - Énergie (kWh)

python tests/capture_packets.py- `sensor.evse_XXXXX_temperature_inner` - Température interne (°C)

```- `sensor.evse_XXXXX_temperature_outer` - Température externe (°C)



## 📋 Protocole technique### Contrôles

- `switch.evse_XXXXX_charge` - Démarrer/arrêter charge

Cette intégration implémente le protocole UDP EVSE Master :- `number.evse_XXXXX_courant_max` - Régler ampérage max (6-32A)

- **Port** : 28376- `number.evse_XXXXX_protection_changements_rapides` - Protection anti-usure (0-60 min, défaut: 5 min, empêche redémarrage rapide)

- **Format** : Datagrammes binaires avec header/checksum

- **Commandes** : Login, Status, Charge Control, Settings## Dépannage



## 🐛 Dépannage### ❌ Tests échouent



### La borne n'est pas détectée```bash

1. Vérifiez que la borne est sur le même réseau# Vérifier réseau

2. Testez avec l'app mobile EVSE Masterping 192.168.1.125  # IP de votre borne

3. Vérifiez le mot de passe

4. Consultez les logs de Home Assistant# Vérifier port UDP  

netstat -an | findstr 28376

### Erreurs de communication

- Redémarrez l'intégration# Tester la découverte

- Vérifiez la stabilité réseaupython test_discovery.py

- La borne peut mettre quelques secondes à répondre

# Tester la communication complète

### Protection des changements rapides activéepython test_full.py

- Attendez 30 secondes minimum entre les opérations```

- C'est normal, cette protection préserve votre équipement

### ❌ Import errors VS Code

## 📁 Structure du projet

```

```Ctrl+Shift+P → "Python: Configure Search Paths"

/Ajouter: home_assistant/custom_components/evsemasterudp

├── __init__.py                 # Point d'entrée de l'intégration```

├── manifest.json              # Métadonnées de l'intégration

├── config_flow.py             # Configuration UI### ❌ Home Assistant

├── sensor.py                  # Capteurs de données

├── switch.py                  # Interrupteurs```yaml

├── number.py                  # Contrôles numériques# Activer logs détaillés

├── evse_client.py             # Client simplifié avec protectionslogger:

├── protocol/                  # Implémentation du protocole UDP  logs:

│   ├── __init__.py    custom_components.evsemasterudp: debug

│   ├── datagram.py           # Classes de base```

│   ├── datagrams.py          # Commandes spécifiques

│   └── communicator.py       # Communication UDP## Documentation complète

├── tests/                     # Tests de validation

└── legacy/                    # Code TypeScript original📖 **Guide détaillé** : `home_assistant/README.md`

```

- Installation pas à pas

## 🤝 Contribution- Configuration VS Code

- Tests avancés

Les contributions sont bienvenues ! - Exemples d'automations

- Tableaux de bord

1. Forkez le projet

2. Créez une branche feature## Support

3. Testez vos modifications

4. Soumettez une Pull Request**Protocole testé avec :**

- ✅ EVSE SQW49

## 📄 Licence- ✅ Morec 7kW/11kW/22kW

- ✅ Bornes génériques EVSE Master

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

**Auteur :**

## ⚠️ Clause de non-responsabilitéJocelyn Lagarenne (& Copilot)



Cette intégration est fournie "telle quelle" sans garantie. L'utilisation est à vos propres risques. Les auteurs ne peuvent être tenus responsables de dommages à votre équipement ou de tout autre problème résultant de l'utilisation de cette intégration.**Remerciements :**

Cette intégration Home Assistant est basée sur le travail de reverse engineering du protocole EVSE réalisé par les développeurs de la bibliothèque TypeScript originale [emproto](https://github.com/johnwoo-nl/emproto). Le portage en Python natif permet une intégration directe dans Home Assistant sans dépendances Node.js.

Respectez toujours les consignes de sécurité de votre installation électrique et de votre borne de recharge.
---

🔌 **Contrôlez votre borne EVSE directement depuis Home Assistant !** ⚡
