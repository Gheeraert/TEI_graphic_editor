# Règles d'encodage TEI P5

> Document de référence pour l'encodage dans cet éditeur. Il explicite les
> neuf règles listées en principe dans `docs/ROADMAP.md` §3.A3, et précise,
> pour chacune, ce que l'application pourra vérifier automatiquement (phases
> 4 et 5 de la feuille de route) et ce qui restera affaire de convention
> éditoriale, signalée par un avertissement plutôt qu'une erreur.
>
> **Version TEI de référence.** Ces règles s'appuient sur, et le catalogue
> des balises (`src/tei_editor/data/tei_catalog.json`) est généré depuis,
> **TEI P5 version 4.12.0** (fichier ODD officiel
> `https://www.tei-c.org/Vault/P5/4.12.0/xml/tei/odd/p5subset.xml`, publié
> par le consortium TEI). Voir `tools/build_catalog.py` pour le script de
> génération et `docs/DECISIONS.md` (ADR-0003) pour les choix et limites de
> cette génération.

## Principe général : suggérer, puis valider

Cet éditeur suit le principe posé dans `docs/DECISIONS.md` (ADR-0001) et
repris dans `docs/ROADMAP.md` (phase 5) : **suggérer de façon permissive,
valider de façon stricte**. Le catalogue généré (enfants/parents
approximatifs, attributs résolus par classe) alimente l'aide à la saisie —
palette de balises, complétion — mais ne décide jamais, seul, qu'un document
est valide. La décision de validité appartient :

- à l'analyseur XML (`lxml`/`libxml2`) pour la bonne formation (règle 1) ;
- au schéma RelaxNG du profil actif pour les modèles de contenu (règle 3) ;
- à des contrôles dédiés, écrits dans l'application, pour les références
  croisées (règle 5) et certains types de données (règle 6) ;
- à l'éditeur humain, assisté d'avertissements non bloquants, pour les
  conventions d'encodage (règle 7).

---

## 1. Bonne formation et espace de noms

Un document TEI valide dans cet éditeur est d'abord un document **XML 1.0
bien formé** : une déclaration XML cohérente avec l'encodage réel du fichier
(UTF-8 par défaut, sans BOM), un seul élément racine, des balises toutes
fermées et correctement imbriquées, des attributs sans doublon sur un même
élément. L'élément racine `<TEI>` doit porter (ou hériter par défaut dans le
document) l'espace de noms `http://www.tei-c.org/ns/1.0` : un document TEI
sans cet espace de noms, ou avec un préfixe non déclaré, n'est pas reconnu
comme TEI P5 par les outils standard (RelaxNG compilé pour cet espace de
noms, XPath par défaut, etc.).

**Vérification automatique.** Totale et immédiate : c'est le rôle même d'un
analyseur XML. Toute opération de chargement ou d'enregistrement passe par
une analyse durcie (voir `CLAUDE.md`, « analyse XML durcie ») qui refuse un
document mal formé plutôt que de tenter de le corriger silencieusement — à
l'image de la discipline reprise de Mérope (« refuser avant toute mutation
plutôt que corrompre silencieusement », `docs/ROADMAP.md` §4). L'absence du
bon espace de noms sur la racine est détectable par une simple inspection de
l'arbre analysé.

## 2. Squelette minimal d'un document TEI

Un document TEI éditable doit respecter une architecture minimale, même
avant d'être complet :

- `<TEI>` contient un `<teiHeader>` suivi d'au moins un élément de contenu
  (`<text>`, ou `<facsimile>` pour une édition essentiellement en fac-similé,
  ou un `<teiCorpus>` de plusieurs `<TEI>`) ;
- `<fileDesc>`, bloc obligatoire de l'en-tête, contient au minimum un
  `<titleStmt>` (avec au moins un `<title>`), un `<publicationStmt>` et un
  `<sourceDesc>` ;
- `<text>` contient un `<body>` (ou un `<group>` de plusieurs textes), avec
  en option un `<front>` avant et un `<back>` après, dans cet ordre.

**Vérification automatique.** Partielle. La présence et l'ordre relatif de
ces blocs sont en réalité des cas particuliers du modèle de contenu général
(règle 3) et seront donc couverts par la validation RelaxNG du profil actif.
L'assistant d'en-tête (phase 6 de la feuille de route) ira plus loin : il
pourra refuser de fermer son dialogue tant que ce squelette minimal n'est
pas rempli, et proposer des modèles de document déjà conformes (minimal
valide, édition critique, théâtre, correspondance).

## 3. Modèles de contenu

L'ordre et la combinaison exacts des éléments enfants d'un élément donné
(p. ex. : un `<div>` commence-t-il par un `<head>` ? un `<l>` peut-il
apparaître directement dans un `<sp>`, ou seulement regroupé dans un
`<lg>` ? un `<lem>`/`<rdg>` sont-ils bien des enfants directs de `<app>` ?)
ne sont **jamais recodés à la main** dans l'application. Cette règle découle
directement du principe : « le catalogue TEI fait foi » (`CLAUDE.md`).

**Vérification automatique.** C'est la validation forte de ce document :
elle est déléguée à un schéma **RelaxNG** officiel, correspondant au profil
actif (phase 4 de la feuille de route). Le catalogue généré par
`tools/build_catalog.py` fournit, lui, des listes d'enfants et de parents
**approximatives** (`children_approx`/`parents_approx` dans
`tei_catalog.json`) : elles servent à proposer des balises dans la palette
(« voici ce qu'on insère *typiquement* ici »), pas à décider qu'une
insertion est valide. Voir `docs/DECISIONS.md` (ADR-0003) pour le détail de
cette approximation et ses limites (pas d'interprétation des cardinalités
ni des alternatives exclusives du modèle de contenu compilé).

Exemples de cas qui devront être couverts par les tests de la validation
RelaxNG, une fois celle-ci en place : `<head>` en tête de `<div>` ;
`<l>` valide dans `<lg>` ou `<sp>` ; `<sp>` avec `<speaker>` ; `<lem>`/`<rdg>`
dans `<app>`.

## 4. Attributs globaux

Un grand nombre d'attributs ne sont pas propres à un élément particulier
mais disponibles (presque) partout, via les classes d'attributs globales de
TEI (`att.global` et ses sous-classes) : `@xml:id`, `@xml:lang`, `@n`,
`@rend`, `@style`, `@type`/`@subtype`, `@resp`, `@cert`, `@source`,
`@corresp`, `@sameAs`, `@next`/`@prev`, `@facs`. Le catalogue généré les
résout par héritage de classe (voir `docs/DECISIONS.md`, ADR-0003) plutôt
que de les lister en dur pour chaque élément : chaque attribut résolu porte
un champ `source` indiquant s'il est propre à l'élément ou hérité d'une
classe nommée.

**Vérification automatique.** Partielle, et de nature différente selon
l'attribut :

- `@xml:id` doit être un `NCName` valide (syntaxe vérifiable par une simple
  expression régulière) et **unique dans tout le document** — ce dernier
  point n'est pas une contrainte RelaxNG locale mais un contrôle global, que
  l'application devra faire elle-même (index des identifiants, mis à jour en
  différé avec le reste du modèle structurel dérivé, voir ADR-0001).
- `@xml:lang` doit être une étiquette de langue BCP 47 valide. Une
  vérification de forme (syntaxe BCP 47) est automatisable ; une vérification
  de pertinence (« cette langue existe-t-elle vraiment, est-elle cohérente
  avec `<langUsage>` dans l'en-tête ? ») relève de l'inspecteur d'attributs
  assisté (phase 5), pas d'une validation bloquante.
- Les autres attributs globaux suivent les règles génériques de type de
  données (règle 6) ou de référence croisée (règle 5) selon leur nature.

## 5. Références internes

Toute valeur de la forme `#id` portée par un attribut de référence
(`@target`, `@ref`, `@corresp`, `@resp`, `@who`, `@wit`, `@facs`, etc.) doit
pointer vers un `@xml:id` effectivement présent ailleurs dans le document (ou,
pour certains attributs, dans un document externe référencé — hors périmètre
v1 de ce contrôle).

**Vérification automatique.** Oui, par un contrôle croisé dédié : une fois
l'index des `@xml:id` du document construit (voir règle 4), il suffit de
résoudre chaque valeur `#id` rencontrée dans un attribut de référence et de
signaler celles qui ne trouvent pas de cible. Ce contrôle est prévu dans le
panneau « Problèmes » (phase 4) et dans la complétion de l'inspecteur
d'attributs, qui pourra proposer la liste des `@xml:id` existants au moment
de la saisie (phase 5) plutôt que de laisser l'utilisateur taper une
référence invalide puis la corriger.

## 6. Types de données

Certains attributs ont un type de données structuré, au-delà de la simple
chaîne de caractères : dates au format ISO 8601 / W3C (`@when`,
`@notBefore`, `@notAfter`, `@from`, `@to`), URI, entiers, ou énumérations
fermées lorsque le schéma en définit une (p. ex. `@status` sur
`<availability>`, avec les valeurs `free`, `restricted`, `unknown`…). Le
catalogue généré capture ces contraintes : le type de donnée déclaré
(`datatype`, en pratique une macro `teidata.*` du schéma TEI) et, le cas
échéant, la liste fermée de valeurs admises (`closed_values`) pour chaque
attribut.

**Vérification automatique.** Oui, en grande partie, et sans attendre la
validation RelaxNG complète : le type de donnée et les valeurs fermées sont
déjà présents dans le catalogue, donc exploitables dès l'inspecteur
d'attributs typé prévu en phase 5 (sélecteur de date, liste déroulante pour
une énumération fermée, etc.), avant même qu'un document existant ne soit
revalidé par le schéma.

## 7. Conventions d'encodage (avertissements, pas des erreurs)

Cette règle est d'une autre nature que les six précédentes : elle ne relève
pas de la validité XML ou RelaxNG, mais d'un choix éditorial que le schéma
TEI, par construction, **autorise aussi bien dans le mauvais sens que dans
le bon**. Quatre conventions, en particulier :

1. **Encoder la sémantique plutôt que l'apparence.** TEI permet d'encoder
   une mise en forme avec `<hi rend="italic">`, qui dit seulement « ce texte
   est rendu différemment, en italique » sans en préciser la raison. Quand
   la raison est connue, un élément sémantique est préférable :
   `<emph>` (insistance), `<title>` (titre d'œuvre), `<foreign>` (mot
   étranger), `<mentioned>` (mot mentionné en tant que mot), `<soCalled>`
   (« ainsi dit »)... `<hi>` reste légitime quand la mise en forme ne
   correspond à aucune catégorie sémantique identifiable, ou pour une
   transcription qui privilégie délibérément la fidélité graphique. L'attribut
   `@rend` sert, lui, à noter *comment* une forme sémantique est rendue
   typographiquement (p. ex. `<title rend="italic">`), sans se substituer au
   choix sémantique.
2. **`<lb>`/`<pb>` pour les sauts physiques.** Les sauts de ligne et de page
   d'un témoin sont des éléments vides (`<lb/>`, `<pb/>`), pas des retours à
   la ligne dans le texte XML lui-même (voir règle 8). Quand un saut de ligne
   coupe un mot, `@break="no"` indique que le mot continue sur la ligne
   suivante sans espace ni trait d'union réel.
3. **`<choice>` pour grouper une paire éditeur/source.** Les couples
   `orig`/`reg` (graphie originale / régularisée), `sic`/`corr` (texte tel
   quel / corrigé), `abbr`/`expan` (abréviation / développée) doivent être
   regroupés sous `<choice>`, qui permet de restituer, au choix, la forme
   diplomatique ou la forme normalisée, sans dupliquer le texte ni perdre
   l'une des deux lectures.
4. **Déclarer les choix éditoriaux dans `<editorialDecl>`.** Toute convention
   systématique adoptée pour un projet (p. ex. : toujours régulariser telle
   graphie, toujours résoudre telles abréviations) doit être documentée en
   prose dans `<editorialDecl>` de l'en-tête, pour qu'un lecteur du XML seul
   comprenne la politique d'édition suivie — et pas seulement la trace de
   chaque décision individuelle dans le texte.

**Vérification automatique.** Non, par nature : choisir entre `<hi>` et
`<emph>` relève d'une lecture du sens, pas d'une règle de grammaire. Cette
application ne transformera donc jamais silencieusement un `<hi>` en
`<emph>`. Ce qu'elle pourra faire, en revanche (phase 5 et au-delà), c'est
**signaler** des motifs suspects à titre d'avertissement non bloquant — par
exemple un grand nombre de `<hi rend="italic">` sans aucun `<foreign>` ni
`<title>` dans tout le document, ou un `orig`/`reg` non enveloppé dans
`<choice>` — pour attirer l'attention de l'éditeur sans jamais l'empêcher
d'enregistrer son travail. C'est la même distinction que celle posée pour le
panneau « Problèmes » (phase 4) entre erreurs (bloquantes, de la bonne
formation à la validation RelaxNG) et avertissements (informatifs, pour les
conventions).

## 8. Contenu mixte

Le texte XML est la source de vérité du document (ADR-0001). Dans un élément
à contenu mixte (texte et balises entremêlés, ce qui concerne la plupart des
éléments de niveau phrastique et de structure du texte), **aucune opération
de balisage ne doit insérer ni retirer un espace ou un retour à la ligne qui
n'était pas déjà dans le texte d'origine**. Une opération d'enveloppement de
sélection, de renommage ou de scission de balise doit déplacer exactement
les caractères visés, ni plus ni moins. Pour la même raison, **l'indentation
automatique est désactivée** dans ces éléments : une ré-indentation
« pretty-print » du XML modifierait silencieusement un contenu mixte dont les
espaces sont porteurs de sens.

**Vérification automatique.** Indirecte, mais déterminante : c'est le test
de **round-trip octet à octet** prévu comme critère d'acceptation de la
phase 3 (ouvrir, modifier, enregistrer un document existant sans aucune
altération non voulue) qui garantit cette règle, plutôt qu'une règle de
validation isolée. Toute régression sur ce point doit être détectée par ce
test de non-régression, pas découverte après coup sur un corpus réel.

## 9. Caractères

L'encodage recommandé des caractères est la forme normalisée **NFC**
d'Unicode. Les espaces typographiques significatifs — espace insécable
(U+00A0) et espace fine insécable (U+202F, utilisée en français avant
certains signes de ponctuation double) — doivent être préservées telles
quelles dans le texte, jamais silencieusement remplacées par une espace
ordinaire. Un caractère qui n'a pas de représentation Unicode (signe
paléographique, abréviation graphique rare) relève de `<charDecl>`/`<g>`,
qui permet de le décrire et de le référencer de façon cohérente dans tout le
document plutôt que d'improviser une convention locale.

**Vérification automatique.** Partielle. La présence d'espaces insécables
peut être signalée (ou au contraire protégée) par un module de typographie
française à la frappe, s'il est repris de Mérope (`markdown/typography.py`,
voir `docs/ROADMAP.md` §4) et adapté pour n'agir que dans les nœuds texte —
jamais en dehors, pour ne pas violer la règle 8. La normalisation NFC peut
être vérifiée (et proposée en correction, jamais appliquée d'autorité) à
l'ouverture d'un document. Le bon usage de `<charDecl>`/`<g>` pour un
caractère hors Unicode reste, lui, une décision éditoriale au même titre que
la règle 7.

---

## Récapitulatif : automatisable / avertissement / hors périmètre v1

| # | Règle | Nature du contrôle |
|---|---|---|
| 1 | Bonne formation, espace de noms | Automatisable (bloquant), dès le chargement |
| 2 | Squelette minimal | Automatisable (bloquant), via la validation RelaxNG + assistant d'en-tête |
| 3 | Modèles de contenu | Automatisable (bloquant), via RelaxNG — jamais via les listes approximatives du catalogue |
| 4 | Attributs globaux | Mixte : syntaxe automatisable (bloquant) ; unicité de `@xml:id` automatisable (bloquant, contrôle applicatif dédié) ; pertinence de `@xml:lang` assistée (non bloquant) |
| 5 | Références internes | Automatisable (bloquant), contrôle croisé applicatif dédié |
| 6 | Types de données | Automatisable (bloquant pour la syntaxe, assisté pour la saisie) |
| 7 | Conventions d'encodage | **Non automatisable** : avertissement éditorial uniquement |
| 8 | Contenu mixte | Garanti par construction (round-trip), pas une règle de validation isolée |
| 9 | Caractères | Mixte : NFC vérifiable (non bloquant, proposé en correction) ; `charDecl`/`g` relève du choix éditorial |
