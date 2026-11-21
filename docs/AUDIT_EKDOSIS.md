# Audit du dépôt ekdosis-TEI-Studio (phase 7)

Source auditée : dépôt public **ekdosis-TEI-Studio**
(`https://github.com/gheeraert/ekdosis-TEI-Studio`), cloné en lecture seule
dans un dossier temporaire (`git clone --depth 1`, sous-dossier
`fixtures/site_builder/legacy_reference/` ignoré — noms de fichiers trop
longs pour Windows, et hors sujet). Dépôt **jetable**, non modifié, non
conservé : seule la sortie TEI de ses fixtures a été consultée, jamais son
code.

**Nature du dépôt, et ce qui n'en a été repris.** ekdosis-TEI-Studio est un
outil complet (pivot de saisie en pseudo-Markdown → TEI canonique →
HTML/LaTeX/publication imprimée), avec sa propre interface Tkinter/Flask et
une chaîne de publication entière — architecture radicalement différente de
TIGRE (ADR-0001 : TIGRE n'a pas de pivot, le texte XML est la seule source
de vérité ; TIGRE n'a pas de chaîne de publication, `docs/ROADMAP.md` §1).
**Aucune ligne de code n'en a été copiée ou portée.** Seule la sortie TEI de
quelques fixtures (`fixtures/shared_verse/`, `fixtures/variant_head_and_cast/`,
`fixtures/implied_stage_directions/`, `fixtures/ekdosis_from_tei/`,
`fixtures/annotations/`) a servi de référence de **pratique éditoriale
réelle et mûrie** pour le théâtre classique français avec apparat critique —
et chaque convention envisagée a été vérifiée contre notre schéma RelaxNG
unique (`src/tei_editor/data/schemas/tei_all/tei_all.rng`) et/ou
`tei_catalog.json` avant toute décision, conformément à la consigne : « ce
dépôt sert de référence d'idées éditoriales, pas de modèle XML à copier
aveuglément ».

## Ce qui a été retenu (confirmé par le schéma/catalogue avant adoption)

| Convention observée chez ekdosis | Où | Vérification faite | Décision |
|---|---|---|---|
| `listWit`/`witness[@xml:id]` dans `sourceDesc`, un `witness` par témoin avec sa description en texte | `fixtures/annotations/berenice_1_1/expected_annotated.xml`, `fixtures/ekdosis_from_tei/*/input.xml` | `listWit`/`witness` déjà dans le catalogue (`tei_catalog.json`) et dans les groupes `header_source`/`apparatus` des profils `edition_textes`/`theatre`/`edition_critique` (déjà présents avant cette phase, vérifié, pas ajoutés). | **Retenu comme idée** pour le test de bout en bout (`tests/test_phase7_end_to_end.py`) : construction d'un `listWit` avec deux `witness[@xml:id]` via les opérations génériques de la phase 5 (dégrouper/insérer/attribut `xml:id`). Non intégré à l'assistant d'en-tête (`header_dialog/`) par manque de temps — voir « Limitations » ci-dessous. |
| `app`/`lem[@wit]`/`rdg[@wit]`, un `lem` et un ou plusieurs `rdg`, chacun avec une liste de pointeurs `@wit="#A #B"` | `fixtures/shared_verse/thebaide_2_2/expected.xml`, `fixtures/variant_head_and_cast/*/expected*.xml` | `@wit` sur `lem`/`rdg` confirmé optionnel (`usage: "opt"`) dans `tei_catalog.json`, classe `att.witnessed`. | **Retenu** : commande composite « Insérer une leçon (app/lem/rdg)… » (`editor/snippets.py::plan_insert_apparatus`). `@wit` n'est volontairement **pas** pré-rempli par la commande (voir plus bas, § « Rejeté/adapté ») : l'utilisateur le renseigne ensuite avec l'inspecteur d'attributs existant (opération générique de la phase 5), plutôt qu'une valeur fictive insérée par la commande. |
| Vers partagé entre deux répliques : même `@n` sur les deux fragments, `l/@part` pour distinguer la partie initiale/finale | Nom du dossier `fixtures/shared_verse/`, mais la convention `@part`/`@n` elle-même n'y est pas démontrée explicitement (voir « Piège » ci-dessous : le dossier ne contient pas d'occurrence `part=` dans son XML attendu) | **`l/@part`** confirmé dans `tei_catalog.json` (classe `att.fragmentable`), valeurs fermées `Y`/`N`/`I`/`M`/`F` avec la glose standard TEI P5 (« initial part of a fragmented element », etc.) — c'est la définition standard de TEI, pas une invention d'ekdosis. | **Retenu**, mais la convention exacte (même `@n`, `@part="I"` sur le premier fragment, `@part="F"` sur le second) est reconstituée depuis la définition standard TEI P5 de `@part`, pas copiée depuis une occurrence concrète d'ekdosis (il n'y en avait pas dans les fixtures effectivement consultées). Implémentée par `editor/snippets.py::plan_mark_shared_verse`, testée contre `tei_all.rng` dans `tests/test_phase7_end_to_end.py`. |
| `castList`/`castItem`/`role` pour la distribution, `stage[@type="personnages"]` en tête de scène | `fixtures/variant_head_and_cast/*/expected*.xml` | Déjà dans le catalogue et dans le profil `theatre` (groupe `theatre`, vérifié, déjà présent). | **Retenu comme idée** pour la commande composite « Insérer une liste de personnages… » (`editor/snippets.py::plan_insert_cast_list`), qui ne fait que généraliser ce patron (n `castItem`/`role` demandés à l'utilisateur) sans rien copier de spécifique à ekdosis. |

## Ce qui a été écarté, et pourquoi

| Observation | Où | Pourquoi écarté |
|---|---|---|
| **Piège repéré et confirmé invalide** : `<stage type="DI" ana="#SET">` enveloppant directement des `<l>` (didascalie implicite marquant plusieurs vers) | `fixtures/implied_stage_directions/berenice/expected.xml`, lignes autour de `berenice-implicite1`/`berenice-implicite2` | Vérifié contre `tei_catalog.json` : `stage` n'a **aucun** enfant dans `children_approx` (modèle de contenu purement phrastique en TEI P5 standard, pas un conteneur de `l`). Le pipeline d'ekdosis tolère ou retraite cette construction en aval (génération HTML/LaTeX propre) ; notre validateur RelaxNG (`tei_all`) la rejetterait. **Non reproduit** : aucune commande de cette phase ne permet d'envelopper des `<l>` dans un `<stage>`. L'idée éditoriale sous-jacente (marquer une didascalie implicite reconstituée par l'édition, via `@ana` vers une taxonomie interprétative) reste intéressante mais demanderait une structure différente (ex. `<stage>` phrastique + `@ana` juste avant le passage concerné, ou un `<span>`/`<seg>` avec le même `@ana`) — non implémentée dans cette phase, faute de besoin exprimé par la roadmap, notée ici comme piste. |
| `@wit` pré-rempli avec une valeur placeholder (`#...`) dans l'énoncé de la commande « Insérer une leçon » | Énoncé de la tâche, pas une observation directe d'ekdosis | Une valeur `wit="#..."` littérale serait un pointeur TEI syntaxiquement valide mais sémantiquement creux (référence à un `xml:id` `...` qui n'existe pas) — pire qu'une absence d'attribut. La commande laisse `@wit` absent ; l'inspecteur d'attributs (phase 5) sert à le renseigner une fois le `listWit` du document connu. |
| Choix de structure « phrase-chiffre » (`@n` décimal `441.1`, `441.2`...) pour les vers partagés en cascade | `fixtures/shared_verse/thebaide_2_2/expected.xml` (`l n="441.1"`, `n="441.2"`...) | Convention de *numérotation éditoriale* propre à l'édition Racine source d'ekdosis, pas une règle TEI ni une exigence de la roadmap : la commande « Marquer un vers partagé » de TIGRE demande le `@n` à l'utilisateur en texte libre (par défaut le `@n` déjà présent sur le vers scindé), sans imposer de convention de numérotation décimale. |
| Code Python (Tkinter/Flask, moteur pseudo-Markdown→TEI, générateurs HTML/LaTeX) | Tout le dépôt hors `fixtures/*/expected*.xml` | Hors sujet par construction (consigne de la tâche) : architecture radicalement différente de TIGRE, aucune ligne reprise. |

## Limitation signalée : `listWit` non structurée dans l'assistant d'en-tête

L'onglet « Source » de l'assistant d'en-tête (`header_dialog/tab_edition_source.py`,
phase 6) gère `sourceDesc` en mode `bibl` texte libre ou `msDesc` minimal, pas
de troisième mode « Témoins (`listWit`) » structuré. Confirmé par lecture du
fichier : pas de widget de saisie liste témoins/`xml:id`/description. Ajouter
ce troisième mode (table éditable `xml:id` + description, générant
`listWit`/`witness[@xml:id]`) est faisable sur le même patron que les deux
modes existants, mais n'a pas été fait dans cette phase par manque de temps
face au reste du périmètre (4 profils à vérifier, 4 commandes composites, le
test de bout en bout). Le critère d'acceptation central de la phase (acte de
théâtre + page d'apparat construits aux seuls outils graphiques, valides)
reste satisfait sans cette extension : le `listWit` du test de bout en bout
est construit avec les opérations génériques existantes (dégrouper/insérer/
attribut `xml:id`), pas avec l'assistant d'en-tête. Piste documentée ici pour
une phase ultérieure plutôt que tranchée silencieusement (`CLAUDE.md`).
