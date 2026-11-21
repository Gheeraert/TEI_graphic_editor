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
