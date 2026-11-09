"""Integration tests that exercise the real anki-tools shell-out.

These are slower than the unit tests (they import the anki library) and they
catch a pinned anki-tools version whose behaviour changed.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts import issue_deck

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "anki-wege-zu-cicero.apkg"


def _fetch_from_package(source: Path) -> Callable[[str, Path], None]:
    """Return a fetch that copies *source* instead of downloading."""

    def fetch(url: str, dest: Path) -> None:
        del url
        shutil.copyfile(source, dest)

    return fetch


@pytest.fixture(autouse=True)
def _in_repo_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run from the repository root so the relative ``dump`` path resolves."""
    monkeypatch.chdir(REPO_ROOT)


def test_real_diff_matches_committed_dump(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fetch_from_package(PACKAGE))
    issue_deck.parse_diff("https://user-attachments/x", tmp_path)
    assert (tmp_path / "code.txt").read_text().strip() == "0"


def test_real_apply_detects_no_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fetch_from_package(PACKAGE))
    changed = issue_deck.parse_apply("https://user-attachments/x", tmp_path, 1)
    assert changed is False
    assert (tmp_path / "deck.apkg").is_file()
    assert "Closes #1" in (tmp_path / "pr-body.md").read_text()
