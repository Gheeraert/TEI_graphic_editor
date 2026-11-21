# Journal de décisions d'architecture (ADR courts)

## ADR-0001 — Texte XML assisté, pas de pivot objet, pas de WYSIWYG

**Statut.** Adopté (phase 0), à reconfirmer avant la phase 3 (voir `docs/ROADMAP.md` §7).

**Contexte.** Mérope encode son éditeur Qt autour d'un pivot `Block`/`InlineRun` pensé pour du Markdown à structure plate. TEI est un arbre XML à contenu mixte, attributs et imbrication libre : ce pivot ne se transpose pas sans perte (contenu mixte, commentaires, PI, espaces significatifs, ordre des attributs).

**Décision.** La source de vérité du document est son texte XML, édité dans un `QPlainTextEdit` avec coloration syntaxique. L'interface graphique (palette de balises, inspecteur d'attributs, plan structurel, panneau de problèmes) est une assistance posée au-dessus de ce texte, jamais un modèle objet qui s'y substitue. Le modèle structurel (arbre lxml) est **dérivé** du texte par re-parsing différé (debounce) ; jamais l'inverse. Aucune sérialisation « pretty-print » qui toucherait au contenu mixte.

**Conséquences.** Round-trip fidèle garanti par construction. Pas d'objet « étranger » refusé par un modèle qui ne sait pas le retranscrire. Coût de développement réduit par rapport à un portage du pivot `Block`/`InlineRun`. En contrepartie, pas de rendu visuel des balises en v1 (une variante « pastilles » inline reste possible plus tard, toujours adossée au texte XML).

## ADR-0002 — Nom de paquet provisoire

**Statut.** Provisoire, à reconfirmer avant la phase 3 (voir `docs/ROADMAP.md` §7, point 3).

**Décision.** Le paquet Python est nommé `tei_editor` (répertoire `src/tei_editor/`) en l'absence d'un nom de projet choisi par l'utilisateur. Renommage trivial si un autre nom est retenu.
