# Journal de décisions d'architecture (ADR courts)

## ADR-0001 — Texte XML assisté, pas de pivot objet, pas de WYSIWYG

**Statut.** Adopté (phase 0), à reconfirmer avant la phase 3 (voir `docs/ROADMAP.md` §7).

**Contexte.** Mérope encode son éditeur Qt autour d'un pivot `Block`/`InlineRun` pensé pour du Markdown à structure plate. TEI est un arbre XML à contenu mixte, attributs et imbrication libre : ce pivot ne se transpose pas sans perte (contenu mixte, commentaires, PI, espaces significatifs, ordre des attributs).

**Décision.** La source de vérité du document est son texte XML, édité dans un `QPlainTextEdit` avec coloration syntaxique. L'interface graphique (palette de balises, inspecteur d'attributs, plan structurel, panneau de problèmes) est une assistance posée au-dessus de ce texte, jamais un modèle objet qui s'y substitue. Le modèle structurel (arbre lxml) est **dérivé** du texte par re-parsing différé (debounce) ; jamais l'inverse. Aucune sérialisation « pretty-print » qui toucherait au contenu mixte.

**Conséquences.** Round-trip fidèle garanti par construction. Pas d'objet « étranger » refusé par un modèle qui ne sait pas le retranscrire. Coût de développement réduit par rapport à un portage du pivot `Block`/`InlineRun`. En contrepartie, pas de rendu visuel des balises en v1 (une variante « pastilles » inline reste possible plus tard, toujours adossée au texte XML).

## ADR-0002 — Nom de paquet provisoire

**Statut.** Provisoire, à reconfirmer avant la phase 3 (voir `docs/ROADMAP.md` §7, point 3).

**Décision.** Le paquet Python est nommé `tei_editor` (répertoire `src/tei_editor/`) en l'absence d'un nom de projet choisi par l'utilisateur. Renommage trivial si un autre nom est retenu.

## ADR-0003 — Génération du catalogue TEI : version épinglée et approximation enfants/parents/attributs

**Statut.** Adopté (phase 1).

**Contexte.** Le catalogue des balises (`src/tei_editor/data/tei_catalog.json`) doit être généré depuis les sources officielles TEI P5, pas écrit à la main (`docs/ROADMAP.md` §3.A1). Le fichier source `p5subset.xml` encode un modèle de contenu compilé (RelaxNG simplifié, avec `classRef`/`elementRef`/`macroRef`/`dataRef`) et des attributs partiellement portés par des classes d'attributs (`att.*`), pas uniquement par chaque `elementSpec`. Reconstruire un interpréteur de grammaire RelaxNG complet pour en déduire les enfants/parents exacts serait un sur-engineering hors du périmètre de cette phase (la validation stricte, via RelaxNG, est prévue en phase 4).

**Décisions.**

1. **Version épinglée.** `tools/build_catalog.py` télécharge une version précise et vérifiée fonctionnelle de `p5subset.xml` (TEI P5 **4.12.0**, `https://www.tei-c.org/Vault/P5/4.12.0/xml/tei/odd/p5subset.xml`), mise en cache localement (`.cache/tei/`, non versionné). Le numéro de version est écrit dans les métadonnées du catalogue (`tei_version`, `source_url`) et dans l'introduction de `docs/REGLES_ENCODAGE.md`. Remonter de version TEI est un geste explicite (changer `TEI_VERSION` dans le script), jamais un effet de bord d'une exécution.
2. **Enfants/parents approximatifs.** Pour chaque `elementSpec`, on parcourt son `<content>` et on collecte toutes les références (`classRef`, `elementRef`) qu'il contient, à n'importe quelle profondeur d'imbrication (`alternate`/`sequence`), sans tenter d'interpréter l'arbre de grammaire (ordre, cardinalités, alternatives exclusives). Une `classRef` est résolue en un ensemble d'éléments via la fermeture transitive de la relation `memberOf` entre classes (une classe B qui déclare `memberOf A` rend membres de A, par transitivité, tous les éléments membres de B). Le résultat (`children_approx` / `parents_approx`, ce dernier obtenu par inversion) est stocké comme **suggestion pour une palette de balises**, jamais comme source de validité : c'est la reformulation, pour cette phase, du principe déjà posé par ADR-0001 et par `docs/ROADMAP.md` phase 5 (« suggérer de façon permissive, valider de façon stricte »). La validation réelle viendra d'un schéma RelaxNG en phase 4/5.
3. **Attributs résolus par héritage de classes.** Plutôt que de s'en tenir aux seuls attributs déclarés directement sur chaque `elementSpec` (minimum pragmatique jugé acceptable par la roadmap), le script résout aussi les attributs hérités des classes d'attributs (`att.*`) dont l'élément est membre, transitivement (p. ex. `att.divLike` → `att.global` pour `@xml:id`/`@xml:lang`). Chaque attribut résolu porte un champ `source` (`"own"` ou l'identifiant de la classe d'origine). Limite assumée : les `<constraintSpec>` (contraintes Schematron conditionnant la présence/valeur d'un attribut selon le contexte) ne sont pas interprétées ; un attribut listé comme possible n'est donc pas garanti pertinent dans tous les contextes d'usage de l'élément.

**Conséquences.** Le catalogue reste reproductible (cache local, numéro de version explicite) et documente ses propres limites dans son champ `notes`. L'interface (palette de balises, phase 7) pourra s'appuyer sur `children_approx`/`parents_approx`/`attributes` pour suggérer, mais toute vérification de validité devra passer par le schéma RelaxNG du profil actif (phase 4), jamais par ces champs.

## ADR-0004 — Trois décisions prises pendant l'extraction (phase 2)

**Statut.** Adopté (phase 2).

**Contexte.** `docs/AUDIT_MEROPE.md` documente l'audit complet. Trois points, non prévus dans le détail par `docs/ROADMAP.md` §4, ont demandé un choix pendant l'extraction effective.

**Décisions.**

1. **`xml_safety.parse_xml_safely` ne supprime plus commentaires/PI.** La version Mérope (`remove_comments=True, remove_pis=True`) part du principe que ces nœuds sont toujours absents en pratique (TEI produit par Pandoc) et visait surtout à égaler le comportement de `xml.etree.ElementTree`. Ici, conformément à ADR-0001 (fidélité du contenu mixte, round-trip sans perte), ces nœuds sont conservés par défaut. La fonction `parse_xml_safely_for_elementtree` (qui existait pour satisfaire ce besoin de compatibilité ET/lxml côté Mérope) n'est pas reprise : cet éditeur reste sur lxml partout.
2. **`tei/commons_publishing.py` résout `_SCHEMA_PATH` vers `tei_editor/data/schemas/commons-publishing/`** (au lieu de `bloggen/resources/schemas/...`), même convention (chemin relatif au fichier, pas au répertoire de travail courant). Le schéma RNG, sa `LICENSE.txt` et sa `PROVENANCE.json` sont copiés tels quels (fichiers tiers, provenance et licence propres conservées, distinctes de la provenance du code Mérope).
3. **`typography.py` est placé sous `tei/typography.py`**, pas sous un éventuel futur paquet `markdown/` (qui n'existe pas dans ce projet, TEI n'étant pas du Markdown) : ces transformations de texte pur (guillemets, espaces insécables, ligature œ) sont génériques mais leur seul point d'application prévu est le contenu textuel d'un document TEI (ADR-0001, §4 de `docs/ROADMAP.md`). Seules les fonctions de texte pur sont reprises ; `split_century_ordinals`/`_split_run_by_century` (couplées au pivot `InlineRun` de Mérope) sont laissées de côté — voir `docs/AUDIT_MEROPE.md`.

**Conséquences.** Aucune de ces décisions ne change l'architecture adoptée en ADR-0001/0002. Elles sont consignées ici plutôt que tranchées silencieusement, conformément à `CLAUDE.md`.

## ADR-0005 — Résolution des décisions `docs/ROADMAP.md` §7

**Statut.** Adopté.

**Décisions.**

1. **Nom du projet : « TEI Graphic Editor — TIGRE ».** Le nom de paquet Python reste `tei_editor` (ADR-0002) : TIGRE est le nom/titre affiché (fenêtre, documentation), pas un renommage de code. Un renommage du paquet reste possible plus tard sur demande explicite.
2. **Profils de validation prioritaires : confirmés** — `tei_all`, `edition_textes`, `theatre`, `edition_critique` (déjà générés en phase 1). `commons_publishing` reste pour une phase ultérieure (schéma RNG/Schematron déjà extrait en phase 2, profil JSON pas encore construit).
3. **Plateformes visées : Windows, macOS, Linux.**
4. **Corpus de test réel : `tests/fixtures/tei-samples/`** — 21 documents (16 valides, 5 invalides) fournis par l'utilisateur, avec `README.md` et `manifest.json` propres indexant module/profil/éléments/erreurs attendues par fichier. Vérifié par `tests/test_tei_samples_corpus.py` : analyse durcie (`xml_safety`) de tous les cas valides, rejet effectif des cas « mal formé » et « xml:id dupliqué » (ce dernier refusé dès l'analyse par libxml2, qui traite `xml:id` comme un attribut ID), détection de référence `#id` non résolue. Les deux cas restants (« hors modèle », « en-tête incomplet ») demandent une validation RelaxNG/Schematron (phase 4) pour être détectés — non vérifiables avant cette phase, noté dans le README du corpus lui-même.
