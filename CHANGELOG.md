# Journal des changements

Format librement inspiré de [Keep a Changelog](https://keepachangelog.com/fr/), le projet suit
[SemVer](https://semver.org/lang/fr/) à partir de `1.0.0` (voir `docs/DECISIONS.md`, ADR-0011 pour la
justification du passage direct de `0.1.0` à `1.0.0`). Chaque entrée reprend le commit réel
correspondant (`git log`) et les décisions d'architecture du moment (`docs/DECISIONS.md`).

## [1.0.0] — 2026-11-21

Première version couvrant l'intégralité des 9 phases du plan initial (`docs/ROADMAP.md`).

### Ajouté (phase 9 — Qualité et distribution)

- Couverture de test ciblée sur les modules d'opérations d'édition portée de 85 % à 99 % (`editor.structured_edits`, `editor.snippets`, `editor.current_element`, `editor.diagnostics`, `tei.header_reader`, `tei.header_writer`) : 51 nouveaux tests sur les branches d'erreur et cas limites non couverts.
- `docs/NON_REGRESSION.md` : documentation du corpus de non-régression (`tests/fixtures/tei-samples/`), recette d'ajout d'un document réel, et correction d'un risque réel d'échec silencieux (fichier XML ajouté au corpus sans entrée de manifeste, désormais détecté par `tests/test_tei_samples_corpus.py`).
- `docs/MANUEL_UTILISATEUR.md` : manuel utilisateur complet (premiers pas, menus, palette/inspecteur, panneau Problèmes, profils et jeux de balises, assistant d'en-tête, préférences/thèmes), vérifié contre le comportement réel du code.
- `docs/INSTALLATION.md` : instructions d'installation (`pipx install .`/`pip install .`), vérifiées par une installation réelle dans un venv propre ; limitation documentée sur l'exécutable autonome (pas de compilation croisée possible depuis cette machine).
- Correction d'une lacune réelle de `pyproject.toml` (`[tool.setuptools.package-data]` manquant : `src/tei_editor/data/` n'était pas embarqué par `pip install .`, l'application plantait au lancement) et test de non-régression associé (`tests/test_packaging.py`).
- `pytest-cov` ajouté aux dépendances de développement.
- Passage en version `1.0.0` (`docs/DECISIONS.md`, ADR-0011).

### Phase 8 — Finition de l'interface (commit `68671fe`)

Jeu d'icônes SVG Lucide (libre de droits, monochrome, recoloré dynamiquement selon le thème),
feuilles de style claire/sombre neuves (contraste WCAG vérifié), quatre barres d'outils regroupées
logiquement avec `objectName` explicite (persistance de disposition), infobulles avec raccourcis,
focus clavier sur les boutons de barre d'outils. Voir ADR-0010.

### Phase 7 — Jeux de balises (commit `a869184`)

Commandes composites : grouper en choix (`orig`/`reg`, `sic`/`corr`, `abbr`/`expan`), insérer une
liste de personnages, marquer un vers partagé (convention `@part`/`@n`), insérer une leçon
(`app`/`lem`/`rdg`). Vérifié de bout en bout par la construction d'un acte de théâtre et d'une page
d'édition critique avec les seuls outils graphiques. Voir ADR-0009.

### Phase 6 — Assistant d'en-tête TEI (commit `cfe1ce3`)

Dialogue à 7 onglets (titre/responsabilités, édition, publication, source, encodage, profil,
révisions), lecture tolérante et réécriture chirurgicale (seuls les sous-éléments modifiés sont
réécrits, le reste du document reste identique au caractère près), 4 modèles de nouveau document
(minimal, édition critique, théâtre, correspondance).

### Phase 5 — Édition guidée (commit `0e39c62`)

Palette contextuelle, enveloppement de sélection, insertion avec fermeture automatique, dégrouper,
renommer, scinder/fusionner un paragraphe, inspecteur d'attributs typé, génération de `xml:id`.
Chaque opération se défait en un seul « Annuler » (bloc d'annulation natif `QTextDocument`). Voir
ADR-0008.

### Correction de fixtures (commit `a4f565f`)

Deux fixtures invalides du corpus de test corrigées après la mise en place de la validation RelaxNG
de la phase 4.

### Phase 4 — Bonne formation, validation, plan (commit `4a49c82`)

Parsing lxml différé avec positions, soulignement des erreurs, panneau « Problèmes », validation
RelaxNG contre le schéma unique `tei_all` (messages reformulés en français), plan structurel
synchronisé avec le curseur, fil d'Ariane XPath calculé par l'arbre réel. Voir ADR-0007.

### Phase 3 — Squelette applicatif (commit `2df9b53`)

`QMainWindow`, menus complets, éditeur de texte XML avec coloration syntaxique, barre d'état,
préférences (`QSettings`), autosave/récupération, écriture atomique, round-trip octet à octet
vérifié sur le corpus de fixtures. Voir ADR-0006.

### Résolution des décisions de cadrage (commit `dd62e4f`)

Nom du projet (TIGRE), plateformes visées (Windows, macOS, Linux), profils de validation
prioritaires, corpus de test réel fourni par l'utilisateur (21 documents). Voir ADR-0005.

### Phase 2 — Audit et extraction du code de Mérope (commit `8e72c04`)

Extraction des modules réutilisables de Mérope (`xml_safety`, `commons_publishing`, `licenses`,
`wrapping_toolbar`, `atomic_write`, `versioning`, `typography`), sans dépendance au paquet
`bloggen`, avec provenance conservée. Voir `docs/AUDIT_MEROPE.md` et ADR-0004.

### Phase 1 — Catalogue TEI P5 (commit `55bb275`)

Catalogue généré depuis les sources officielles TEI P5 4.12.0 (`tools/build_catalog.py`), profils
JSON (`tei_all`, `edition_textes`, `theatre`, `edition_critique`), `docs/REGLES_ENCODAGE.md`. Voir
ADR-0003.

### Phase 0 — Cadrage (commit `9b14d6a`, `6a108b8`)

Dépôt initial, `CLAUDE.md`, licence, `pyproject.toml`, CI, décision d'architecture fondatrice (texte
XML assisté, pas de pivot objet, pas de WYSIWYG). Voir ADR-0001/ADR-0002.
