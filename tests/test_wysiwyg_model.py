from tei_editor.wysiwyg.model import Block, InlineRun, merge_adjacent_runs


def test_merge_adjacent_runs_combines_same_style() -> None:
    runs = [
        InlineRun(text="a", style="hi"),
        InlineRun(text="b", style="hi"),
        InlineRun(text="c", style=None),
    ]
    merged = merge_adjacent_runs(runs)
    assert merged == [InlineRun(text="ab", style="hi"), InlineRun(text="c", style=None)]


def test_merge_adjacent_runs_drops_empty_text() -> None:
    runs = [InlineRun(text="", style="hi"), InlineRun(text="x", style=None)]
    assert merge_adjacent_runs(runs) == [InlineRun(text="x", style=None)]


def test_merge_adjacent_runs_distinguishes_lang() -> None:
    runs = [
        InlineRun(text="a", style="foreign", lang="la"),
        InlineRun(text="b", style="foreign", lang="en"),
    ]
    merged = merge_adjacent_runs(runs)
    assert len(merged) == 2


def test_block_default_runs_is_empty_list() -> None:
    block = Block(kind="p", level=0)
    assert block.runs == []
