"""Cas limites de :mod:`tei_editor.editor.current_element` non couverts par
`tests/test_current_element.py` (phase 9)."""

from __future__ import annotations

from tei_editor.editor.current_element import CurrentElement, ElementSpan


def test_span_of_renvoie_none_pour_un_element_none() -> None:
    span = ElementSpan(
        element=None,  # type: ignore[arg-type]
        start_tag_start=0,
        start_tag_end=3,
        self_closing=False,
    )
    current = CurrentElement(element=None, span=span, spans={})  # type: ignore[arg-type]
    assert current.span_of(None) is None
