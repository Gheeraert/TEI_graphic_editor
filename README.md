# TIGRE — TEI Graphic Editor

Application de bureau (PySide6, lxml) pour produire et éditer du XML-TEI P5.

Voir `docs/ROADMAP.md` pour le projet complet, `docs/DECISIONS.md` pour les choix d'architecture,
`CLAUDE.md` pour les règles de travail, `docs/MANUEL_UTILISATEUR.md` pour le manuel utilisateur
(menus, palette, inspecteur, assistant d'en-tête, jeux de balises, validation...),
`docs/INSTALLATION.md` pour installer l'application, `docs/NON_REGRESSION.md` pour le corpus de
test et comment y ajouter un document, et `CHANGELOG.md` pour l'historique des versions.

## Installation et utilisation

Voir `docs/INSTALLATION.md` pour les instructions complètes (`pipx install .` ou `pip install .`,
prérequis). En résumé :

```
pipx install .
tei-editor
```

## Développement

```
pip install -e ".[dev]"
QT_QPA_PLATFORM=offscreen pytest
python -m tei_editor.app
```
