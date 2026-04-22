# RPG Bot

Un bot Discord pour gérer des sessions de jeu de rôle sur table — gestion des personnages, combats, inventaires, artisanat, quêtes et bien plus, directement depuis Discord via des commandes slash.

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.7-5865F2)](https://discordpy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Fonctionnalités

- **Personnages** — création, affichage des stats, assignation aux joueurs
- **Combat** — système de combat au tour par tour avec carte visuelle
- **Inventaire** — gestion des objets, équipements, sets et runes
- **Artisanat** — recettes de craft avec jets de dés
- **Lootboxes** — ouverture de coffres avec récompenses aléatoires
- **Buffs & Pouvoirs** — application et gestion des effets temporaires
- **PNJs** — gestion des personnages non-joueurs et marchands
- **Quêtes** — suivi de la progression des quêtes
- **Carte** — affichage de la carte du monde
- **Dés** — jets de dés avec historique
- **Mémoires** — notes de lore et souvenirs de campagne
- **Administration** — commandes MJ pour gérer la session

---

## Prérequis

- Python **3.13** ou supérieur
- Un bot Discord avec les permissions nécessaires (voir [Configuration du bot](#configuration-du-bot))
- Des Google Sheets publics pour les données de jeu (personnages, objets, ennemis, etc.)

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/ton-nom/rpg-bot.git
cd rpg-bot
```

### 2. Créer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Édite le fichier `.env` et renseigne ton token Discord ainsi que les URLs de tes Google Sheets :

```env
DISCORD_TOKEN=ton_token_discord_ici

GSHEET_CHARACTER=https://docs.google.com/spreadsheets/d/TON_ID/export?format=csv
GSHEET_CRAFT=https://docs.google.com/spreadsheets/d/TON_ID/export?format=csv
GSHEET_ITEMS=https://docs.google.com/spreadsheets/d/TON_ID/export?format=csv
# ... etc. (voir .env.example pour la liste complète)
```

Pour obtenir l'URL d'export CSV d'un Google Sheet : **Fichier → Partager → Publier sur le web → CSV**.

### 5. Configurer les noms des salons Discord

Si ta configuration de serveur diffère des valeurs par défaut, édite `utils/path.py` pour ajuster les noms des salons (`BUFF_HISTORY_CHANNEL_NAME`, `COMBAT_CHANNEL_NAME`, etc.).

### 6. Lancer le bot

```bash
python main.py
```

---

## Configuration du bot Discord

1. Va sur le [Discord Developer Portal](https://discord.com/developers/applications)
2. Crée une nouvelle application → **Bot**
3. Active les **Privileged Intents** : `Message Content Intent`
4. Copie le token et colle-le dans ton fichier `.env`
5. Génère un lien d'invitation avec les permissions :
   - `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`
   - `Use Slash Commands`

---

## Structure du projet

```
rpg-bot/
├── main.py                # Point d'entrée du bot
├── requirements.txt       # Dépendances Python
├── .env.example           # Template des variables d'environnement
├── cogs/                  # Modules de commandes Discord (23 cogs)
│   ├── admin.py           # Commandes d'administration MJ
│   ├── characters.py      # Gestion des personnages
│   ├── combat.py          # Système de combat
│   ├── crafts.py          # Artisanat
│   ├── inventories.py     # Inventaires
│   ├── items.py           # Objets et équipements
│   └── ...
├── instance/              # Modèles de données et repositories (18 modules)
│   ├── character.py
│   ├── item.py
│   ├── combat.py
│   └── ...
├── utils/                 # Utilitaires et builders (20+ modules)
│   ├── path.py            # Configuration des chemins et noms Discord
│   ├── db.py              # Initialisation et migrations SQLite
│   └── ...
└── data/                  # Données locales (base de données, assets) — non versionné
```

---

## Dépendances

| Package | Version | Usage |
|---------|---------|-------|
| discord.py | 2.7.1 | API Discord |
| matplotlib | 3.10.8 | Génération des cartes de combat |
| numpy | 2.4.4 | Calculs numériques |
| pillow | 12.1.1 | Traitement d'images |
| python-dotenv | 1.2.2 | Variables d'environnement |
| requests | 2.33.0 | Chargement des Google Sheets |

---

## Contribuer

Les contributions sont les bienvenues ! Consulte [CONTRIBUTING.md](CONTRIBUTING.md) pour les détails.

---

## Licence

Distribué sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus d'informations.
