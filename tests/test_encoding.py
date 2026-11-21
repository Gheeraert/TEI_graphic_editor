"""Détection d'encodage/fin de ligne (sans Qt), tei_editor.editor.encoding."""

from __future__ import annotations

from tei_editor.editor.encoding import decode_document, detect_encoding, encode_document


def test_detects_utf8_declared_without_bom() -> None:
    data = '<?xml version="1.0" encoding="UTF-8"?>\n<TEI/>\n'.encode("utf-8")
    encoding = detect_encoding(data)
    assert encoding.name == "utf-8"
    assert encoding.bom == b""
    assert encoding.newline == "\n"


def test_defaults_to_utf8_without_declaration() -> None:
    data = b"<TEI/>\n"
    encoding = detect_encoding(data)
    assert encoding.name == "utf-8"
    assert encoding.bom == b""


def test_detects_utf8_bom() -> None:
    data = b"\xef\xbb\xbf" + '<?xml version="1.0" encoding="UTF-8"?><TEI/>'.encode("utf-8")
    encoding = detect_encoding(data)
    assert encoding.name == "utf-8"
    assert encoding.bom == b"\xef\xbb\xbf"


def test_detects_utf16_le_bom() -> None:
    body = '<?xml version="1.0" encoding="UTF-16"?><TEI/>'.encode("utf-16-le")
    data = b"\xff\xfe" + body
    encoding = detect_encoding(data)
    assert encoding.name == "utf-16-le"
    assert encoding.bom == b"\xff\xfe"


def test_detects_crlf_newline() -> None:
    data = b"<TEI>\r\n<a/>\r\n</TEI>\r\n"
    encoding = detect_encoding(data)
    assert encoding.newline == "\r\n"


def test_detects_lf_newline() -> None:
    data = b"<TEI>\n<a/>\n</TEI>\n"
    encoding = detect_encoding(data)
    assert encoding.newline == "\n"


def test_decode_then_encode_round_trips_utf8_lf() -> None:
    original = '<?xml version="1.0" encoding="UTF-8"?>\n<TEI><a/></TEI>\n'.encode("utf-8")
    text, encoding = decode_document(original)
    assert encode_document(text, encoding) == original


def test_decode_then_encode_round_trips_utf8_bom_crlf() -> None:
    original = (
        b"\xef\xbb\xbf"
        + '<?xml version="1.0" encoding="UTF-8"?>\r\n<TEI>\r\n<a/>\r\n</TEI>\r\n'.encode("utf-8")
    )
    text, encoding = decode_document(original)
    assert encode_document(text, encoding) == original


def test_decode_then_encode_round_trips_utf16_le_bom() -> None:
    body = '<?xml version="1.0" encoding="UTF-16"?><TEI><a/></TEI>'.encode("utf-16-le")
    original = b"\xff\xfe" + body
    text, encoding = decode_document(original)
    assert encode_document(text, encoding) == original
