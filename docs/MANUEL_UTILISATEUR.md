# Manuel utilisateur de TIGRE (TEI Graphic Editor)

TIGRE est un éditeur de bureau pour le XML-TEI P5 : il **édite** du TEI avec l'aide d'une interface
graphique (palette de balises, inspecteur d'attributs, plan structurel, panneau de problèmes,
assistant d'en-tête), mais ne produit aucun rendu (pas d'aperçu HTML, pas d'export vers un autre
format). Ce manuel décrit l'application telle qu'elle existe aujourd'hui, à l'issue des neuf phases
de `docs/ROADMAP.md`.

**Principe à retenir** : le texte XML affiché dans la fenêtre principale est la seule source de
vérité. Toutes les aides graphiques (palette, inspecteur, plan, assistant d'en-tête) lisent ce texte
et le modifient par petites retouches ciblées — elles ne le reconstruisent jamais entièrement. C'est
ce qui garantit qu'ouvrir puis enregistrer un document sans y toucher ne change pas un seul octet.

## 1. Premiers pas

### Ouvrir un document existant

Menu **Fichier > Ouvrir...** (`Ctrl+O`), ou un fichier du menu **Fichier > Fichiers récents**. Le
filtre par défaut affiche les fichiers `.xml`/`.tei`, mais « Tous les fichiers » reste disponible. Si
le document a été modifié mais non enregistré, l'application demande confirmation avant d'écraser
l'état courant en ouvrant un autre fichier.

À l'ouverture, si un brouillon de récupération automatique existe pour ce fichier (ou pour un
document « Sans titre » resté ouvert), une boîte de dialogue propose de le restaurer.

### Créer un nouveau document

- **Fichier > Nouveau** (`Ctrl+N`) crée directement un document minimal valide (le squelette TEI
  obligatoire : `TEI` > `teiHeader` + `text`/`body`).
- **Fichier > Nouveau depuis un modèle** propose les 4 modèles de départ : **Minimal valide**,
  **Édition critique** (avec un `listWit` de deux témoins et un `app`/`lem`/`rdg` d'exemple),
  **Théâtre** (`castList`, un acte, une scène, une réplique) et **Correspondance** (`correspDesc`,
  `opener`/`closer`). Chaque modèle est une structure TEI valide contre le schéma, sans contenu
  réaliste : il sert à démarrer dans le bon profil, pas à fournir un texte déjà écrit.

### Enregistrer

**Fichier > Enregistrer** (`Ctrl+S`), **Enregistrer sous...** (`Ctrl+Shift+S`) pour choisir un
nouveau chemin, **Exporter une copie...** pour écrire une copie du texte courant ailleurs sans
changer le fichier actuellement ouvert ni son état « modifié ». L'écriture est atomique (le fichier
visible n'est jamais dans un état intermédiaire en cas d'interruption), l'encodage et la fin de ligne
d'origine (`\n` ou `\r\n`) sont préservés tels quels.

## 2. La fenêtre : menus et barres d'outils

La fenêtre principale a une barre de menus (**Fichier**, **Édition**, **Insertion**, **Balises**,
**Affichage**, **Outils**, **Aide**), quatre barres d'outils repositionnables (**Fichier**,
**Édition**, **Balises**, **Affichage**, chacune avec infobulles indiquant le raccourci), une zone
d'édition de texte XML avec coloration syntaxique, et une barre d'état en bas (position
ligne/colonne, chemin XPath de l'élément courant, profil actif, validité du document).

### Menu Fichier
Nouveau (`Ctrl+N`) ; Nouveau depuis un modèle (sous-menu, 4 entrées) ; Ouvrir... (`Ctrl+O`) ;
Fichiers récents ; Enregistrer (`Ctrl+S`) ; Enregistrer sous... (`Ctrl+Shift+S`) ; Exporter une
copie... ; Quitter (`Ctrl+Q`).

### Menu Édition
Annuler (`Ctrl+Z`) / Rétablir (`Ctrl+Shift+Z`) — natifs de la zone de texte, une opération graphique
structurée (envelopper, dégrouper, renommer...) se défait toujours en **un seul** « Annuler », même
si elle modifie plusieurs endroits du texte ; Couper/Copier/Coller (`Ctrl+X`/`Ctrl+C`/`Ctrl+V`) ;
Rechercher/remplacer... (`Ctrl+F`, avec expression régulière optionnelle et respect de la casse) ;
Aller à la ligne... (`Ctrl+G`).

### Menu Insertion
Reste un simple renvoi (« Palette de balises : voir le dock « Palette » (Affichage) ») : l'insertion
de balises se fait depuis le dock **Palette**, pas depuis ce menu.

### Menu Balises
Envelopper la sélection... (`Ctrl+E`), Dégrouper la balise, Renommer la balise..., Scinder le
paragraphe, Fusionner avec le paragraphe suivant, Générer un xml:id, puis un sous-menu **Jeux de
balises** avec les quatre commandes composites de la phase 7 (voir §5).

### Menu Affichage
Bascules des quatre docks (Plan, Inspecteur, Problèmes, Palette), sous-menu Zoom (avant/arrière/
réinitialiser, `Ctrl++`/`Ctrl+-`/`Ctrl+0`), sous-menu Thème (clair/sombre).

### Menu Outils
Valider (`F7`), sous-menu Profil actif (liste exclusive des 4 profils), Assistant d'en-tête...,
Préférences....

### Menu Aide
À propos de TIGRE.

## 3. Palette contextuelle et inspecteur d'attributs (phase 5)

### Dock Palette
Liste filtrable (champ de recherche en haut) et groupée des éléments TEI du profil actif. Les
éléments jugés pertinents pour la position actuelle du curseur sont mis en avant (étoile, gras, triés
en tête de leur groupe) — une **suggestion**, jamais une restriction : la recherche libre donne accès
à n'importe quel élément du catalogue, même hors suggestion. Double-cliquer (ou appuyer sur Entrée)
sur une entrée :
- si du texte est sélectionné dans l'éditeur : l'enveloppe dans l'élément choisi (`<élément>...
  </élément>`) sans toucher à un seul caractère de la sélection ni du reste du document ;
- sinon : insère l'élément à la position du curseur, en balise auto-fermante pour les éléments
  typiquement vides (`lb`, `pb`, `cb`, `gap`, `anchor`, `milestone`, `graphic`, `space`) ou avec ses
  deux balises (ouvrante/fermante, curseur placé entre les deux) pour les autres.

### Menu/barre d'outils Balises : opérations génériques
- **Envelopper la sélection...** (`Ctrl+E`) : demande le nom d'un élément et enveloppe la sélection
  (même résultat que la palette, en passant par une boîte de dialogue plutôt qu'une liste).
- **Dégrouper la balise** : retire les balises ouvrante/fermante de l'élément courant sans toucher à
  son contenu (désactivé sur un élément auto-fermant, qui n'a pas de contenu à libérer).
- **Renommer la balise...** : change uniquement le nom de l'élément courant (ouvrante et fermante),
  en conservant tous ses attributs tels quels.
- **Scinder le paragraphe** / **Fusionner avec le paragraphe suivant** : actives uniquement dans un
  `<p>`, au bon endroit (curseur à l'intérieur du contenu pour scinder ; `<p>` suivant immédiat pour
  fusionner).
- **Générer un xml:id** : désactivé si l'élément courant a déjà un `xml:id` ; sinon propose un
  identifiant garanti unique (`p-1`, `div-3`...) basé sur le nom de l'élément.

### Dock Inspecteur
Affiche les attributs de l'élément XML sur lequel se trouve le curseur : d'abord ceux déjà présents
(y compris un attribut inconnu du catalogue — jamais perdu), puis ceux que le catalogue TEI autorise
pour cet élément mais qui sont encore absents (proposables). L'éditeur présenté pour chaque attribut
dépend de son type déclaré dans le catalogue (liste fermée → menu déroulant, date, langue...) ; un
attribut de référence (`@ref`, etc.) propose en complétion les `xml:id` déjà présents dans le
document. Une valeur validée (`Entrée`/perte du focus) écrit directement l'attribut dans le texte ;
vider le champ retire l'attribut ; le bouton « ✖ » à côté d'un attribut présent le retire aussi. Un
bouton « Générer un xml:id » fait la même chose que l'action du menu Balises, désactivé si l'élément
en a déjà un.

### Dock Plan
Arborescence structurelle du document (titres, divisions...), synchronisée avec la position du
curseur ; cliquer sur une entrée déplace le curseur à la ligne correspondante.

## 4. Panneau Problèmes et validation (phase 4)

Le dock **Problèmes** liste, en continu (recalcul différé ~400 ms après chaque frappe), tous les
diagnostics du document courant :
- **Erreurs** (icône rouge ✖) : document mal formé (avec ligne/colonne précises), document invalide
  contre le schéma RelaxNG unique `tei_all` (message reformulé en français, sans jargon libxml2),
  référence interne non résolue (`@ref`/`@target`/`@wit`/`@corresp`/`@resp`/`@who`/`@facs="#id"` qui
  ne correspond à aucun `xml:id` du document).
- **Avertissements** (icône ocre ⚠), non bloquants : un élément présent dans le document mais absent
  de la liste blanche du **profil actif** (voir §5) — le document reste valide contre `tei_all`
  malgré l'avertissement, c'est seulement un signal que l'élément sort du profil choisi.

Double-cliquer sur une entrée déplace le curseur à l'endroit concerné. **Outils > Valider** (`F7`)
relance une vérification immédiate et affiche un résumé (document valide, ou décompte
erreurs/avertissements) sans attendre le prochain recalcul différé. La barre d'état affiche en
permanence l'état de validité (« Document valide », « Document invalide (schéma TEI) », « Document
mal formé ») et le chemin XPath de l'élément sous le curseur.

**Important** : le schéma RelaxNG de validation (`tei_all`) est **unique**, quel que soit le profil
actif — changer de profil ne change jamais ce qui est accepté ou refusé par **Valider**, seulement ce
qui apparaît dans la palette et ce qui déclenche un avertissement « hors profil ».

## 5. Profils, modèles et jeux de balises (phase 7)

### Profil actif
**Outils > Profil actif** propose 4 profils (liste exclusive) : **TEI (complet)** (aucune
restriction, aucun avertissement hors profil possible), **Édition de textes**, **Théâtre**,
**Édition critique**. Le profil choisi pilote la palette (quels éléments sont proposés, et dans
quels groupes) et les avertissements « hors profil » du panneau Problèmes ; il est mémorisé entre
deux lancements et affiché dans la barre d'état. Un profil personnalisé peut être ajouté comme
fichier JSON dans `src/tei_editor/data/profiles/` (format documenté dans `docs/PROFILS.md`) ; il
apparaît alors automatiquement dans ce sous-menu, sans aucune autre modification.

### Jeux de balises (sous-menu Balises > Jeux de balises)
Quatre commandes composites, chacune un seul pas d'annulation :
- **Grouper en choix…** : enveloppe la sélection (le texte tel qu'il apparaît, pas la forme
  normalisée) dans `<choice><premier>...</premier><second></second></choice>` ; une boîte de
  dialogue propose les trois paires définies dans `data/snippets/choice_pairs.json` (`orig`/`reg`,
  `sic`/`corr`, `abbr`/`expan`) — le second élément est inséré vide, à compléter ensuite.
- **Insérer une liste de personnages…** : demande un nombre de personnages et insère un squelette
  `<castList>` avec autant de `<castItem><role></role></castItem>`, curseur placé dans le premier
  `<role>` vide.
- **Marquer un vers partagé** : à utiliser avec le curseur à l'intérieur du texte d'un `<l>`, au
  point de partage entre deux répliques (`<sp>`) voisines. Scinde ce vers en deux fragments
  `@part="I"`/`@part="F"` portant le même `@n` (demandé dans une boîte de dialogue), convention
  standard `att.fragmentable` de la TEI ; le second fragment est inséré au début de la réplique
  suivante (après `<speaker>` si elle en a un).
- **Insérer une leçon (app/lem/rdg)…** : enveloppe la sélection (la leçon retenue) dans
  `<app><lem>...</lem><rdg></rdg>...</app>`, avec un nombre de `<rdg>` vides à choisir ; l'attribut
  `@wit` n'est pas pré-rempli, à renseigner ensuite avec l'inspecteur.

## 6. Assistant d'en-tête TEI (phase 6)

**Outils > Assistant d'en-tête...** ouvre un dialogue à 7 onglets : **Titre et responsabilités**
(titres multiples typés, auteurs/éditeurs/financeurs ou `respStmt` générique avec ORCID et
affiliation), **Édition** (mention d'édition + étendue), **Publication** (éditeur, lieu, date,
identifiants, licence — reconnaît les licences SPDX courantes, sinon nom/URL libres —, mention de
droits), **Source** (bibliographie en texte libre, ou `msDesc` minimal pour un manuscrit),
**Encodage** (`projectDesc`/`editorialDecl`/`tagsDecl` en texte libre), **Profil** (langues avec
pourcentage d'usage, mots-clés, résumé, participants), **Révisions** (liste de `<change>` avec
date/responsable/description).

L'assistant **relit** le `<teiHeader>` existant et ne réécrit, au clic sur **Appliquer**, que les
sous-éléments dont une valeur a réellement changé — tout le reste du document (y compris des
éléments que l'assistant ne gère pas, comme `<seriesStmt>` ou `<notesStmt>`) reste identique au
caractère près. Si `<teiHeader>` ou `<fileDesc>` est totalement absent du document, un avertissement
prévient que l'assistant affichera ce qu'il peut lire mais ne pourra pas écrire les sous-éléments
dont il n'a pas pu calculer l'emplacement (limitation assumée, voir `docs/DECISIONS.md`) ; créer
d'abord ces ancêtres à la main (ou repartir d'un modèle, §1) règle le problème. **Annuler** referme
le dialogue sans toucher au document.

## 7. Préférences, thèmes et finition de l'interface (phases 3 et 8)

**Outils > Préférences...** : thème (clair/sombre), dossier du dernier fichier ouvert (information),
activation et intervalle de l'enregistrement automatique (5 à 3600 secondes). Le brouillon
automatique est proposé au redémarrage si le document n'avait pas été enregistré (§1).

**Affichage > Thème** bascule entre un thème clair sobre et un thème sombre inspiré de Monokai, tous
deux vérifiés pour un contraste texte/fond conforme aux recommandations WCAG. Les icônes de barre
d'outils (jeu Lucide, libre de droits) se recolorent automatiquement avec le thème actif. Les quatre
barres d'outils et les quatre docks sont déplaçables/détachables et leur disposition est mémorisée
d'une session à l'autre (`QMainWindow.saveState`), de même que la taille et la position de la
fenêtre. Tous les boutons de barre d'outils sont atteignables au clavier (`Tab`/`Shift+Tab`), avec une
infobulle qui rappelle le raccourci de chaque action.

## 8. Limites connues

- Pas de rendu visuel des balises (pas de « pastilles » inline) : le texte XML est affiché tel
  quel, avec coloration syntaxique générique. C'est un choix délibéré (voir ADR-0001 de
  `docs/DECISIONS.md`), pas un oubli.
- Le chemin XPath affiché dans la barre d'état peut rester rattaché à un élément déjà refermé si le
  curseur se trouve juste après sa balise fermante et avant celle de son parent (limite documentée
  d'ADR-0007) — sans conséquence sur les opérations d'édition elles-mêmes, qui utilisent un repérage
  plus précis.
- Un fichier encodé en UTF-16 sans BOM n'est pas détecté comme tel à l'ouverture (ADR-0006).
- Les fins de ligne mixtes au sein d'un même fichier (`\n` et `\r\n` mélangés) ne sont pas préservées
  telles quelles à l'enregistrement : la convention majoritaire du fichier est réappliquée partout.
