# EVSE Master UDP - Intégration Home Assistant

🔌 **Intégration Home Assistant pour bornes EVSE compatibles EVSE Master**

## À propos

Cette intégration permet de contrôler les bornes de recharge EVSE depuis Home Assistant. Elle est compatible avec :

- **Morec** (tous modèles compatibles EVSE Master)
- **EVSE génériques** utilisant le protocole UDP EmProto 
- **Bornes chinoises** configurables via l'app EVSE Master

⚠️ **AVERTISSEMENT IMPORTANT - Protection des équipements** :

Chaque démarrage/arrêt de charge sollicite les **relais AC** de la borne et les **contacteurs haute tension DC** du véhicule. Des cycles répétés trop rapidement peuvent **user prématurément ces composants électriques critiques**.

**💡 Recommandations** :
- Évitez les démarrages/arrêts fréquents (< 5 minutes d'intervalle)
- Utilisez la protection intégrée "Fast Change Protection" (configurée par défaut à 5 min)
- Planifiez vos automations pour éviter les cycles rapides

## Structure du projet

```
📁 emproto/
├── 📁 home_assistant/
│   └── 📁 custom_components/
│       └── 📁 evsemasterudp/          # 🏠 INTÉGRATION HOME ASSISTANT
│           ├── __init__.py
│           ├── manifest.json
│           ├── config_flow.py
│           ├── evse_client.py
│           ├── sensor.py
│           ├── switch.py
│           ├── number.py
│           └── 📁 protocol/           # 🐍 PROTOCOLE PYTHON
│               ├── __init__.py
│               ├── datagram.py
│               ├── datagrams.py
│               └── communicator.py
├── 🧪 test_basic.py                   # Tests Python
├── 🧪 test_discovery.py
├── 🧪 test_full.py
├── 🧪 capture_packets.py
└── 📋 README.md
```

## Installation rapide

### 1. Tester d'abord (RECOMMANDÉ)

```bash
# Cloner le projet
git clone https://github.com/johnwoo-nl/emproto.git
cd emproto

# Créer environnement virtuel (aucune dépendance externe requise)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Tester la communication (modules Python standard uniquement)
python test_basic.py      # ✅ Modules Python
python test_discovery.py  # 🔍 Détection EVSE
python test_full.py       # 🔗 Communication complète
```

### 2. Installer dans Home Assistant

```bash
# Copier l'intégration
cp -r home_assistant/custom_components/evsemasterudp /config/custom_components/

# Redémarrer Home Assistant
# Ajouter l'intégration : Configuration → Intégrations → "EVSE Master UDP"
```

## Configuration

**Informations requises :**
- **Numéro de série** : Trouvé dans l'app EVSE Master
- **Mot de passe** : Configuré dans l'app EVSE Master  
- **Port UDP** : 28376 (par défaut)

**Exemple :**
- Série : `1368844619649410`
- Password : `123456`

## Entités créées

### Capteurs
- `sensor.evse_XXXXX_etat` - État (idle/plugged_in/charging)
- `sensor.evse_XXXXX_puissance` - Puissance (W)
- `sensor.evse_XXXXX_courant` - Courant (A)
- `sensor.evse_XXXXX_tension` - Tension (V)
- `sensor.evse_XXXXX_energie` - Énergie (kWh)
- `sensor.evse_XXXXX_temperature_inner` - Température interne (°C)
- `sensor.evse_XXXXX_temperature_outer` - Température externe (°C)

### Contrôles
- `switch.evse_XXXXX_charge` - Démarrer/arrêter charge
- `number.evse_XXXXX_courant_max` - Régler ampérage max (6-32A)
- `number.evse_XXXXX_protection_changements_rapides` - Protection anti-usure (0-60 min, défaut: 5 min, empêche redémarrage rapide)

## Dépannage

### ❌ Tests échouent

```bash
# Vérifier réseau
ping 192.168.1.125  # IP de votre borne

# Vérifier port UDP  
netstat -an | findstr 28376

# Tester la découverte
python test_discovery.py

# Tester la communication complète
python test_full.py
```

### ❌ Import errors VS Code

```
Ctrl+Shift+P → "Python: Configure Search Paths"
Ajouter: home_assistant/custom_components/evsemasterudp
```

### ❌ Home Assistant

```yaml
# Activer logs détaillés
logger:
  logs:
    custom_components.evsemasterudp: debug
```

## Documentation complète

📖 **Guide détaillé** : `home_assistant/README.md`

- Installation pas à pas
- Configuration VS Code
- Tests avancés
- Exemples d'automations
- Tableaux de bord

## Support

**Protocole testé avec :**
- ✅ EVSE SQW49
- ✅ Morec 7kW/11kW/22kW
- ✅ Bornes génériques EVSE Master

**Auteur :**
Jocelyn Lagarenne (& Copilot)

**Remerciements :**
Cette intégration Home Assistant est basée sur le travail de reverse engineering du protocole EVSE réalisé par les développeurs de la bibliothèque TypeScript originale [emproto](https://github.com/johnwoo-nl/emproto). Le portage en Python natif permet une intégration directe dans Home Assistant sans dépendances Node.js.

---

🔌 **Contrôlez votre borne EVSE directement depuis Home Assistant !** ⚡
