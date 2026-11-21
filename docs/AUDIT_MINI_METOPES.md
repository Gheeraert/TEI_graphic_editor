# Audit de C:\mini-metopes pour la phase 6 (assistant d'en-tête TEI)

**Statut.** Consultation en lecture seule, autorisée explicitement par l'utilisateur pour cette
phase. Dépôt source : `C:\mini-metopes`, HEAD `ba590fc16abad97ec4d8c117308863fcf90859cc`
(2026-08-06). Aucun fichier de ce dépôt n'a été modifié, créé ou supprimé : seules des lectures
(`Read`/`git log` sans écriture) ont été effectuées. Même format que `docs/AUDIT_MEROPE.md` : ce
qui a été regardé, ce qui a inspiré quoi, ce qui n'a pas été repris et pourquoi.

## Ce qui a été consulté

1. `src/mini_metopes/metadata/model.py` (dataclasses `Contributor`, `Affiliation`,
   `EditorialResponsibility`, `Publisher`, `Publication`, `Identifier`, `License`, `Rights`,
   `Abstract`, `KeywordGroup`, `Collection`, `Funding`, `DocumentMetadata`, etc.)
2. `src/mini_metopes/tei/serializer.py`, fonctions `_append_header` (~l. 284),
   `_append_publication_statement` (~l. 420), `_append_bibliographic_source_desc` (~l. 503),
   et les fonctions voisines `_tei_identifier`, `_availability_content`, `_affiliation_text`.
3. Survol de `metadata/serialization.py` et `editorial/serialization.py` (lecture rapide, pour
   confirmer qu'ils sont couplés au DOCX et au pivot `Block`/`InlineRun`, hors sujet ici).

## Ce qui a inspiré quoi

- **Modèle multi-contributeurs avec rôles et affiliations.** `Contributor` (identifiant, rôle
  fermé, nom décomposé prénom/nom ou nom littéral, ORCID, affiliations multiples par identifiant)
  a inspiré la forme générale de `tei_editor.tei.header_model.ResponsibleParty` : une liste ouverte
  de responsables, chacun avec un rôle, un nom, et des champs optionnels (ORCID, affiliation en
  texte libre). La distinction `given_name`/`family_name` vs `literal_name` a été reprise comme
  principe (un nom peut être saisi décomposé ou tel quel) sans reprendre le type `Contributor`
  lui-même : le vocabulaire TEI (`respStmt`/`resp`/`name`, `author`, `editor`) est fondamentalement
  différent de celui, pensé pour du DOCX, de mini-metopes (`role_label` libre + `role` fermé sur 5
  valeurs qui ne couvrent pas `funder`/`sponsor` ni un `resp` TEI totalement libre).
- **Affiliations comme registre réutilisable (`Affiliation` + `affiliation_ids`).** Idée retenue en
  principe (une affiliation est un texte attaché à un responsable) mais *simplifiée* : la phase 6
  ne construit pas de registre séparé avec identifiants et ROR — un champ texte libre `affiliation`
  par responsable suffit au périmètre demandé (« texte libre » explicitement accepté par la
  consigne pour `profileDesc`/`encodingDesc`, et ici appliqué par cohérence à ce sous-champ
  secondaire de `ResponsibleParty`). Pas de `ror`/`city`/`country` structurés.
- **`publicationStmt` : ordre éditeur → lieu → date → identifiants → disponibilité/licence.**
  `_append_publication_statement` construit cet ordre précis (`publisher`, puis `pubPlace`/adresse,
  puis `date`, puis `idno`, puis `availability`/`licence`). `header_writer.py` reproduit le même
  ordre de sous-éléments pour `publicationStmt` — c'est une référence de forme utile (quel enfant
  TEI dans quel ordre), pas du code copié : la fonction mini-metopes est couplée à
  `DocumentMetadata`/`_SerializationState`/diagnostics de conversion DOCX→TEI qui n'ont pas
  d'équivalent ici.
- **Résolution de licence.** `resolved_license(metadata.rights.license)` confirme le même principe
  déjà extrait en phase 2 dans `tei_editor.tei.licenses` (identifiant SPDX → nom/URL canoniques,
  sinon champs libres) : aucune ré-extraction nécessaire, la phase 6 réutilise directement
  `tei_editor.tei.licenses.resolve_license` comme demandé par la consigne.
- **`sourceDesc` minimal avec `bibl`.** `_append_bibliographic_source_desc` ne construit qu'un
  `bibl` simple (série, pagination) — conforme au choix, pris indépendamment pour cette phase, de
  garder `tei_editor.tei.header_model.SourceDescription` simple (soit un `bibl` texte libre, soit
  un `msDesc` minimal à 2-3 champs), un `msDesc` complet étant explicitement hors de portée.
- **`respStmt` multiples et rôles non capturés par `author`/`editor`.** La boucle
  `for contributor_index, contributor in enumerate(...)` qui émet un `<author>`/`<editor>` par
  contributeur, plus un `<funder>` séparé pour chaque financement, a confirmé le choix de modéliser
  les responsabilités de `titleStmt` comme une liste hétérogène de `ResponsibleParty` typés par
  rôle TEI (`author`, `editor`, `funder`, ou `respStmt` générique avec un libellé `resp` libre),
  plutôt qu'un seul rôle fermé sur 5 valeurs.

## Ce qui n'a pas été repris, et pourquoi

- **Les types `Contributor`/`Affiliation`/`DocumentMetadata` eux-mêmes** : conçus pour des
  métadonnées de DOCX à sérialiser *à sens unique* vers un profil TEI fixe (Commons Publishing),
  pas pour relire un `teiHeader` TEI quelconque. Le vocabulaire de champs (`role_label`,
  `contributor_id`, `affiliation_ids` en tuple d'identifiants) n'a pas d'équivalent naturel côté
  lecture d'un `respStmt`/`author`/`editor` TEI existant.
- **`_append_header`/`_append_publication_statement`/`_append_bibliographic_source_desc`
  elles-mêmes** : étroitement couplées à `_SerializationState` (diagnostics de conversion),
  `metadata.publication.publisher` etc. Aucune ligne n'a été copiée ; ces fonctions ne résolvent de
  toute façon pas le problème central de cette phase — elles *génèrent* un `teiHeader` neuf, elles
  ne relisent jamais un en-tête existant pour en préserver les parties non gérées. C'est exactement
  l'inverse du problème posé par `header_reader.py`/`header_writer.py` (ADR-0001 : agir sur des
  plages de texte précises d'un document déjà là, jamais une ré-sérialisation complète).
- **`EditorialResponsibility`** (suivi éditorial distinct des auteurs) : signalée par mini-metopes
  elle-même comme non sérialisable dans son profil embarqué (`editorial_responsibility_not_serialized`).
  Pas reprise : `ResponsibleParty` avec un rôle `respStmt` générique couvre déjà ce cas en TEI natif.
- **`normalize_orcid`/`normalize_doi`/`normalize_isbn`/`normalize_issn`** : utilitaires de
  normalisation de chaînes, indépendants du problème de relecture/écriture chirurgicale ; hors
  périmètre de cette phase (pas de validation poussée des identifiants demandée par la consigne).
- **`metadata/serialization.py`, `editorial/serialization.py`** : survolés, confirmés couplés au
  pivot DOCX (`Block`/`InlineRun`, lecture d'un `.docx` via `python-docx`) — aucun rapport avec la
  relecture d'un `teiHeader` XML existant, donc pas creusés davantage.

## Conclusion

Aucun extrait de code de mini-metopes n'a été repris verbatim dans `tei_editor` — l'attente
annoncée par la consigne (« inspiré de », pas « repris de ») s'est confirmée. L'inspiration retenue
porte uniquement sur la *forme* du modèle de données (responsables multiples typés par rôle,
affiliation en texte libre) et sur l'*ordre* de sérialisation de `publicationStmt`, tous deux
adaptés au vocabulaire TEI natif et au problème de relecture/préservation propre à cette phase, que
mini-metopes ne traite pas.
