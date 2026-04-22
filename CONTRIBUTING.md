# Contribuer à RPG Bot

Merci de l'intérêt que tu portes à ce projet ! Voici comment contribuer.

## Signaler un bug

Utilise le [template de bug report](.github/ISSUE_TEMPLATE/bug_report.md) en ouvrant une nouvelle issue.

Inclus :
- La commande slash utilisée
- Le comportement attendu vs. observé
- Les logs d'erreur si disponibles (`python main.py` affiche les logs dans la console)

## Proposer une fonctionnalité

Ouvre une issue en utilisant le [template de feature request](.github/ISSUE_TEMPLATE/feature_request.md).

## Soumettre une pull request

1. **Fork** le dépôt
2. Crée une branche depuis `main` :
   ```bash
   git checkout -b feature/ma-fonctionnalite
   ```
3. Fais tes modifications
4. Vérifie que le bot démarre sans erreur :
   ```bash
   python main.py
   ```
5. Ouvre une **Pull Request** vers `main` en décrivant tes changements

## Conventions de code

- **Langue** : le code, les commentaires et les messages Discord sont en **français**
- **Style** : PEP 8, indentation 4 espaces
- **Commandes Discord** : utilise les commandes slash (`app_commands`) — pas de préfixe `!`
- **Logging** : utilise `logger` (module `logging`) plutôt que `print()`
- **Nouveaux cogs** : crée un fichier dans `cogs/`, hérite de `commands.Cog`, ajoute le nom dans `COGS` dans `utils/path.py`
- **Nouveaux modèles** : place les classes dans `instance/`, les builders d'embeds dans `utils/embeds/`

## Structure des branches

- `main` — branche stable, seules les PR validées y sont mergées

## Licence

En contribuant, tu acceptes que ton code soit distribué sous licence [MIT](LICENSE).
