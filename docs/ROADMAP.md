# Éditeur graphique de TEI (standalone) — brief et feuille de route pour Claude Code

> Ce document est destiné à être placé à la racine du nouveau dépôt (`docs/ROADMAP.md`), avec un `CLAUDE.md` court qui reprend la section « Règles de travail ».
> Provenance : audit de surface du dépôt `Gheeraert/merope` (lecture des fichiers, des imports, des docs ; **aucun code exécuté**). Les affirmations de couplage sont à revérifier à l'extraction (phase 2).

## 1. Objectif

Application de bureau autonome (Python 3.11+, PySide6, lxml) qui **produit, édite et affiche pour un humain (conformément aux conventions de l'imprimerie et de la typographie) du XML-TEI P5**, mais sans le rendre disponible dans une autre interface (pas d'aperçu HTML, pas de XSLT, pas de Pandoc, pas de site statique).
Trois axes : (1) récupérer le code utile de Mérope, (2) une interface soignée avec vrais menus, (3) des fonctions TEI : assistant de `teiHeader` valide et jeux de balises (édition de textes en premier).

Philosophie : sobriété technologique, solutions légères et durables. Peu de dépendances (PySide6, lxml, éventuellement pyspellchecker).

## 2. Décision d'architecture (à valider avant la phase 3)

**Constat sur Mérope.** L'éditeur Qt de Mérope est un éditeur WYSIWYG de **Markdown** : son pivot est `Block` / `InlineRun` (paragraphes, titres H1–H4, listes simples, citations, tableaux, encadrés), avec `QTextDocument ↔ Block/InlineRun ↔ Markdown`. Ce modèle plat refuse tout objet qu'il ne sait pas retranscrire. TEI est un arbre XML à contenu mixte, attributs et imbrication libre : le modèle ne se transpose pas. Les trois gros fichiers (`document_adapter.py` 2768 l., `text_edit.py` 2735 l., `window.py` 2659 l.) sont indissociables de ce pivot.

**Recommandation : ne pas porter l'éditeur, en reprendre la périphérie.**

- **Source de vérité = le texte XML** (`QPlainTextEdit` + coloration syntaxique), assisté par une interface graphique : palette de balises, inspecteur d'attributs, plan structurel (arbre), panneau de problèmes, dialogues. C'est le mode « texte assisté » des éditeurs XML professionnels.
- **Pourquoi** : fidélité de round-trip garantie (commentaires, instructions de traitement, espaces significatifs du contenu mixte, préfixes de namespace, ordre des attributs), pas d'objet « étranger » refusé, et coût de développement bien moindre. L'utilisateur ne veut pas de rendu, donc le WYSIWYG n'apporte presque rien ici.
- **Variante ultérieure possible** (hors v1) : afficher les balises comme « pastilles » dans le texte (balisage inline stylé), toujours adossé au texte XML.
- Le modèle structurel (arbre lxml) est **dérivé** du texte, re-parsé en différé (debounce) ; jamais l'inverse. Aucune sérialisation « pretty-print » qui toucherait au contenu mixte.

## 3. Livrable A — Catalogue des balises et règles d'encodage

Ne pas écrire la liste à la main : la **générer** depuis les sources officielles TEI P5 (version épinglée, mentionnée dans le catalogue).

### A1. Génération du catalogue

- Script reproductible `tools/build_catalog.py` : lit `p5subset.xml` (et/ou `tei_all.rng`) et produit `src/<pkg>/data/tei_catalog.json` : pour chaque élément → module, classes d'appartenance, attributs (nom, type de donnée, valeurs fermées éventuelles, obligatoire ou non), enfants possibles, parents possibles, glose et description (fr si disponible, sinon en), exemples.
- Profils (listes blanches) en JSON, dans `src/<pkg>/data/profiles/` : `tei_all` (générique, tout le catalogue), `edition_textes`, `theatre`, `edition_critique`, `commons_publishing` (voir 3.C). Un profil = éléments proposés dans la palette + regroupements + schéma de validation associé.
- Tests : le catalogue contient X éléments (compte épinglé), `div` accepte `head` et `p`, `sp` accepte `speaker`, etc.

### A2. Ensemble de départ (à confronter au catalogue généré, qui fait foi)

- **En-tête** : `teiHeader`, `fileDesc` (`titleStmt` [`title`, `author`, `editor`, `respStmt` [`resp`, `name`], `funder`], `editionStmt`, `extent`, `publicationStmt` [`publisher`, `pubPlace`, `date`, `idno`, `availability`/`licence`, `authority`], `seriesStmt`, `notesStmt`, `sourceDesc` [`bibl`, `biblStruct`, `msDesc`, `listWit`]), `encodingDesc` (`projectDesc`, `editorialDecl`, `tagsDecl`, `refsDecl`, `classDecl`, `charDecl`, `appInfo`), `profileDesc` (`langUsage`, `creation`, `textClass`/`keywords`, `abstract`, `particDesc`, `correspDesc`), `revisionDesc` (`change`, `listChange`).
- **Structure du texte** : `TEI`, `teiCorpus`, `text`, `front`, `body`, `back`, `group`, `floatingText`, `div` (+ `@type`, `@n`), `head`, `byline`, `dateline`, `salute`, `signed`, `opener`, `closer`, `epigraph`, `argument`, `titlePage` (`docTitle`, `titlePart`, `docAuthor`, `docImprint`, `docDate`), `p`, `ab`, `lg`, `l`, `seg`, `lb`, `pb`, `cb`, `milestone`, `anchor`.
- **Niveau phrastique** : `hi`, `emph`, `foreign`, `mentioned`, `soCalled`, `q`, `quote`, `cit`, `said`, `title`, `term`, `gloss`, `distinct`, `date`, `time`, `num`, `measure`, `name`, `persName`, `placeName`, `orgName`, `geogName`, `rs`, `ref`, `ptr`, `note`, `bibl`, `idno`.
- **Édition de textes / transcription** : `abbr`, `expan`, `am`, `ex`, `choice`, `sic`, `corr`, `orig`, `reg`, `unclear`, `gap`, `supplied`, `add`, `del`, `subst`, `damage`, `restore`, `space`, `handShift`.
- **Apparat critique** : `app`, `lem`, `rdg`, `rdgGrp`, `wit`, `witDetail`, `listWit`, `witness`, `listApp`.
- **Théâtre** : `sp`, `speaker`, `stage`, `castList`, `castItem`, `role`, `roleDesc`, `set`, `performance`, `l`/`lg` (avec `@part` pour les vers partagés).
- **Listes, tableaux, images** : `list`, `item`, `label`, `table`, `row`, `cell`, `figure`, `figDesc`, `graphic`, `facsimile`, `surface`, `zone`.
- **Indices et entités** : `listPerson`/`person`, `listPlace`/`place`, `listOrg`/`org`, `listBibl`, `link`, `linkGrp`, `join`.

### A3. Règles d'encodage à documenter (`docs/REGLES_ENCODAGE.md`) et, quand c'est possible, à vérifier automatiquement

1. **Bonne formation** (XML 1.0, un seul élément racine, UTF-8 par défaut, déclaration d'encodage cohérente) et **namespace** `http://www.tei-c.org/ns/1.0` sur la racine `TEI`.
2. **Squelette minimal** : `TEI` → `teiHeader` + (`text` | `facsimile`…) ; `fileDesc` avec `titleStmt` (au moins un `title`), `publicationStmt`, `sourceDesc` ; `text` contient `body` (ou `group`), `front`/`back` optionnels et ordonnés.
3. **Modèles de contenu** : validés par le schéma (RelaxNG) du profil actif, non recodés à la main. Exemples à tester : `head` en tête de `div` ; `l` dans `lg` ou `sp` ; `sp` avec `speaker` ; `lem`/`rdg` dans `app`.
4. **Attributs globaux** : `@xml:id` (NCName, **unique dans le document**), `@xml:lang` (BCP 47), `@n`, `@rend`, `@style`, `@type`/`@subtype`, `@resp`, `@cert`, `@source`, `@corresp`, `@sameAs`, `@next`/`@prev`, `@facs`.
5. **Références internes** : toute valeur `#id` (`@target`, `@ref`, `@corresp`, `@resp`, `@who`, `@wit`, `@facs`…) doit pointer vers un `@xml:id` existant. Contrôle croisé, avec complétion dans l'inspecteur.
6. **Types de données** : dates ISO 8601 / W3C (`@when`, `@notBefore`, `@notAfter`, `@from`, `@to`), URI, entiers, énumérations fermées quand le schéma en définit.
7. **Conventions d'encodage** (avertissements, pas des erreurs) : encoder la sémantique plutôt que l'apparence (`emph`, `title`, `foreign` plutôt que `hi` quand c'est possible) ; `@rend` pour la forme ; `lb`/`pb` en éléments vides avec `@break="no"` pour les coupes de mots ; `choice` pour grouper `orig`/`reg`, `sic`/`corr`, `abbr`/`expan` ; déclarer les choix éditoriaux dans `editorialDecl`.
8. **Contenu mixte** : ne jamais insérer/retirer d'espaces ou de retours à la ligne dans le texte lors d'une opération de balisage ; l'indentation automatique est **désactivée** dans les éléments à contenu mixte.
9. **Caractères** : Unicode NFC conseillé ; espaces insécables (U+00A0, U+202F) préservés ; `charDecl`/`g` si caractères hors Unicode.

## 4. Livrable B — Audit et récupération du code de Mérope

Rendre la décision dans `docs/AUDIT_MEROPE.md` (tableau fichier → décision → raison → couplage restant), puis extraire dans un nouveau dépôt, **sans dépendre du paquet `bloggen`** (pas de Pandoc, pas de Pillow) et en conservant la provenance (commit source dans l'en-tête de chaque fichier repris).

### Pré-audit (à confirmer)

| Module Mérope | Taille | Décision | Remarque |
|---|---|---|---|
| `tei/xml_safety.py` | 102 l. | **Reprendre** | Parsing durci (pas de réseau, pas de DTD). À assouplir si besoin de DOCTYPE/entités internes (réglage explicite, refus par défaut). |
| `tei/commons_publishing.py` + `resources/schemas/commons-publishing/*` (RNG, LICENSE, PROVENANCE) | 196 l. + RNG | **Reprendre** comme un profil de validation parmi d'autres | Bon modèle de validation RelaxNG avec accès réseau interdit. |
| `tei/licenses.py` | 40 l. | **Reprendre** | Liste de licences pour l'assistant d'en-tête. |
| `tei/header_builder.py` | 229 l. | **S'en inspirer, ne pas reprendre** | Modèle minimal pensé pour un billet (un auteur, une licence). Le nouveau modèle doit gérer auteurs et responsabilités multiples. Son docstring indique qu'il s'inspire déjà du sérialiseur de `teiHeader` de Mini-Métopes : vérifier s'il existe un sérialiseur plus riche à réutiliser dans les autres projets. |
| `ui/qt_editor/wrapping_toolbar.py` | 186 l. | **Reprendre** | Pur Qt, aucun import `bloggen`. Barre d'outils qui passe à la ligne. |
| `ui/qt_editor/toolbar_icons.py`, `ui/toolbar_icons.py` | 223 / 153 l. | **Remplacer** | Icônes dessinées à la main : source probable de la laideur actuelle. Adopter un jeu d'icônes SVG libre (voir phase 8). |
| `content/atomic_write.py`, `content/versioning.py` | à mesurer | **Reprendre si découplé** | Écriture atomique et archivage de la version précédente. |
| `ui/qt_editor/recovery.py`, `ui/editor_recovery.py` | 125 / 86 l. | **Réécrire sur le même principe** | Autosave + restauration après plantage, mais couplés à `Block` et aux notes. |
| `ui/qt_editor/find_replace*.py` | 238 / 122 l. | **Réécrire** | Couplés à `document_adapter`. `QPlainTextEdit` + regex suffisent. |
| `ui/qt_editor/spellcheck.py` | 327 l. | **Adapter (optionnel)** | Dépend des types de blocs ; à limiter aux nœuds texte. |
| `markdown/typography.py` | pur Python | **Option** | Typographie française à la frappe (espaces insécables, guillemets), à n'appliquer que dans les nœuds texte. |
| `ui/qt_editor/{document_adapter,text_edit,window}.py`, `markdown/rich_text_*`, `content/footnotes.py`, `box_*`, `table_*`, `image_*`, `video_*`, `clipboard_*`, `content_browser`, `ipc`, `preview*`, `qt_editor_launcher` | ~15 000 l. | **Ne pas reprendre** | Couplés au pivot Markdown, au projet Mérope et au protocole Tk↔Qt. À consulter pour les idées (garde-fous, tests), pas pour le code. |

À reprendre aussi comme **pratiques** : tests Qt hors écran (`pytest`, plateforme `offscreen`), CI GitHub Actions (`.github/workflows/ci.yml`), cadrage par documents (`CAHIER_DES_CHARGES`, `ROADMAP`), et la discipline « refuser avant toute mutation plutôt que corrompre silencieusement ».

## 5. Feuille de route par phases

Chaque phase est livrée avec tests, doc à jour et commit(s) atomiques. Ne pas commencer la suivante sans critère d'acceptation vérifié.

**Phase 0 — Cadrage (1 session).** Créer le dépôt, `CLAUDE.md`, licence, `pyproject.toml` (PySide6, lxml ; extras : spellcheck), CI. Consigner l'architecture de la section 2 dans `docs/DECISIONS.md` (ADR courts). *Critère : `pytest` vert à vide, l'application s'ouvre sur une fenêtre vide.*

**Phase 1 — Catalogue TEI (livrable A).** A1 + A2 + A3. *Critère : `build_catalog.py` reproductible ; `docs/REGLES_ENCODAGE.md` ; tests sur 10 éléments clés.*

**Phase 2 — Audit et extraction (livrable B).** `docs/AUDIT_MEROPE.md`, extraction des modules retenus avec provenance, graphe d'imports vérifié (aucun `import bloggen`). *Critère : modules extraits testés isolément.*

**Phase 3 — Squelette applicatif.** `QMainWindow`, `QAction` centralisées, **menus complets** (Fichier : Nouveau [depuis modèle], Ouvrir, Récents, Enregistrer, Enregistrer sous, Exporter, Quitter ; Édition : annuler/rétablir, couper/copier/coller, rechercher/remplacer, aller à la ligne ; Insertion ; Balises ; Affichage : plan, inspecteur, problèmes, zoom, thème ; Outils : valider, profil actif, préférences ; Aide), éditeur texte avec coloration XML, barre d'état (position, XPath courant, profil, état de validité), préférences (`QSettings`), autosave/récupération, ouverture/enregistrement atomiques, détection d'encodage. *Critère : ouvrir/modifier/enregistrer un TEI existant sans aucune altération non voulue (test de round-trip octet à octet sur un corpus de fixtures).*

**Phase 4 — Bonne formation, validation, plan.** Parse lxml différé avec positions, soulignement des erreurs, panneau « Problèmes » (clic → saut), validation RelaxNG par profil, plan structurel (`QTreeView`) synchronisé avec le curseur, fil d'Ariane XPath. *Critère : erreurs localisées à la ligne et à la colonne près ; messages RelaxNG reformulés en français lisible.*

**Phase 5 — Édition guidée.** Palette contextuelle, **enveloppement de la sélection**, insertion avec fermeture automatique, dégrouper, renommer, scinder/fusionner `p`, inspecteur d'attributs typé (liste fermée, date, langue, `@ref` avec complétion sur les `xml:id`), génération d'`xml:id`, contrôle des références croisées. *Principe : suggérer de façon permissive (enfants possibles d'après le catalogue, sans calcul d'ordre), valider de façon stricte (RelaxNG) ; `libxml2` ne fournit pas « éléments valides ici ».* *Critère : toute opération se défait en un seul « annuler » ; aucune opération ne modifie le texte hors de la zone visée.*

**Phase 6 — Assistant d'en-tête TEI.** Dialogue à onglets : Titre et responsabilités (auteurs, éditeurs, `respStmt` multiples) ; Édition ; Publication (éditeur, lieu, date, identifiants, licence) ; Source (`bibl`, ou `msDesc` simplifié) ; Encodage (`projectDesc`, `editorialDecl`, `tagsDecl`) ; Profil (langues, mots-clés, résumé, participants) ; Révisions (`change`, avec ajout automatique optionnel à l'enregistrement). **Doit relire un en-tête existant et préserver tout élément qu'il ne gère pas.** Création par modèles (minimal valide, édition critique, théâtre, correspondance). *Critère : l'en-tête produit valide contre le profil actif ; round-trip sans perte sur des en-têtes réels.*

**Phase 7 — Jeux de balises.** Profil **« Édition de textes »** d'abord : structure (`div`/`head`/`p`), vers et strophes, normalisation (`choice` avec `orig`/`reg`, `abbr`/`expan`, `sic`/`corr`), lacunes et restitutions (`gap`, `supplied`, `unclear`), ajouts et suppressions, `pb`/`lb`/`cb`, notes, entités nommées (`persName`, `placeName`), apparat critique de base. Puis **« Théâtre »** (`sp`/`speaker`/`stage`, `castList`, vers partagés) et **« Édition critique »** (`app`/`lem`/`rdg`/`witness`). Profils personnalisables par l'utilisateur (JSON documenté) : choix des balises, raccourcis, attributs par défaut. *Critère : un acte de théâtre et une page d'édition critique saisis avec les seuls outils graphiques, valides.*

**Phase 8 — Finition de l'interface.** Jeu d'icônes SVG cohérent (libre de droits, monochrome, adapté aux thèmes), feuille de style Qt (QSS) claire/sombre, boutons uniformes (taille, survol, état désactivé), regroupement logique des barres d'outils, infobulles avec raccourcis, docks repositionnables, mémorisation de la disposition, interface en français, accessibilité (navigation clavier, contraste). *Critère : captures d'écran avant/après ; revue visuelle par l'utilisateur.*

**Phase 9 — Qualité et distribution.** Couverture des opérations d'édition par des tests hors écran, corpus de TEI réels (des projets de l'utilisateur) en tests de non-régression, documentation utilisateur, installation simple (`pipx`/`pip`, éventuellement un exécutable), numéro de version et journal des changements.

## 6. Règles de travail pour Claude Code (section à copier dans `CLAUDE.md`)

- Python ≥ 3.11, PySide6, lxml. Aucune dépendance supplémentaire sans validation.
- **Fidélité du XML avant tout** : ne jamais re-sérialiser tout le document pour une modification locale ; agir sur des plages de texte et vérifier par un test de round-trip.
- Pas d'accès réseau dans l'application ; analyse XML durcie (`xml_safety`).
- Une fonctionnalité = un module testable sans interface graphique + une fine couche Qt. Éviter les fichiers de plus de ~600 lignes.
- Chaque opération d'édition est une commande annulable en un seul pas (`QUndoStack` ou groupe d'annulation du `QTextDocument`).
- Le catalogue TEI fait foi : ne jamais coder des listes de balises ou de règles en dur dans l'interface.
- Avant tout choix d'architecture non prévu ici, proposer et attendre la validation.
- Messages d'erreur, menus et documentation en français ; identifiants de code en anglais.
- Tests : `pytest` avec `QT_QPA_PLATFORM=offscreen`.

## 7. Décisions à confirmer par l'utilisateur avant la phase 3

1. Mode « texte assisté » (recommandé) ou modèle graphique plus proche du WYSIWYG ?
2. Profils de validation à embarquer en priorité : `tei_all`, `TEI Lite`, Commons Publishing, profil Métopes/PURH ?
3. Nom et dépôt du nouveau projet ; licence.
4. Plateformes visées (Windows seul ou aussi macOS/Linux).
5. Fichiers TEI réels à fournir comme corpus de test.
