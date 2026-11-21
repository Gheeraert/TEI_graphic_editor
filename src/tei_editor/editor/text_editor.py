"""Le ``QPlainTextEdit`` qui porte le texte XML : source de vérité unique
(ADR-0001). Ouverture/enregistrement passent par :mod:`tei_editor.editor.encoding`
(détection/préservation de l'encodage et de la fin de ligne) et par
:func:`tei_editor.content.atomic_write.atomic_write_bytes` (écriture
atomique, sans traduction d'octets) pour garantir le round-trip octet à
octet exigé par la phase 3.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFont, QTextOption
from PySide6.QtWidgets import QPlainTextEdit

from tei_editor.content.atomic_write import atomic_write_bytes
from tei_editor.editor.encoding import DocumentEncoding, decode_document, encode_document
from tei_editor.editor.xml_highlighter import XmlHighlighter

#: Squelette minimal valide (voir tests/fixtures/tei-samples/01-structure/01-minimal.xml,
#: modèle de référence du corpus de la phase 1/ADR-0005). Une seule
#: proposition de modèle à ce stade : les modèles multiples par type
#: d'édition (théâtre, édition critique...) viennent en phase 6/7.
NEW_DOCUMENT_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "  <teiHeader>\n"
    "    <fileDesc>\n"
    "      <titleStmt>\n"
    "        <title>Sans titre</title>\n"
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
    "    <body>\n"
    "      <p></p>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)

_DEFAULT_ENCODING = DocumentEncoding(name="utf-8", bom=b"", newline="\n")


class XmlTextEditor(QPlainTextEdit):
    """Éditeur de texte XML brut, sans réindentation ni réécriture
    automatique (contenu mixte, ADR-0001 §3.A3.8)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setTabChangesFocus(False)
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(11)
        self.setFont(font)
        self.highlighter = XmlHighlighter(self.document())

        self.current_path: Path | None = None
        self.current_encoding: DocumentEncoding = _DEFAULT_ENCODING

    # -- Nouveau document --------------------------------------------------
    def new_from_template(self, template_text: str | None = None) -> None:
        """Charge un modèle de nouveau document (``template_text``, l'un
        des 4 modèles de `tei_editor.tei.templates` — phase 6 — ou le
        modèle minimal par défaut)."""
        self.setPlainText(template_text if template_text is not None else NEW_DOCUMENT_TEMPLATE)
        self.document().setModified(False)
        self.current_path = None
        self.current_encoding = _DEFAULT_ENCODING

    # -- Ouverture -----------------------------------------------------------
    def load_file(self, path: Path) -> None:
        """Charge ``path`` en détectant son encodage et sa fin de ligne.

        Ne valide pas le document (bonne formation) : c'est la
        responsabilité de l'appelant (menu Outils > Valider, ou
        re-parsing différé) de signaler un document mal formé une fois
        chargé — on affiche quand même tout document lisible comme texte,
        y compris mal formé, pour pouvoir le corriger à la main.
        """
        path = Path(path)
        data = path.read_bytes()
        text, encoding = decode_document(data)
        self.setPlainText(text)
        self.document().setModified(False)
        self.current_path = path
        self.current_encoding = encoding

    # -- Enregistrement -------------------------------------------------------
    def save_to(self, path: Path, *, remember_as_current: bool = True) -> None:
        """Enregistre le texte courant vers ``path`` avec l'encodage et la
        fin de ligne mémorisés à l'ouverture (ou UTF-8/``"\\n"`` pour un
        nouveau document)."""
        path = Path(path)
        data = encode_document(self.toPlainText(), self.current_encoding)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes(path, data)
        if remember_as_current:
            self.current_path = path
            self.document().setModified(False)

    def export_copy_to(self, path: Path, *, encoding: DocumentEncoding | None = None) -> None:
        """« Exporter » (voir ``docs/DECISIONS.md``) : écrit une copie du
        XML courant vers ``path``, sans changer le fichier courant ouvert
        ni son état modifié. ``encoding`` permet de choisir un autre
        encodage pour l'export ; par défaut, celui du document courant.
        """
        path = Path(path)
        data = encode_document(self.toPlainText(), encoding or self.current_encoding)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_bytes(path, data)

    # -- Zoom -------------------------------------------------------------
    def zoom_editor_in(self) -> None:
        font = self.font()
        font.setPointSize(min(72, font.pointSize() + 1))
        self.setFont(font)

    def zoom_editor_out(self) -> None:
        font = self.font()
        font.setPointSize(max(6, font.pointSize() - 1))
        self.setFont(font)

    def zoom_editor_reset(self) -> None:
        font = self.font()
        font.setPointSize(11)
        self.setFont(font)
