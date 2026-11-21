# Balises génétiques essentielles — repères

Les échantillons de ce dossier s'appuient (1) sur la page de travail du groupe TEI
« éditions génétiques » (TCW19, état de brouillon, éléments non-TEI préfixés `ge:`) et
(2) sur les **spécifications de la TEI P5 courante** (dépôt TEIC/TEI, branche `dev`, états
du 4 novembre 2026), qui ont depuis intégré une partie de ces propositions.
**C'est P5 qui fait foi pour les noms de balises** : ne pas utiliser le préfixe `ge:`.

## Le noyau à retenir (tout ne sert pas)

| Besoin | Balise P5 | Attributs utiles | Échantillon |
|---|---|---|---|
| Ajout | `add` | `@place`, `@hand`, `@change` | 07-01 |
| Suppression | `del` | `@rend`, `@hand`, `@instant` | 07-01 |
| Substitution | `subst` (= `del` + `add`) | `@instant`, `@change` | 07-01, 07-02 |
| Annuler une suppression | `restore` | `@hand` | 07-01 |
| Passage long biffé / ajouté | `delSpan`, `addSpan` + `anchor` | `@spanTo` | 07-01 |
| Qui a écrit | `handNote` (en-tête), `@hand`, `handShift` | `@new`, `@medium` | 07-02 |
| Quand (stades) | `listChange`/`change` (en-tête), `@change` | `@ordered`, `@when` | 07-02 |
| Correction immédiate | `@instant="true"` | `@seq` pour l'ordre | 07-02 |
| Signes de lecture | `metamark` | `@function`, `@target`, `@place` | 07-03 |
| Transposition | `listTranspose`/`transpose`/`ptr` | `@target` | 07-03 |
| Repassé / réécrit | `retrace` | `@hand`, `@cause` | 07-03 |
| Annuler / réaffirmer | `undo`, `redo` (éléments vides) | `@target` | 07-03 |
| Lien avec l'image | `facsimile`, `surface`, `zone`, `@facs` | `@ulx @uly @lrx @lry`, `@rotate` | 07-04 |

## Hors du noyau (volontairement laissés de côté)

Graphes génétiques de dossier (`graph`/`node`/`arc`), assemblage `teiCorpus` + XInclude,
`ge:patch`, `ge:used`, `ge:interAdd`, `substJoin` (substitutions disjointes), `damageSpan`,
`mod` (modification non interprétée : usage prudent). À ajouter plus tard, sur besoin réel.

## Attention aux attributs (vérifié dans les spécifications)

`@hand`, `@place`, `@instant`, `@cause`, `@seq` sont disponibles sur `add`, `del`, `subst`,
`restore`, `retrace`, `undo`, `redo`, `mod`, `delSpan`, `addSpan`. En revanche `@hand` n'existe
pas sur `lg` ni `l` : on l'attache à un `div`, `p`, `ab`, `seg` ou `hi` englobant.
