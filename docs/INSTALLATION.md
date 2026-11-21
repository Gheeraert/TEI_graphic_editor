# Installation de TIGRE

## Prérequis

- Python ≥ 3.11 (`requires-python` de `pyproject.toml`).
- Les dépendances (PySide6 ≥ 6.6, lxml ≥ 5.0) sont installées automatiquement par `pip`/`pipx` :
  rien à installer séparément, pas d'accès réseau requis par l'application elle-même une fois
  installée (seul l'outillage de build, `tools/build_catalog.py`/`fetch_schema.py`/`fetch_icons.py`,
  télécharge des sources TEI/icônes — déjà fait une fois pour toutes et committé dans le dépôt,
  inutile à une installation normale).

## Installation pour un usage courant

Avec [pipx](https://pipx.pypa.io/) (recommandé : isole l'application dans son propre environnement,
sans toucher au Python système) :

```
pipx install .
```

depuis la racine du dépôt (le dossier qui contient `pyproject.toml`). La commande `tei-editor` est
alors disponible directement.

Sans pipx, dans un environnement virtuel (`python -m venv .venv` puis activation) :

```
pip install .
```

Dans les deux cas, lancer l'application :

```
tei-editor
```

Pour installer en mode développement (le code du dépôt reste modifiable sans réinstaller) :

```
pip install -e ".[dev]"
```

## Vérification effectuée pour cette phase

L'installation ci-dessus a été testée réellement (pas seulement relue) : création d'un nouveau venv
isolé (hors de celui utilisé pour le développement), `pip install .` depuis la racine du dépôt,
puis lancement de l'entrée de script `tei-editor` ainsi installée, en mode hors écran
(`QT_QPA_PLATFORM=offscreen`) — l'application démarre, construit sa fenêtre principale, et se ferme
proprement.

Ce test a révélé un défaut réel de `pyproject.toml` : sans déclaration explicite de
`[tool.setuptools.package-data]`, `pip install .` n'embarquait que les fichiers `.py` et omettait
tout `src/tei_editor/data/` (catalogue TEI, profils JSON, schémas RelaxNG, icônes SVG, paires
`choice` du jeu de balises) — l'application plantait au lancement (`FileNotFoundError` sur
`action_icons.json`), même si `pytest` passait toujours (les tests tournent depuis le dépôt, pas
depuis un paquet installé, donc ne voyaient jamais ce trou). Corrigé dans `pyproject.toml`
(`tei_editor = ["data/**/*"]`) et vérifié par une réinstallation complète dans le même venv propre
après correction ; un test de non-régression (`tests/test_packaging.py`) fait désormais échouer la
suite si cette déclaration disparaissait à nouveau.

## Exécutable autonome (optionnel)

`docs/ROADMAP.md` ne demande un exécutable autonome qu'« éventuellement » : ce n'est pas un critère
d'acceptation de cette phase. Aucun exécutable autonome n'a été construit ni committé ici, pour une
raison qui dépasse le simple manque de temps : **un script PyInstaller exécuté sur cette machine
(Windows) ne peut produire qu'un exécutable Windows**. PyInstaller ne fait pas de compilation croisée
— il embarque l'interpréteur et les bibliothèques natives de la plateforme sur laquelle il tourne.
Produire aussi des exécutables macOS et Linux demanderait de relancer le même script sur une machine
macOS et une machine Linux (ou via des images/CI dédiées à chaque OS), ce qui n'est pas possible
depuis cette session. Documenter cette limite ici plutôt que prétendre à un résultat multiplateforme
non vérifié a semblé préférable à construire un exécutable Windows seul en le présentant comme une
solution de distribution générale.

Pour qui voudrait tenter la construction d'un exécutable Windows à partir de ce dépôt :

```
pip install -e ".[dev]"
pip install pyinstaller
pyinstaller --name tei-editor --onedir --windowed ^
    --add-data "src\tei_editor\data;tei_editor\data" ^
    --paths src ^
    src\tei_editor\app.py
```

(syntaxe `cmd.exe` ; adapter `--add-data` avec `:` au lieu de `;` sous macOS/Linux si tenté sur ces
plateformes). Le dossier `data/` doit être explicitement embarqué (`--add-data`) : PyInstaller, comme
`pip` avant la correction ci-dessus, ne devine pas qu'un paquet a besoin de fichiers non-`.py` à
l'exécution. Non testé dans cette phase (pas de build effectivement lancé ni vérifié) : à valider par
quiconque l'essaie avant de considérer ce résultat comme acquis.
