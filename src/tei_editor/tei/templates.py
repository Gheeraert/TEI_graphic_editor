"""Modèles de document pour « Nouveau » (phase 6, ``docs/ROADMAP.md`` §5) :
minimal valide (repris de la phase 3), édition critique, théâtre,
correspondance. Chacun est un squelette ``teiHeader``+``text`` de base,
valide contre le schéma RelaxNG unique ``tei_all`` (ADR-0007) — pas de
contenu réaliste, juste une structure qui démarre dans le bon profil
(``docs/ROADMAP.md`` : « pas besoin de contenu réaliste, juste une
structure TEI valide RelaxNG qui démarre dans le bon profil »).

Un petit sous-menu « Nouveau > » (``actions.py``/``menus.py``) plutôt
qu'une boîte de dialogue : le choix est resté simple (4 entrées fixes,
pas de paramétrage), un sous-menu évite une fenêtre modale supplémentaire
pour un choix aussi direct.
"""

from __future__ import annotations

from dataclasses import dataclass

from tei_editor.editor.text_editor import NEW_DOCUMENT_TEMPLATE

_EDITION_CRITIQUE_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "  <teiHeader>\n"
    "    <fileDesc>\n"
    "      <titleStmt>\n"
    "        <title>Sans titre (édition critique)</title>\n"
    "      </titleStmt>\n"
    "      <publicationStmt>\n"
    "        <p>Non publié.</p>\n"
    "      </publicationStmt>\n"
    "      <sourceDesc>\n"
    "        <listWit>\n"
    '          <witness xml:id="A">Témoin A.</witness>\n'
    '          <witness xml:id="B">Témoin B.</witness>\n'
    "        </listWit>\n"
    "      </sourceDesc>\n"
    "    </fileDesc>\n"
    "  </teiHeader>\n"
    "  <text>\n"
    "    <body>\n"
    "      <p>\n"
    '        <app>\n'
    '          <lem wit="#A">leçon retenue</lem>\n'
    '          <rdg wit="#B">variante</rdg>\n'
    "        </app>\n"
    "      </p>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)

_THEATRE_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "  <teiHeader>\n"
    "    <fileDesc>\n"
    "      <titleStmt>\n"
    "        <title>Sans titre (théâtre)</title>\n"
    "      </titleStmt>\n"
    "      <publicationStmt>\n"
    "        <p>Non publié.</p>\n"
    "      </publicationStmt>\n"
    "      <sourceDesc>\n"
    "        <p>Document né numérique : aucune source.</p>\n"
    "      </sourceDesc>\n"
    "    </fileDesc>\n"
    "  </teiHeader>\n"
    "  <text>\n"
    "    <front>\n"
    "      <castList>\n"
    '        <castItem><role xml:id="r-personnage">Un personnage</role></castItem>\n'
    "      </castList>\n"
    "    </front>\n"
    "    <body>\n"
    '      <div type="act" n="1">\n'
    '        <div type="scene" n="1">\n'
    "          <sp who=\"#r-personnage\">\n"
    "            <speaker>Un personnage</speaker>\n"
    "            <p>Première réplique.</p>\n"
    "          </sp>\n"
    "        </div>\n"
    "      </div>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)

_CORRESPONDANCE_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "  <teiHeader>\n"
    "    <fileDesc>\n"
    "      <titleStmt>\n"
    "        <title>Sans titre (correspondance)</title>\n"
    "      </titleStmt>\n"
    "      <publicationStmt>\n"
    "        <p>Non publié.</p>\n"
    "      </publicationStmt>\n"
    "      <sourceDesc>\n"
    "        <p>Document né numérique : aucune source.</p>\n"
    "      </sourceDesc>\n"
    "    </fileDesc>\n"
    "    <profileDesc>\n"
    "      <correspDesc>\n"
    '        <correspAction type="sent">\n'
    "          <persName>Expéditeur</persName>\n"
    '          <date when="2026-11-21">21 novembre 2026</date>\n'
    "        </correspAction>\n"
    '        <correspAction type="received">\n'
    "          <persName>Destinataire</persName>\n"
    "        </correspAction>\n"
    "      </correspDesc>\n"
    "    </profileDesc>\n"
    "  </teiHeader>\n"
    "  <text>\n"
    "    <body>\n"
    "      <div>\n"
    "        <opener>\n"
    "          <salute>Cher correspondant,</salute>\n"
    "        </opener>\n"
    "        <p>Corps de la lettre.</p>\n"
    "        <closer>\n"
    "          <salute>Bien à vous.</salute>\n"
    "        </closer>\n"
    "      </div>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)


@dataclass(frozen=True)
class DocumentTemplate:
    template_id: str
    label: str
    text: str


#: Ordre d'affichage du sous-menu « Nouveau > » (``docs/ROADMAP.md`` §5,
#: phase 6 : « minimal valide (déjà là), édition critique, théâtre,
#: correspondance »).
TEMPLATES: list[DocumentTemplate] = [
    DocumentTemplate("minimal", "&Minimal valide", NEW_DOCUMENT_TEMPLATE),
    DocumentTemplate("edition_critique", "Édition &critique", _EDITION_CRITIQUE_TEMPLATE),
    DocumentTemplate("theatre", "&Théâtre", _THEATRE_TEMPLATE),
    DocumentTemplate("correspondance", "C&orrespondance", _CORRESPONDANCE_TEMPLATE),
]

_BY_ID = {template.template_id: template for template in TEMPLATES}


def template_text(template_id: str) -> str:
    """Texte du modèle ``template_id``, ou le modèle minimal si
    l'identifiant est inconnu (ne doit pas arriver en usage normal : les
    identifiants viennent du sous-menu construit depuis :data:`TEMPLATES`)."""
    return _BY_ID.get(template_id, _BY_ID["minimal"]).text
