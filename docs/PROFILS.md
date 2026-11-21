# Profils personnalisables

Un profil est un simple fichier JSON sous `src/tei_editor/data/profiles/`,
de la forme :

```json
{
  "id": "mon_profil",
  "label": "Mon profil",
  "description": "Une phrase décrivant l'usage visé.",
  "groups": [
    {"id": "structure", "label": "Structure", "elements": ["div", "head", "p"]}
  ]
}
```

- `id` doit être unique parmi les profils présents dans le dossier (il sert
  de clef interne, p. ex. pour `QSettings`) ; par convention il correspond
  au nom du fichier sans l'extension, mais ce n'est pas vérifié.
- `groups[].elements` est une liste blanche de noms d'éléments TEI (sans
  préfixe d'espace de noms) ; chaque nom doit exister dans
  `tei_editor/data/tei_catalog.json` (sinon il est simplement ignoré par la
  palette/l'avertissement « hors profil », sans erreur). `groups[].label`
  sert de titre de section dans la palette contextuelle (phase 5).
- Ce profil ne restreint jamais la validité RelaxNG du document (ADR-0007
  point 2) : c'est une liste blanche qui pilote la palette et un
  avertissement non bloquant, jamais une grammaire.

**Pour ajouter un 5ᵉ profil**, il suffit de déposer un nouveau fichier
`data/profiles/mon_profil.json` sur ce modèle : `tei_editor.tei.profiles.list_profiles()`
scanne déjà tout le dossier (`*.json`, un profil par fichier, triés avec les
quatre profils d'origine en tête et les suivants par ordre alphabétique
d'identifiant) — aucune modification de code n'est nécessaire, le profil
apparaît automatiquement dans le sous-menu « Outils > Profil actif ». Vérifié
par `tests/test_tei_catalog.py` (cohérence profils/catalogue) sur les quatre
profils fournis ; un profil ajouté par un utilisateur n'est pas couvert par
ces tests (il n'existe pas encore au moment où ils sont écrits), mais suit
exactement le même mécanisme de chargement.
