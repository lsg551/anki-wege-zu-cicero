"""Tests for the issue workflow helpers."""

from __future__ import annotations

import io
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from scripts import issue_deck


def _write_apkg(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("collection.anki2", b"collection")
        archive.writestr("meta", b"")


def _fake_fetch_apkg(url: str, dest: Path) -> None:
    del url
    _write_apkg(dest)


def _patch_diff(
    monkeypatch: pytest.MonkeyPatch, code: int, out: str = "", err: str = ""
) -> None:
    def fake(apkg: Path, diff: Path, error: Path) -> int:
        del apkg
        diff.write_text(out)
        error.write_text(err)
        return code

    monkeypatch.setattr(issue_deck, "diff_against_dump", fake)


def _patch_run(
    monkeypatch: pytest.MonkeyPatch,
    diff_code: int,
    diff_out: str = "",
    fail: str | None = None,
) -> None:
    def fake(command: list[str]) -> subprocess.CompletedProcess[str]:
        sub = command[1]
        if sub == fail:
            return subprocess.CompletedProcess(command, 1, "", "boom")
        if sub == "diff":
            return subprocess.CompletedProcess(command, diff_code, diff_out, "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(issue_deck, "run", fake)


def test_find_attachment_url_markdown_link() -> None:
    body = "hello\n[deck.apkg.zip](https://github.com/user-attachments/assets/abc)\n"
    assert (
        issue_deck.find_attachment_url(body)
        == "https://github.com/user-attachments/assets/abc"
    )


def test_find_attachment_url_raw() -> None:
    body = "see https://example.com/deck.apkg now"
    assert issue_deck.find_attachment_url(body) == "https://example.com/deck.apkg"


def test_find_attachment_url_none() -> None:
    assert issue_deck.find_attachment_url("no links at all") is None


def test_normalize_renamed_apkg(tmp_path: Path) -> None:
    source = tmp_path / "deck.apkg.zip"
    _write_apkg(source)
    dest = tmp_path / "out.apkg"
    issue_deck.normalize_attachment(source, dest)
    with zipfile.ZipFile(dest) as archive:
        assert "collection.anki2" in archive.namelist()


def test_normalize_compressed_apkg(tmp_path: Path) -> None:
    inner = tmp_path / "deck.apkg"
    _write_apkg(inner)
    source = tmp_path / "compressed.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.write(inner, "deck.apkg")
    dest = tmp_path / "out.apkg"
    issue_deck.normalize_attachment(source, dest)
    assert dest.read_bytes() == inner.read_bytes()


def test_normalize_rejects_junk(tmp_path: Path) -> None:
    source = tmp_path / "junk.zip"
    source.write_bytes(b"not a zip")
    with pytest.raises(issue_deck.NotAPackageError):
        issue_deck.normalize_attachment(source, tmp_path / "out.apkg")


def test_normalize_rejects_zip_without_apkg(tmp_path: Path) -> None:
    source = tmp_path / "plain.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("readme.txt", b"nothing here")
    with pytest.raises(issue_deck.NotAPackageError):
        issue_deck.normalize_attachment(source, tmp_path / "out.apkg")


def test_normalize_rejects_junk_nested_apkg(tmp_path: Path) -> None:
    source = tmp_path / "bad.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("deck.apkg", b"not a zip either")
    with pytest.raises(issue_deck.NotAPackageError):
        issue_deck.normalize_attachment(source, tmp_path / "out.apkg")


def test_fetch_attachment_from_file_url(tmp_path: Path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"payload")
    dest = tmp_path / "dest.bin"
    issue_deck.fetch_attachment(source.as_uri(), dest)
    assert dest.read_bytes() == b"payload"


def test_run_captures_output() -> None:
    result = issue_deck.run([sys.executable, "-c", "print('hi')"])
    assert result.returncode == 0
    assert result.stdout.strip() == "hi"


def test_diff_against_dump_writes_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, "out", "err")

    monkeypatch.setattr(issue_deck, "run", fake_run)
    diff = tmp_path / "diff.txt"
    error = tmp_path / "error.txt"
    code = issue_deck.diff_against_dump(tmp_path / "x.apkg", diff, error)
    assert code == 1
    assert diff.read_text() == "out"
    assert error.read_text() == "err"


def test_render_comment_unchanged() -> None:
    body = issue_deck.render_comment(0, "", "", "http://run")
    assert issue_deck.MARKER in body
    assert "inhaltsgleich" in body


def test_render_comment_diff() -> None:
    body = issue_deck.render_comment(1, "-x\n+y\n", "", "http://run")
    assert "```diff" in body
    assert "+y" in body


def test_render_comment_truncates() -> None:
    body = issue_deck.render_comment(
        1, "x" * (issue_deck.DIFF_LIMIT + 10), "", "http://run"
    )
    assert "gekürzt" in body
    assert "x" * (issue_deck.DIFF_LIMIT + 1) not in body


def test_render_comment_error() -> None:
    body = issue_deck.render_comment(2, "", "boom", "http://run")
    assert "umbenennen" in body
    assert "boom" in body


def test_render_pr_body() -> None:
    body = issue_deck.render_pr_body(7, "```diff\n+x\n```\n")
    assert "Closes #7" in body
    assert "+x" in body


def test_render_pr_body_truncates() -> None:
    body = issue_deck.render_pr_body(7, "x" * (issue_deck.DIFF_LIMIT + 10))
    assert "gekürzt" in body


def test_parse_diff_without_url(tmp_path: Path) -> None:
    issue_deck.parse_diff("no link", tmp_path, "http://run")
    assert (tmp_path / "code.txt").read_text().strip() == "2"
    assert "Kein Anhang" in (tmp_path / "body.md").read_text()


def test_parse_diff_junk_attachment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(url: str, dest: Path) -> None:
        del url
        dest.write_bytes(b"junk")

    monkeypatch.setattr(issue_deck, "fetch_attachment", fetch)
    issue_deck.parse_diff(
        "https://github.com/user-attachments/x", tmp_path, "http://run"
    )
    assert (tmp_path / "code.txt").read_text().strip() == "2"
    assert "kein Anki-Deck" in (tmp_path / "body.md").read_text()


def test_parse_diff_fetch_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(url: str, dest: Path) -> None:
        del url, dest
        raise OSError("boom")

    monkeypatch.setattr(issue_deck, "fetch_attachment", fetch)
    issue_deck.parse_diff(
        "https://github.com/user-attachments/x", tmp_path, "http://run"
    )
    assert (tmp_path / "code.txt").read_text().strip() == "2"
    assert "konnte nicht geladen" in (tmp_path / "body.md").read_text()


def test_parse_diff_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_diff(monkeypatch, 0)
    issue_deck.parse_diff(
        "https://github.com/user-attachments/x", tmp_path, "http://run"
    )
    assert (tmp_path / "code.txt").read_text().strip() == "0"
    assert "inhaltsgleich" in (tmp_path / "body.md").read_text()


def test_parse_diff_changed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_diff(monkeypatch, 1, out="-x\n+y\n")
    issue_deck.parse_diff(
        "https://github.com/user-attachments/x", tmp_path, "http://run"
    )
    assert (tmp_path / "code.txt").read_text().strip() == "1"
    assert "+y" in (tmp_path / "body.md").read_text()


def test_parse_diff_tool_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_diff(monkeypatch, 2, err="bad package")
    issue_deck.parse_diff(
        "https://github.com/user-attachments/x", tmp_path, "http://run"
    )
    assert (tmp_path / "code.txt").read_text().strip() == "2"
    assert "bad package" in (tmp_path / "body.md").read_text()


def test_parse_apply_changed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_run(monkeypatch, diff_code=1, diff_out="```diff\n+x\n```\n")
    changed = issue_deck.parse_apply(
        "https://github.com/user-attachments/x", tmp_path, 7
    )
    assert changed is True
    assert "Closes #7" in (tmp_path / "pr-body.md").read_text()


def test_parse_apply_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_run(monkeypatch, diff_code=0)
    changed = issue_deck.parse_apply(
        "https://github.com/user-attachments/x", tmp_path, 7
    )
    assert changed is False


def test_parse_apply_without_url(tmp_path: Path) -> None:
    with pytest.raises(issue_deck.IssueError):
        issue_deck.parse_apply("no link", tmp_path, 7)


@pytest.mark.parametrize("fail", ["dump", "build"])
def test_parse_apply_tool_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail: str
) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_run(monkeypatch, diff_code=0, fail=fail)
    with pytest.raises(issue_deck.IssueError):
        issue_deck.parse_apply("https://github.com/user-attachments/x", tmp_path, 7)


def test_parse_apply_diff_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_run(monkeypatch, diff_code=2)
    with pytest.raises(issue_deck.IssueError):
        issue_deck.parse_apply("https://github.com/user-attachments/x", tmp_path, 7)


def test_cli_url(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = tmp_path / "body.txt"
    body.write_text("[d](https://github.com/user-attachments/abc)")
    assert issue_deck.main(["url", str(body)]) == 0
    assert capsys.readouterr().out.strip() == "https://github.com/user-attachments/abc"


def test_cli_url_missing(tmp_path: Path) -> None:
    body = tmp_path / "body.txt"
    body.write_text("nothing")
    assert issue_deck.main(["url", str(body)]) == 1


def test_cli_url_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.stdin", io.StringIO("https://github.com/user-attachments/abc")
    )
    assert issue_deck.main(["url", "-"]) == 0
    assert capsys.readouterr().out.strip() == "https://github.com/user-attachments/abc"


def test_cli_comment(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    diff = tmp_path / "diff.txt"
    error = tmp_path / "error.txt"
    diff.write_text("")
    error.write_text("")
    code = issue_deck.main(["comment", "0", str(diff), str(error), "http://run"])
    assert code == 0
    assert "inhaltsgleich" in capsys.readouterr().out


def test_cli_pr_body(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    diff = tmp_path / "d.md"
    diff.write_text("x")
    assert issue_deck.main(["pr-body", "3", str(diff)]) == 0
    assert "Closes #3" in capsys.readouterr().out


def test_cli_normalize(tmp_path: Path) -> None:
    source = tmp_path / "deck.apkg.zip"
    _write_apkg(source)
    dest = tmp_path / "out.apkg"
    assert issue_deck.main(["normalize", str(source), str(dest)]) == 0
    assert dest.exists()


def test_cli_normalize_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "junk.zip"
    source.write_bytes(b"junk")
    assert issue_deck.main(["normalize", str(source), str(tmp_path / "o.apkg")]) == 2
    assert "issue_deck:" in capsys.readouterr().err


def test_cli_parse_diff(tmp_path: Path) -> None:
    body = tmp_path / "body.txt"
    body.write_text("no link")
    assert issue_deck.main(["parse-diff", str(body), str(tmp_path), "http://run"]) == 0
    assert (tmp_path / "body.md").exists()


def test_cli_parse_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_run(monkeypatch, diff_code=1)
    body = tmp_path / "body.txt"
    body.write_text("https://github.com/user-attachments/x")
    assert issue_deck.main(["parse-apply", str(body), str(tmp_path), "7"]) == 0
    assert capsys.readouterr().out.strip() == "true"


def test_module_entrypoint(tmp_path: Path) -> None:
    body = tmp_path / "body.txt"
    body.write_text("no link")
    result = subprocess.run(
        [sys.executable, "-m", "scripts.issue_deck", "url", str(body)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
