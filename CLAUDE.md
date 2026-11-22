# CLAUDE.md

Éditeur graphique de bureau pour XML-TEI P5 (édition, pas de rendu HTML/XSLT/Pandoc). Voir `docs/ROADMAP.md` pour le projet complet et `docs/DECISIONS.md` pour les ADR.

## Règles de travail

- Python ≥ 3.11, PySide6, lxml. Aucune dépendance supplémentaire sans validation.
- **Fidélité du XML avant tout** : ne jamais re-sérialiser tout le document pour une modification locale ; agir sur des plages de texte et vérifier par un test de round-trip. **Exception explicite (ADR-0012, `docs/DECISIONS.md`) :** le mode WYSIWYG (`src/tei_editor/wysiwyg/`) resérialise l'intégralité du contenu de `<body>` et applique une politique de simplification sans échappatoire aux éléments TEI non modélisés (balise et attributs perdus, texte conservé) — risque accepté explicitement par l'utilisateur, limité à ce mode et à cette portée, jamais étendu sans nouvelle décision consignée.
- Pas d'accès réseau dans l'application ; analyse XML durcie (`xml_safety`).
- Une fonctionnalité = un module testable sans interface graphique + une fine couche Qt. Éviter les fichiers de plus de ~600 lignes.
- Chaque opération d'édition est une commande annulable en un seul pas (`QUndoStack` ou groupe d'annulation du `QTextDocument`).
- Le catalogue TEI fait foi : ne jamais coder des listes de balises ou de règles en dur dans l'interface.
- Avant tout choix d'architecture non prévu dans `docs/ROADMAP.md` ou `docs/DECISIONS.md`, proposer et attendre la validation.
- Messages d'erreur, menus et documentation en français ; identifiants de code en anglais.
- Tests : `pytest` avec `QT_QPA_PLATFORM=offscreen`.
- Ne pas commencer une phase de `docs/ROADMAP.md` sans que le critère d'acceptation de la phase précédente soit vérifié.
