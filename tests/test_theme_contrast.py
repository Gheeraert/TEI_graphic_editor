"""Vérifie le ratio de contraste WCAG des couleurs réellement déclarées
dans les feuilles de style claire/sombre (``tei_editor.ui.theme.THEMES``),
pas une vérification visuelle seulement (``docs/ROADMAP.md`` §5, phase 8).

Cible : ratio >= 4.5:1 (WCAG AA, texte normal) pour les paires texte
principal/fond et texte désactivé/fond de chaque thème."""

from __future__ import annotations

import pytest

from tei_editor.ui.theme import THEME_IDS, THEMES

WCAG_AA_NORMAL_TEXT_RATIO = 4.5


def _srgb_to_linear(channel: float) -> float:
    channel /= 255.0
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    r, g, b = (_srgb_to_linear(c) for c in (r, g, b))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color_a: str, color_b: str) -> float:
    l_a, l_b = _relative_luminance(color_a), _relative_luminance(color_b)
    lighter, darker = max(l_a, l_b), min(l_a, l_b)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize("theme_id", THEME_IDS)
def test_main_text_contrast_against_window_background(theme_id: str) -> None:
    colors = THEMES[theme_id]
    ratio = contrast_ratio(colors["text"], colors["window_bg"])
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO, (
        f"thème {theme_id} : contraste texte/fond = {ratio:.2f} < "
        f"{WCAG_AA_NORMAL_TEXT_RATIO}"
    )


@pytest.mark.parametrize("theme_id", THEME_IDS)
def test_disabled_text_contrast_against_window_background(theme_id: str) -> None:
    colors = THEMES[theme_id]
    ratio = contrast_ratio(colors["text_disabled"], colors["window_bg"])
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO, (
        f"thème {theme_id} : contraste texte désactivé/fond = {ratio:.2f} < "
        f"{WCAG_AA_NORMAL_TEXT_RATIO}"
    )


@pytest.mark.parametrize("theme_id", THEME_IDS)
def test_main_text_contrast_against_surface_background(theme_id: str) -> None:
    colors = THEMES[theme_id]
    ratio = contrast_ratio(colors["text"], colors["surface_bg"])
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO


@pytest.mark.parametrize("theme_id", THEME_IDS)
def test_disabled_text_contrast_against_surface_background(theme_id: str) -> None:
    colors = THEMES[theme_id]
    ratio = contrast_ratio(colors["text_disabled"], colors["surface_bg"])
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO
