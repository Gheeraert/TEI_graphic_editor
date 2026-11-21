# Corpus de non-régression

Ce document décrit comment le projet utilise `tests/fixtures/tei-samples/` comme corpus de
non-régression (phase 9, `docs/ROADMAP.md` §5) et comment y ajouter un document TEI réel sans
toucher au code.

## Le corpus

`tests/fixtures/tei-samples/` contient 21 documents TEI répartis par thème dans des sous-dossiers
(`01-structure`, `02-entete`, `03-prose`, `04-poesie`, `05-theatre`, `06-sources-primaires`,
`07-genetique`, `08-edition-critique`, `09-entites-dates`, `10-correspondance`, `99-invalides`) :
16 documents valides et 5 cas invalides construits exprès (mal formé, `xml:id` dupliqué, référence
cassée, hors modèle de contenu, en-tête incomplet). Voir `tests/fixtures/tei-samples/README.md` pour
la provenance (TEI by Example pour la typologie des modules, TCW19 pour les gestes de l'édition
génétique — rien de copié, seulement l'inspiration, cf. ce README).

`tests/fixtures/tei-samples/manifest.json` indexe chaque fichier (chemin, module, profil suggéré,
éléments attendus, et pour les cas invalides la ou les erreurs attendues) : **toutes** les suites de
tests qui exploitent ce corpus le parcourent *via* ce manifeste, jamais par un listage direct du
dossier. C'est le fait à retenir avant de modifier le corpus (voir « Risque identifié » plus bas).

## Qui utilise ce corpus, et pourquoi

| Suite | Ce qu'elle vérifie sur le corpus |
|---|---|
| `tests/test_tei_samples_corpus.py` | Intégrité du manifeste lui-même (chaque entrée pointe vers un fichier qui existe, et réciproquement — voir plus bas) ; que chaque document valide analysé contient bien les éléments listés dans son entrée ; que les 3 premiers cas invalides (`01-mal-forme`, `02-xml-id-duplique`, `03-reference-cassee`) sont effectivement rejetés ou effectivement dangling dès l'analyse XML durcie (`tei_editor.tei.xml_safety`), sans attendre la validation RelaxNG de la phase 4. |
| `tests/test_roundtrip.py` | Fidélité **octet à octet** : ouvrir un document du corpus, l'enregistrer sans modification, comparer les octets du fichier produit à ceux du fichier d'origine (ADR-0001 : la source de vérité est le texte, jamais un modèle objet resérialisé). Le critère d'acceptation central de la phase 3. |
| `tests/test_diagnostics.py` | Validation RelaxNG contre le schéma unique `tei_all` (`05-theatre/01-scene-vers.xml` pour les avertissements « hors profil », `99-invalides/04-hors-modele.xml` et `05-en-tete-incomplet.xml` pour les deux cas qui ne sont détectables **qu'à ce stade**, cf. le README du corpus) ; contrôle des références croisées (`99-invalides/03-reference-cassee.xml`). |
| `tests/test_header_reader.py` / `tests/test_header_writer.py` | Lecture et réécriture sans perte d'un `teiHeader` réel (`02-entete/01-entete-complet.xml`) : relecture tolérante, localisation exacte des sous-éléments gérés, non-perte des parties non gérées (`seriesStmt`, `notesStmt`...) après une modification ciblée. |
| `tests/test_phase7_end_to_end.py` | Construction d'un acte de théâtre et d'une page d'édition critique **avec les seuls outils graphiques** (opérations génériques phase 5 + commandes composites phase 7), puis validation du résultat contre `tei_all.rng` — critère d'acceptation central de la phase 7. |

Les cas invalides ne sont pas un détail : ils garantissent que l'éditeur **refuse** les documents
qu'il doit refuser, pas seulement qu'il accepte ceux qu'il doit accepter (principe « refuser avant
toute mutation plutôt que corrompre silencieusement », `docs/ROADMAP.md` §4).

## Ajouter un document TEI réel au corpus

Pas besoin de toucher au code Python. Trois étapes :

1. **Déposer le fichier** dans le sous-dossier thématique le plus proche (ou en créer un nouveau,
   numéroté à la suite des existants, ex. `11-mon-corpus/01-mon-document.xml`). Le fichier doit être
   un document TEI bien formé, encodé en UTF-8 ; pas besoin qu'il soit déjà valide RelaxNG si
   l'intention est justement de tester un cas invalide (voir le dossier `99-invalides` pour le
   format attendu dans ce cas).
2. **Ajouter une entrée dans `manifest.json`** (`"files"` est une liste simple, l'ordre n'a pas
   d'importance) avec au moins ces champs :
   - `"file"` : chemin relatif à `tests/fixtures/tei-samples/` (ex. `"11-mon-corpus/01-mon-document.xml"`).
   - `"module"` : un intitulé libre (sert seulement à l'humain qui relit le manifeste).
   - `"profile"` : le profil suggéré (`"tous"`, `"edition_textes"`, `"theatre"`, `"edition_critique"`,
     ou `"test"` pour un cas invalide).
   - `"description"` : une phrase qui explique ce que le document illustre.
   - `"elements"` : la liste des noms d'éléments locaux (sans préfixe de namespace) que le document
     est censé contenir — **pour un document valide**, un test (`test_valid_sample_parses_and_contains_expected_elements`)
     vérifie que chacun de ces noms apparaît bien dans l'arbre une fois analysé. Une liste vide est
     acceptée mais n'apporte alors aucune vérification de contenu.
   - Pour un cas volontairement invalide, ajouter `"expect"` (liste parmi `"not-wellformed"`,
     `"duplicate-id"`, `"unresolved-ref"` — détectables dès l'analyse XML durcie) et/ou
     `"expect_rng"` (erreurs détectables seulement par la validation RelaxNG de la phase 4, ex.
     `"content-model"`, `"datatype"`) ; laisser `"elements"` à `[]` si non pertinent.
3. **Lancer la suite de tests** (`QT_QPA_PLATFORM=offscreen pytest -q`). Le nouveau fichier est alors
   automatiquement repris par `test_manifest_references_existing_files`,
   `test_every_xml_file_on_disk_has_a_manifest_entry`, et par le test paramétré
   `test_valid_sample_parses_and_contains_expected_elements` (ou, pour un cas invalide, par le test
   correspondant à son `"expect"`). Aucune autre modification de code n'est nécessaire : ces tests
   lisent le manifeste à la collecte, pas une liste de fichiers codée en dur.

`tests/test_roundtrip.py` lit lui aussi directement le manifeste et ne filtre que sur `"expect"`
(pas sur `"expect_rng"`) : toute entrée sans `"expect"` — y compris les deux cas invalides
détectables seulement par RelaxNG (`04-hors-modele`, `05-en-tete-incomplet`, qui portent
`"expect_rng"` mais pas `"expect"`) — est donc automatiquement incluse dans le test de round-trip
octet à octet dès son ajout au manifeste, sans action supplémentaire.

## Risque identifié et corrigé

Avant cette phase, `test_manifest_references_existing_files` vérifiait déjà qu'une entrée du
manifeste pointe vers un fichier qui existe réellement sur le disque — mais **rien ne vérifiait le
sens inverse**. Comme toutes les suites listées ci-dessus parcourent le corpus *via* le manifeste
(jamais par un listage direct du dossier), un fichier `.xml` déposé dans
`tests/fixtures/tei-samples/` sans entrée de manifeste correspondante aurait été silencieusement
ignoré par **toute** la suite de tests : ni bonne formation, ni validation RelaxNG, ni round-trip, ni
rien — un risque d'échec silencieux exactement du type que cette phase demande de repérer.

Corrigé par un nouveau test, `test_every_xml_file_on_disk_has_a_manifest_entry`
(`tests/test_tei_samples_corpus.py`) : il parcourt réellement le dossier (`rglob("*.xml")`) et échoue
avec la liste des fichiers orphelins si l'un d'eux n'a pas d'entrée dans `manifest.json`. Toute
étape 1 de la recette ci-dessus oubliant l'étape 2 fait donc désormais échouer la suite de tests de
façon explicite, au lieu de laisser le nouveau document traverser le projet sans jamais être
vérifié.
