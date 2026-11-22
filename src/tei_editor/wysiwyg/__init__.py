"""Mode WYSIWYG (phase 10, ``docs/DECISIONS.md`` ADR-0009).

Pivot ``Block``/``InlineRun`` qui masque les balises TEI à l'écran pour le
contenu de ``<body>``, inspiré du pivot Markdown de Mérope mais limité au
sous-ensemble d'éléments listé dans ``model.py`` (profil « Édition de
textes », premier jalon). Voir ADR-0009 pour la politique de
simplification appliquée aux éléments non modélisés : ce mode **n'est
pas** un round-trip sans perte, contrairement au reste de l'éditeur
(ADR-0001, toujours en vigueur en mode texte).
"""
