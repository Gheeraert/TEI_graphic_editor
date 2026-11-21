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

## ADR-0006 — Squelette applicatif (phase 3) : round-trip, encodage, undo natif, `QSettings`, autosave, « Exporter »

**Statut.** Adopté (phase 3).

**Contexte.** `docs/ROADMAP.md` §5 (phase 3) pose plusieurs choix d'implémentation non détaillés par les ADR précédents, avec pour critère d'acceptation central un round-trip octet à octet sur `tests/fixtures/tei-samples/`.

**Décisions.**

1. **Écriture atomique par octets, pas par texte, pour le document TEI.** `tei_editor.content.atomic_write.atomic_write_text` (repris de Mérope, ADR précédents) ouvre son flux en mode texte : Python y traduit toute fin de ligne écrite selon `os.linesep` de la plateforme, ce qui romprait le round-trip sur un fichier LF réécrit depuis Windows (`os.linesep == "\r\n"`). `atomic_write_bytes` est ajoutée au même module (même primitive de remplacement atomique, sans traduction) et c'est elle que `tei_editor.editor.text_editor.XmlTextEditor.save_to`/`export_copy_to` utilisent. `atomic_write_text` reste disponible pour du contenu non critique en octets (JSON de récupération, `tei_editor.recovery`).
2. **Détection d'encodage et de fin de ligne, mémorisées par document.** `tei_editor.editor.encoding.detect_encoding` reconnaît le BOM UTF-8/UTF-16 (LE/BE) s'il est présent, sinon lit la déclaration `encoding="..."` du prologue XML (en ASCII, donc valable pour UTF-8 et les encodages ASCII-compatibles ; **limite assumée** : un fichier UTF-16 *sans* BOM n'est pas détecté — il faudrait déjà connaître l'encodage pour lire son prologue), sinon UTF-8 par défaut (`docs/ROADMAP.md` §3.A3.1). La fin de ligne dominante (`\r\n`, `\n` ou `\r`) est détectée de la même passe. `decode_document` normalise le texte renvoyé en `"\n"` seul (la convention interne de `QTextDocument`, de toute façon appliquée dès que le texte entre dans un `QPlainTextEdit` — Qt n'offre pas de mode « fins de ligne brutes ») ; `encode_document` réapplique le BOM et la fin de ligne d'origine à l'enregistrement. **Limite assumée** : un fichier aux fins de ligne mixtes (`\n` et `\r\n` dans le même fichier) n'est pas préservé tel quel — seule la convention majoritaire est réappliquée partout (cas marginal, non rencontré dans le corpus de fixtures).
3. **Undo/redo : natif `QTextDocument`, pas de `QUndoStack`.** Conforme à ce que demande `docs/ROADMAP.md` §5 pour cette phase. `QUndoStack` devient nécessaire à partir de la phase 5 (opérations structurées comme « envelopper la sélection », qui doivent se défaire en un seul pas alors qu'elles mélangent plusieurs insertions/suppressions de texte) — la phase 5 devra remplacer le branchement actuel de `Actions.undo`/`Actions.redo` (connecté directement à `QPlainTextEdit.undo`/`redo`) par un `QUndoStack` applicatif.
4. **`QSettings("TIGRE", "TIGRE")` partout**, clefs centralisées dans `tei_editor.prefs.settings` (fichiers récents, thème, profil actif, autosave, géométrie de fenêtre). `MainWindow` accepte un `QSettings` (et un dossier de récupération) en paramètre optionnel pour permettre aux tests d'utiliser un `QSettings.Format.IniFormat` temporaire plutôt que le registre/les fichiers système réels — seul `tests/test_main_window.py` (non modifié dans son contenu, car un test déjà existant à ne pas casser) instancie encore `MainWindow()` sans argument, donc avec le `QSettings` réel par défaut ; c'est sans risque (`QSettings` n'écrit rien tant qu'aucun `setValue` n'est appelé, et une seule fermeture de fenêtre y écrit une poignée de petites clefs de géométrie sous `TIGRE`), mais un humain qui lance la suite de tests verra une entrée `TIGRE` apparaître dans son registre/ses fichiers de configuration applicatifs.
5. **Dossier d'autosave/récupération : `QStandardPaths.AppDataLocation`, sous-dossier `TIGRE/recovery`.** Le sous-dossier `TIGRE` est ajouté explicitement par `tei_editor.recovery.default_recovery_directory` plutôt que délégué à la qualification habituelle de `QStandardPaths` par organisation/application, qui suppose que `QCoreApplication.setOrganizationName`/`setApplicationName` ont été appelées — ce qui n'est pas garanti dans tous les contextes de lancement (notamment les tests). Un brouillon est identifié par une clef stable (hachage SHA-1 du chemin absolu du fichier ouvert, ou `"untitled"` pour un document « Sans titre »), stockée dans un fichier `<clef>.recovery.json` écrit via `atomic_write_text` (contenu JSON, pas de contrainte d'octets).
6. **« Exporter » interprété comme « exporter une copie »**, conformément à l'énoncé de la phase 3 : aucun format de sortie n'est prévu par ce projet (`docs/ROADMAP.md` §1), donc « Exporter » écrit une copie du XML TEI courant vers un chemin choisi (`XmlTextEditor.export_copy_to`), sans changer le fichier courant ouvert dans l'éditeur ni son état modifié, et sans retirer le brouillon de récupération associé au document réellement ouvert.
7. **Fil d'Ariane XPath courant : balayage du texte par expressions régulières, pas des positions `lxml`.** `lxml` n'expose que la ligne de *début* d'un élément (`sourceline`), pas la fin ; reconstruire les positions précises nécessiterait soit un analyseur incrémental, soit un second passage par ligne/colonne, prévus pour la phase 4 (« Parse lxml différé avec positions »). Pour cette phase, `tei_editor.editor.xpath.current_xpath` vérifie d'abord la bonne formation du document entier avec `parse_xml_safely` (comme demandé), puis reconstruit la pile d'imbrication jusqu'à la position du curseur par un balayage regex des balises (ouvrantes/fermantes/auto-fermantes, en ignorant commentaires/PI/CDATA). Renvoie `None` si le document est mal formé ; l'appelant affiche alors l'indicateur neutre `"— (document mal formé)"`.
8. **Coloration syntaxique : regex (`QRegularExpression`) sur `QSyntaxHighlighter`, générique (pas sémantique TEI)**, conformément à la phase 3. Les commentaires multi-lignes utilisent le mécanisme standard Qt de report d'état entre blocs (`previousBlockState`/`setCurrentBlockState`).
9. **Thème clair/sombre : une feuille de style Qt (QSS) statique appliquée à `QApplication`/`MainWindow.setStyleSheet`, pas de jeu de styles par composant.** La finition visuelle complète (palette cohérente, icônes SVG, contrastes vérifiés) reste pour la phase 8 ; ce commutateur n'est qu'un interrupteur fonctionnel, stocké dans `QSettings`.
10. **Un seul modèle de « Nouveau document » à ce stade** : le squelette minimal valide repris de `tests/fixtures/tei-samples/01-structure/01-minimal.xml` (constante `NEW_DOCUMENT_TEMPLATE` dans `tei_editor.editor.text_editor`), conformément à la phase 3 (« un seul modèle minimal valide pour l'instant »). Les modèles multiples par profil (théâtre, édition critique...) sont pour la phase 6/7.

## ADR-0005 — Résolution des décisions `docs/ROADMAP.md` §7

**Statut.** Adopté.

**Décisions.**

1. **Nom du projet : « TEI Graphic Editor — TIGRE ».** Le nom de paquet Python reste `tei_editor` (ADR-0002) : TIGRE est le nom/titre affiché (fenêtre, documentation), pas un renommage de code. Un renommage du paquet reste possible plus tard sur demande explicite.
2. **Profils de validation prioritaires : confirmés** — `tei_all`, `edition_textes`, `theatre`, `edition_critique` (déjà générés en phase 1). `commons_publishing` reste pour une phase ultérieure (schéma RNG/Schematron déjà extrait en phase 2, profil JSON pas encore construit).
3. **Plateformes visées : Windows, macOS, Linux.**
4. **Corpus de test réel : `tests/fixtures/tei-samples/`** — 21 documents (16 valides, 5 invalides) fournis par l'utilisateur, avec `README.md` et `manifest.json` propres indexant module/profil/éléments/erreurs attendues par fichier. Vérifié par `tests/test_tei_samples_corpus.py` : analyse durcie (`xml_safety`) de tous les cas valides, rejet effectif des cas « mal formé » et « xml:id dupliqué » (ce dernier refusé dès l'analyse par libxml2, qui traite `xml:id` comme un attribut ID), détection de référence `#id` non résolue. Les deux cas restants (« hors modèle », « en-tête incomplet ») demandent une validation RelaxNG/Schematron (phase 4) pour être détectés — non vérifiables avant cette phase, noté dans le README du corpus lui-même.

## ADR-0007 — Phase 4 : schéma RelaxNG unique (`tei_all`) et double couche d'avertissement, calcul par positions lxml

**Statut.** Adopté (phase 4).

**Contexte.** `docs/ROADMAP.md` §5 (phase 4) demande une validation RelaxNG par profil, un panneau de problèmes, un plan structurel synchronisé et un fil d'Ariane XPath calculé par positions `lxml` (l'approximation par balayage regex de la phase 3, ADR-0006 §7, était explicitement provisoire). Deux points n'étaient pas tranchés en détail.

**Décisions.**

1. **Schéma RelaxNG unique faisant autorité : `tei_all`.** Compiler une grammaire RelaxNG distincte et correcte par profil demanderait l'outillage officiel de compilation ODD (Roma/Java), hors de portée ici (voir aussi ADR-0003, qui pose déjà la même limite pour les enfants/parents approximatifs du catalogue). Le `tei_all.rng` du dépôt GitHub `TEIC/TEI` est signalé obsolète (copie de 2009) par `tests/fixtures/tei-samples/README.md` : il n'est pas utilisé. À la place, `tools/fetch_schema.py` télécharge le schéma RelaxNG précompilé officiel pour la version TEI P5 **4.12.0**, épinglée en phase 1 (même version que `p5subset.xml`, ADR-0003), depuis `https://www.tei-c.org/Vault/P5/4.12.0/xml/tei/custom/schema/relaxng/tei_all.rng` (URL vérifiée fonctionnelle : HTTP 200, en-tête du fichier confirmant « TEI Edition: P5 Version 4.12.0 », compilation réussie par `lxml.etree.RelaxNG`, validée sur `tests/fixtures/tei-samples/`). Le schéma est committé dans le dépôt (`src/tei_editor/data/schemas/tei_all/tei_all.rng`, avec `PROVENANCE.json`), comme `commons-publishing.rng` en phase 2 ; `.cache/tei/` reste le cache local non versionné du téléchargement. La validation RelaxNG de « Valider » et du panneau Problèmes se fait **toujours** contre ce schéma unique, quel que soit le profil actif.
2. **Le profil actif reste une liste blanche non bloquante, jamais une grammaire.** Conformément à ADR-0003 et à `docs/ROADMAP.md` phase 5 (« suggérer de façon permissive, valider de façon stricte »), le profil actif (`QSettings`, phase 3) ne restreint jamais la validité RelaxNG. En plus des diagnostics RelaxNG/bonne-formation (sévérité « erreur »), `tei_editor.editor.diagnostics.profile_warnings` calcule une catégorie séparée et non bloquante, « avertissement hors profil » : un élément du document absent de la liste blanche du profil actif (`src/tei_editor/data/profiles/*.json`). Le profil `tei_all` couvre les 588 éléments du catalogue et ne produit donc jamais cet avertissement ; un profil restrictif (ex. `edition_critique` face à un document théâtral) le produit pour chaque occurrence d'un élément hors liste, tout en laissant le document valide RelaxNG. Présentation retenue dans le panneau Problèmes : icône et couleur distinctes par sévérité (✖ rouge pour une erreur, ⚠ ocre pour un avertissement), tri par ligne puis par sévérité (erreurs avant avertissements à ligne égale) — laissé au jugement de l'implémentation, pas une exigence de cette décision.
3. **Fil d'Ariane XPath : calcul par l'arbre lxml réellement analysé, complété par un repérage minimal des positions de balises.** `lxml` ne donne que `Element.sourceline` (ligne de *début*, pas de colonne, pas de fin) : insuffisant à lui seul pour départager deux éléments sur la même ligne. `tei_editor.editor.xpath.current_xpath` analyse désormais le document avec `lxml` (structure, imbrication, index parmi les frères de même nom tous dérivés de l'arbre réel, plus robustes qu'une pile reconstruite à la main) et ne recourt à un balayage regex que pour une tâche limitée et non structurelle : repérer, dans l'ordre du document, la position de fin de chaque balise ouvrante/auto-fermante, pour départager les cas de même ligne. Heuristique retenue pour « l'élément courant » à une position donnée : le dernier élément, dans l'ordre du document, dont la balise ouvrante est entièrement refermée avant ou à cette position (les éléments auto-fermants ne sont jamais retenus comme élément courant, n'ayant pas de contenu). **Limite assumée, documentée dans le docstring du module** : un curseur placé après la fermeture d'un élément mais avant celle de son parent (ex. juste après `</p>` et avant `</div>`) reste rattaché au `p` déjà refermé, `lxml` ne donnant pas sa ligne de fin pour détecter ce retour au parent — approximation jugée acceptable pour un indicateur informatif de barre d'état, pas pour une opération d'édition structurée (phase 5).
4. **Soulignement des erreurs : `QPlainTextEdit`/`QTextEdit.ExtraSelection`, pas une extension de `XmlHighlighter`.** Les diagnostics changent à chaque re-parsing différé (debounce 400 ms existant), sur des plages dynamiques sans rapport avec les règles lexicales stables de la coloration syntaxique. Remplacer en bloc la liste des `ExtraSelection` (`tei_editor.editor.diagnostics_overlay.apply_diagnostic_highlights`) évite de déclencher un nouveau passage de `QSyntaxHighlighter` sur tout le document à chaque frappe.

**Conséquences.** La validation reste simple à raisonner (un seul schéma, pas de divergence de grammaire par profil) ; la palette de balises par profil (phase 7) continue de s'appuyer sur les mêmes listes blanches JSON, maintenant aussi utilisées pour ce nouvel avertissement. Le fil d'Ariane XPath et le plan structurel partagent la même notion de « position » (ligne lxml), avec les limites ci-dessus assumées plutôt que masquées.

## ADR-0008 — Phase 5 : blocs d'annulation natifs, et une exception assumée à « le catalogue fait foi »

**Statut.** Adopté (phase 5).

**Décisions.**

1. **Undo natif par bloc, pas de `QUndoStack`.** Chaque opération structurée (envelopper, insérer, dégrouper, renommer, scinder/fusionner un `p`, modifier/retirer un attribut, générer un `xml:id`) encadre toutes ses modifications de texte entre `QTextCursor.beginEditBlock()`/`endEditBlock()` sur un même curseur réutilisé (`editor.structured_edits.apply_edits_with_cursor`), ce qui en fait un seul pas pour l'undo/redo natif de `QTextDocument` déjà câblé depuis la phase 3 (ADR-0006 §undo). Pas de `QUndoStack` séparé : il dupliquerait un état déjà porté par le document. Vérifié par test pour chacune des 8 opérations.
2. **Exception assumée à « le catalogue fait foi, jamais de liste de balises codée en dur » (`CLAUDE.md`) : `editor.structured_edits`/`tei.catalog.TYPICALLY_EMPTY_ELEMENTS` est une petite liste statique** (`lb`, `pb`, `cb`, `gap`, `anchor`, `milestone`, `graphic`, `space`) utilisée uniquement pour décider si l'insertion automatique produit `<ident/>` plutôt que `<ident></ident>`. Raison : le catalogue n'a pas d'indicateur fiable pour « élément typiquement vide » — `children_approx` (ADR-0003) est une approximation du modèle de contenu compilé, pas une déclaration de vacuité, et des éléments presque toujours encodés vides en pratique (ex. `gap`) y ont malgré tout des références non vides. Portée de l'exception strictement limitée à ce choix cosmétique (une balise auto-fermante ou non) : elle ne pilote ni la validation, ni la palette, ni aucune autre décision de contenu — ces dernières continuent de s'appuyer uniquement sur le catalogue et les profils JSON.

**Conséquences.** L'undo/redo reste un mécanisme unique et prévisible pour tout le projet (natif, pas deux systèmes parallèles). La liste statique de la décision 2 devra être revue si le calcul de `children_approx` (phase 1) devient un jour assez fiable pour en déduire la vacuité typique d'un élément ; en l'état, elle reste la seule dérogation connue à la règle « catalogue fait foi » et doit rester limitée à ce cas précis.

## ADR-0009 — Phase 7 : commandes composites (jeux de balises), convention `@part`/`@n` pour le vers partagé, profils déjà complets

**Statut.** Adopté (phase 7).

**Contexte.** `docs/ROADMAP.md` §5 (phase 7) demande quatre commandes composites (« Grouper en choix… », « Insérer une liste de personnages… », « Marquer un vers partagé », « Insérer une leçon (app/lem/rdg)… ») au-dessus des opérations génériques de la phase 5, plus la vérification/complétion des quatre profils JSON et du critère « profils personnalisables ». `docs/AUDIT_EKDOSIS.md` documente l'étude du dépôt externe ekdosis-TEI-Studio (lecture seule, idées éditoriales uniquement, rien de copié).

**Décisions.**

1. **Les quatre profils JSON (`tei_all`, `edition_textes`, `theatre`, `edition_critique`) étaient déjà complets** (vérifié par lecture et par `tests/test_tei_catalog.py`, déjà existant depuis la phase 1) : tous les éléments attendus par cette phase (`choice`/`orig`/`reg`/`sic`/`corr`/`abbr`/`expan`/`gap`/`supplied`/`unclear`/`add`/`del`/`pb`/`lb`/`cb`/`persName`/`placeName`, `castList`/`castItem`/`role`/`roleDesc`/`set`/`performance`/`sp`/`speaker`/`stage`, `app`/`lem`/`rdg`/`rdgGrp`/`wit`/`witDetail`/`listWit`/`witness`/`listApp`) y figuraient déjà. Aucune modification des profils n'a été nécessaire.
2. **Nouveau module `editor/snippets.py`** (fonctions de planification pures, même patron que `editor/structured_edits.py`) plutôt qu'un ajout dans ce dernier, pour rester sous la limite indicative de `CLAUDE.md` et parce que ce sont des opérations de niveau supérieur (composées), pas des primitives. `editor/snippet_commands_mixin.py` fait le pont avec Qt, séparé de `editor/tag_commands_mixin.py` pour la même raison. Les quatre commandes réutilisent `structured_edits.apply_edits_with_cursor` (un seul bloc d'annulation natif, ADR-0008) ; « Marquer un vers partagé » réutilise aussi `structured_edits.plan_set_attribute` plutôt que de réécrire la balise ouvrante du `<l>` à la main.
3. **Paires `choice` dans une donnée JSON neuve (`data/snippets/choice_pairs.json`), pas codées en dur.** Conforme à `CLAUDE.md` : ce n'est pas une nouvelle dérogation à « le catalogue fait foi » (ADR-0008 point 2 reste la seule dérogation à cette règle, strictement bornée à la vacuité typique d'un élément) — c'est une petite donnée de configuration documentée, du même ordre que les profils JSON, pas une liste de structures codée dans le widget.
4. **Convention `@part`/`@n` pour le vers partagé, reconstituée depuis la définition standard de `att.fragmentable` dans `tei_catalog.json`** (valeurs `I`/`M`/`F`), pas copiée depuis une occurrence concrète d'ekdosis-TEI-Studio (ses fixtures effectivement consultées ne contenaient pas d'exemple direct de `@part`, voir `docs/AUDIT_EKDOSIS.md`) : `plan_mark_shared_verse` met `@part="I"`/`@n=valeur` sur le fragment qui reste dans la réplique d'origine et insère un nouveau `<l part="F" n=valeur>` au début (ou juste après `<speaker>`) de la réplique suivante. Vérifiée par un test de bout en bout contre `tei_all.rng`.
5. **Piège ekdosis identifié et non reproduit** : `<stage type="DI" ana="#SET">` enveloppant directement des `<l>` (didascalie implicite) n'est pas un modèle de contenu valide pour `stage` en TEI P5 standard (`stage` n'a aucun enfant dans `children_approx`, modèle purement phrastique) — confirmé avant toute décision, pas reproduit par aucune commande de cette phase. Détail dans `docs/AUDIT_EKDOSIS.md`.
6. **`listWit` structurée non ajoutée à l'assistant d'en-tête** (`header_dialog/tab_edition_source.py`, phase 6) par manque de temps face au reste du périmètre de cette phase ; documenté comme limitation dans `docs/AUDIT_EKDOSIS.md`, piste pour une phase ultérieure. Le critère d'acceptation central (test de bout en bout) reste satisfait sans cette extension : le `listWit` y est construit avec les opérations génériques existantes.
7. **« Profils personnalisables » déjà acquis** : `tei_editor.tei.profiles.list_profiles()` scanne déjà tout `data/profiles/*.json` (vérifié, aucune modification de code nécessaire) ; `docs/PROFILS.md` (nouveau, un paragraphe) documente le format pour un utilisateur qui voudrait en créer un cinquième.

**Conséquences.** Les quatre commandes composites de cette phase suivent exactement le même mécanisme d'annulation et la même séparation pur/Qt que la phase 5, sans introduire de second mécanisme. Le critère d'acceptation central de la phase (« un acte de théâtre et une page d'édition critique saisis avec les seuls outils graphiques, valides ») est vérifié par `tests/test_phase7_end_to_end.py`, qui construit les deux documents en n'appelant que des fonctions publiques (génériques phase 5 + composites phase 7) et les valide contre `tei_all.rng`.

## ADR-0010 — Phase 8 : jeu d'icônes Lucide, substitutions de noms, feuilles de style neuves, barres d'outils séparées

**Statut.** Adopté (phase 8).

**Contexte.** `docs/ROADMAP.md` §5 (phase 8) demande un jeu d'icônes SVG libre de droits et adapté aux thèmes, une feuille de style Qt claire/sombre soignée (remplaçant la `_DARK_STYLESHEET` statique posée en phase 3, ADR-0006 point 9), des barres d'outils regroupées logiquement, des infobulles avec raccourci, et de l'accessibilité (focus clavier, contraste). Le choix du jeu d'icônes (Lucide, licence ISC) et la correspondance action -> icône de départ étaient déjà fixés par la consigne de cette phase ; plusieurs points restaient à trancher pendant l'implémentation.

**Décisions.**

1. **Quatre noms d'icônes Lucide suggérés par la roadmap n'existent plus dans le jeu actuel** (vérifié par téléchargement effectif, pas par supposition) : `fingerprint` -> **`hash`** (seconde option déjà proposée par la roadmap), `split-square-horizontal` -> **`columns-2`** (idem), `triangle-alert`/`alert-triangle` -> **`triangle-exclamation-point`** (triangle d'avertissement équivalent du jeu courant), `check-circle-2`/`check-circle` -> **`circle-check-big`** (coche dans un cercle, variante épaisse). Chaque substitution est documentée nommément dans `tools/fetch_icons.py` (`SUBSTITUTIONS`) et répercutée dans `data/icons/PROVENANCE.json`, jamais faite silencieusement.
2. **Correspondance action -> icône en donnée externe (`data/icons/action_icons.json`), pas codée en dur dans un widget**, conformément à `CLAUDE.md` (principe des données externalisées, déjà appliqué au catalogue/profils/paires `choice`) ; `tools/fetch_icons.py` la définit une seule fois (`ACTION_ICONS`) et l'écrit à la fois comme fichier de données et comme base de `PROVENANCE.json`, pour qu'il n'y ait qu'une source.
3. **Substitution `currentColor` -> couleur du thème en mémoire, à l'usage** (`tei_editor.ui.icons`), pas un second jeu de fichiers SVG par couleur committé : les SVG Lucide sont récupérés tels quels (`stroke="currentColor"`), et c'est `QSvgRenderer` qui rend, à chaque appel, les octets déjà recolorés par un simple remplacement de chaîne. La couleur utilisée est exactement `tei_editor.ui.theme.foreground_color(theme_id)`, donc toujours identique à la couleur de texte réellement déclarée dans la feuille de style active (pas une couleur arbitraire distincte).
4. **Palette de couleurs neuve, définie comme données Python (`tei_editor.ui.theme.THEMES`), pas des couleurs littérales dispersées dans un gabarit QSS.** `stylesheet_for()` compose la feuille de style à partir de ces mêmes constantes, et le test de contraste WCAG (`tests/test_theme_contrast.py`) les relit directement : un seul endroit où les couleurs sont déclarées, jamais de divergence possible entre ce qui s'affiche et ce qui est mesuré. Thème sombre : esprit Monokai conservé (couleurs de phase 3 reprises pour le texte/fond). Thème clair : neuf, sobre, contraste fort. Ratios WCAG vérifiés par test, ≥ 4.5:1 pour texte principal/fond et texte désactivé/fond des deux thèmes (contre une couleur de fond de fenêtre *et* de surface — docks/listes ont un fond légèrement différent de la fenêtre).
5. **Barres d'outils construites dans un module séparé (`tei_editor.ui.toolbars`), pas dans `main_window.py`**, comme `menus.py` le fait déjà pour la barre de menus (`CLAUDE.md`, limite indicative de ~600 lignes par fichier). Quatre barres (« Fichier », « Édition », « Balises », « Affichage »), chacune avec un `objectName` explicite : sans lui, `QMainWindow.saveState()`/`restoreState()` ignore silencieusement la barre à la restauration (vérifié par test, `tests/test_toolbars_layout.py`) — le même risque existait déjà pour les docks depuis la phase 3 (aucun n'avait de `objectName`) ; corrigé à cette occasion pour les quatre docks existants.
6. **Les `QToolButton` d'une `QToolBar` n'acceptent pas le focus clavier par défaut dans Qt** (`Qt.FocusPolicy.NoFocus`, comportement de la bibliothèque, pas un oubli de ce projet) : `tei_editor.ui.toolbars._enable_keyboard_focus` l'active explicitement (`Qt.FocusPolicy.TabFocus`) sur chaque bouton après construction, condition nécessaire à leur présence dans la chaîne `Tab`/`Shift+Tab` (vérifié par test, `tests/test_focus_order.py`).
7. **Correspondance action -> nom logique aplatie une seule fois (`tei_editor.ui.action_registry.flatten_actions`)**, réutilisée à la fois par `tei_editor.ui.icons.apply_action_icons` et par `tei_editor.ui.tooltips.apply_tooltips_with_shortcuts` : une seule liste de correspondance entre l'arborescence de `Actions` (dataclasses imbriquées) et les clefs de `action_icons.json`, jamais deux listes parallèles qui pourraient diverger.

**Conséquences.** Le thème (couleurs + icônes) reste un point d'entrée unique (`MainWindow._apply_theme`), appelé à l'initialisation et à chaque changement de thème, qui pose la feuille de style *et* recolore toutes les icônes d'action en une seule fois. Les captures d'écran avant/après (`docs/screenshots/phase8_avant.png`, `phase8_apres.png`) illustrent ce critère d'acceptation explicite de la roadmap.

## ADR-0011 — Phase 9 : numéro de version 1.0.0, pas d'exécutable multiplateforme, lacune de `package-data` corrigée

**Statut.** Adopté (phase 9).

**Contexte.** `docs/ROADMAP.md` §5 (phase 9) demande un numéro de version et un journal des
changements, en notant que les 9 phases couvrent désormais l'intégralité du plan initial. Le projet
était resté en `0.1.0` (version posée à la phase 0, jamais retouchée depuis) à la fois dans
`pyproject.toml` et `src/tei_editor/__init__.py`. Un exécutable autonome est demandé «
éventuellement » par la même section, et l'installation « simple » (`pipx`/`pip`) devait être vérifiée
réellement, pas seulement relue.

**Décisions.**

1. **Version `1.0.0`, pas `0.9.0`/`0.10.0`.** Un `0.x` signale conventionnellement (SemVer) un projet
   encore instable dont l'API/le comportement peuvent changer sans préavis à chaque mineure. Ce
   n'est plus la situation de TIGRE à l'issue de cette phase : les 9 phases du plan initial
   (`docs/ROADMAP.md` §5, phases 0 à 9) sont toutes implémentées et chacune a son critère
   d'acceptation vérifié (round-trip octet à octet, validation RelaxNG, jeux de balises de bout en
   bout, finition visuelle, et maintenant couverture ciblée + installation réelle) — c'est
   raisonnablement la définition même d'une version « 1.0 » pour un projet dont le plan initial est
   un ensemble fini de phases plutôt qu'un flux continu de fonctionnalités. `0.10.0` aurait suggéré
   un simple incrément parmi d'autres plutôt qu'un jalon ; `1.0.0` marque explicitement que le plan
   initial est tenu en entier. Les versions ultérieures (corrections, extensions au-delà du plan
   initial — ex. la `listWit` structurée notée comme piste par ADR-0009 point 6) suivront SemVer
   normalement à partir de ce point (`1.0.x` pour un correctif, `1.x.0` pour une extension
   compatible).
2. **Pas d'exécutable autonome construit dans cette phase, documenté comme limitation plutôt que
   bâclé.** La roadmap ne le demande qu'« éventuellement » (pas un critère d'acceptation). Un script
   PyInstaller ne fait pas de compilation croisée : exécuté sur cette machine (Windows), il ne peut
   produire qu'un exécutable Windows, jamais macOS/Linux simultanément. Plutôt que prétendre à un
   résultat multiplateforme non vérifiable depuis cette session, `docs/INSTALLATION.md` documente
   cette limite explicitement et donne la commande PyInstaller (non exécutée, non vérifiée) pour qui
   voudrait la tenter sur chaque plateforme cible.
3. **Lacune réelle découverte par la vérification effective de l'installation : `package-data`
   manquant.** Le critère « installation vérifiée dans un venv propre, pas de suppositions non
   testées » a été pris au sérieux : un `pip install .` réel dans un venv neuf, puis un lancement
   réel de `tei-editor` (`QT_QPA_PLATFORM=offscreen`), a révélé que `pyproject.toml` n'embarquait que
   les fichiers `.py` — `src/tei_editor/data/` (catalogue, profils, schémas RelaxNG, icônes, paires
   `choice`) en était absent, et l'application plantait au démarrage (`FileNotFoundError` sur
   `action_icons.json`). `pytest` ne l'avait jamais détecté : les tests tournent depuis le dépôt, pas
   depuis un paquet installé. Corrigé par `[tool.setuptools.package-data] tei_editor =
   ["data/**/*"]`, revérifié par une réinstallation complète dans le même venv (lancement réussi,
   fermeture propre), et gardé par un nouveau test (`tests/test_packaging.py`) qui n'a pas besoin de
   reconstruire un paquet pour détecter la régression.

**Conséquences.** Le numéro de version reflète maintenant l'achèvement du plan initial plutôt qu'un
compteur resté figé depuis la phase 0. L'absence d'exécutable autonome est une limitation assumée et
documentée, pas un oubli silencieux. La correction de `package-data` est le seul changement de
comportement de cette phase qui touche à autre chose que la documentation/les tests — nécessaire
pour que le critère d'acceptation « installation vérifiée » de cette même phase soit satisfait.
