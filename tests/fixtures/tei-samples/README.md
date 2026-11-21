# Échantillons TEI pour l'éditeur graphique

Corpus de test et de démonstration pour le projet d'éditeur TEI autonome : 16 documents valides
et 5 cas invalides, répartis par thème. Chaque fichier commence par un commentaire qui indique
le module visé, ce qu'il faut tester dans l'éditeur, et ce qui est fictif.

## Contenu

| Dossier | Thème | Fichiers | Utile pour (phase de la feuille de route) |
|---|---|---|---|
| `01-structure` | Squelette, front/body/back, div typées | 2 | 3 (création de document, plan), 4 |
| `02-entete` | `teiHeader` complet | 1 | 6 (assistant d'en-tête : relecture sans perte) |
| `03-prose` | Prose, phrastique, notes, listes, tableau, figure | 1 | 5 (enveloppement, palette) |
| `04-poesie` | Strophes, vers, rimes | 1 | 7 |
| `05-theatre` | Vers et prose, vers partagés, didascalies | 2 | 7 (profil « Théâtre ») |
| `06-sources-primaires` | Transcription : `choice`, `supplied`, `gap`, `fw`… | 1 | 7 (profil « Édition de textes ») |
| `07-genetique` | Genèse du texte, 4 niveaux (+ `00-LISEZ-MOI.md`) | 4 | 7 (palette « Genèse ») |
| `08-edition-critique` | Apparat (`app`/`lem`/`rdg`, `rdgGrp`) | 2 | 7 (profil « Édition critique ») |
| `09-entites-dates` | Noms, lieux, dates, index | 1 | 5 (inspecteur, complétion de `@ref`) |
| `10-correspondance` | Lettre, `correspDesc` | 1 | corpus épistolaires |
| `99-invalides` | Mal formé, id dupliqué, référence cassée, hors modèle, en-tête incomplet | 5 | 4 (panneau de problèmes) |

`manifest.json` indexe tout (module, profil suggéré, éléments utilisés, erreurs attendues pour les
cas invalides) : un test automatique peut le parcourir sans connaître les noms de fichiers.

## Inspiration et provenance

- **TEI by Example** : seule la **typologie** des modules a été reprise (structure commune, en-tête,
  prose, poésie, théâtre, sources primaires, édition critique). Les exemples sont **originaux** ;
  rien n'est copié du site.
- **TCW19 (groupe « éditions génétiques », état de brouillon)** : les gestes essentiels ont été
  dégagés (ajout, suppression, substitution, mains, stades, métamarques, transposition,
  annulation) et **ramenés aux noms de la TEI P5 courante**, vérifiés dans les spécifications
  (`TEIC/TEI`, branche `dev`, 4 novembre 2026). Les éléments préfixés `ge:` du brouillon ne sont
  donc pas utilisés. Voir `07-genetique/00-LISEZ-MOI.md`.
- Textes : inventés, sauf l'extrait de La Fontaine (domaine public). Aucune donnée personnelle.
- Licence : à choisir par toi. Je suggère CC0 pour un corpus de test destiné à circuler librement.

## Contrôle automatique

```
python3 tools/check_samples.py        # nécessite lxml
```

Vérifie, pour chaque fichier : bonne formation, noms d'éléments et d'attributs connus de la P5
(`tools/p5_catalog_min.json`, 589 éléments), unicité des `xml:id`, résolution des références
`#id` ; et compare avec les erreurs attendues du manifeste. État actuel : **21/21 conformes**.
`tools/build_min_catalog.py` régénère le catalogue minimal depuis les spécifications P5, et
`tools/make_manifest.py` le manifeste. Ces deux scripts sont une amorce de l'étape A1 de la phase 1.

## Limites (à lire)

- **Les modèles de contenu ne sont pas contrôlés** (ordre et imbrication des éléments : un `head`
  tardif, un `p` dans un `p`). Je n'ai pas pu obtenir un schéma RelaxNG de la P5 courante : le
  `tei_all.rng` disponible dans le dépôt TEIC est une copie de 2009, inutilisable ; le schéma à jour
  se compile depuis l'ODD. Les échantillons respectent les modèles d'après les spécifications, mais
  **tu dois les valider une fois dans Oxygen ou avec un `tei_all.rng` récent** avant de les figer.
  Les deux cas « hors modèle » du dossier `99-invalides` ne sont détectables qu'à ce stade.
- Les valeurs d'attributs (dates, énumérations) ne sont pas vérifiées.
- Corpus volontairement petit : couvrir le noyau, pas la TEI entière.
