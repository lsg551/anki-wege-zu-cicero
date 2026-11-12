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
    monkeypatch: pytest.MonkeyPatch,
    code: int,
    out: str = "",
    err: str = "",
    summary: str = "",
) -> None:
    def fake(apkg: Path, diff: Path, error: Path, table: Path) -> int:
        del apkg
        diff.write_text(out)
        error.write_text(err)
        table.write_text(summary)
        return code

    monkeypatch.setattr(issue_deck, "diff_against_dump", fake)


def _patch_run(
    monkeypatch: pytest.MonkeyPatch,
    diff_code: int,
    diff_out: str = "",
    fail: str | None = None,
    summary_out: str = "",
) -> None:
    def fake(command: list[str]) -> subprocess.CompletedProcess[str]:
        sub = command[1]
        if sub == fail:
            return subprocess.CompletedProcess(command, 1, "", "boom")
        if sub == "diff":
            out = summary_out if "--summary" in command else diff_out
            return subprocess.CompletedProcess(command, diff_code, out, "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(issue_deck, "run", fake)


def _patch_gh(
    monkeypatch: pytest.MonkeyPatch,
    *,
    artifact: str = "123",
    existing: str = "",
    url: str = "https://example/comment",
    capture: dict[str, str] | None = None,
) -> None:
    def fake(command: list[str]) -> subprocess.CompletedProcess[str]:
        joined = " ".join(command)
        if "/artifacts" in joined:
            return subprocess.CompletedProcess(command, 0, artifact, "")
        if "--paginate" in command:
            return subprocess.CompletedProcess(command, 0, existing, "")
        if capture is not None:
            for part in command:
                if part.startswith("body=@"):
                    capture["body"] = Path(part[len("body=@") :]).read_text()
        return subprocess.CompletedProcess(command, 0, url, "")

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
        if "--summary" in command:
            return subprocess.CompletedProcess(command, 1, "| section |\n", "")
        out = "--- dump\n+++ /tmp/issue.apkg\n@@ -1 +1 @@\n-a\n+b\n"
        return subprocess.CompletedProcess(command, 1, out, "err")

    monkeypatch.setattr(issue_deck, "run", fake_run)
    diff = tmp_path / "diff.txt"
    error = tmp_path / "error.txt"
    summary = tmp_path / "summary.txt"
    code = issue_deck.diff_against_dump(tmp_path / "x.apkg", diff, error, summary)
    assert code == 1
    assert "--- Repository" in diff.read_text()
    assert "+++ Vorschlag" in diff.read_text()
    assert "/tmp/issue.apkg" not in diff.read_text()
    assert error.read_text() == "err"
    assert summary.read_text() == "| section |\n"


def test_diff_against_dump_writes_no_summary_when_equal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(issue_deck, "run", fake_run)
    summary = tmp_path / "summary.txt"
    issue_deck.diff_against_dump(
        tmp_path / "x.apkg", tmp_path / "d", tmp_path / "e", summary
    )
    assert summary.read_text() == ""


def test_relabel_diff_plain() -> None:
    text = "--- dump\n+++ /home/runner/x.apkg\n@@ -1 +1 @@\n-a\n+b\n"
    out = issue_deck._relabel_diff(text)
    assert "--- Repository" in out
    assert "+++ Vorschlag" in out
    assert "/home/runner" not in out
    assert "-a" in out


def test_relabel_diff_fenced() -> None:
    text = "```diff\n--- dump\n+++ /tmp/x\n@@\n```\n"
    out = issue_deck._relabel_diff(text)
    assert "--- Repository" in out
    assert "/tmp/x" not in out


def test_render_comment_mentions_bot() -> None:
    body = issue_deck.render_comment(0, "", "")
    assert issue_deck.BOT_NOTE in body
    assert body.index("Bot") < body.index("### Deck-Vorschlag")


def test_render_comment_unchanged() -> None:
    body = issue_deck.render_comment(0, "", "")
    assert issue_deck.MARKER in body
    assert "inhaltsgleich" in body


def test_render_comment_diff() -> None:
    body = issue_deck.render_comment(1, "-x\n+y\n", "")
    assert "```diff" in body
    assert "+y" in body


def test_render_comment_notes_then_table() -> None:
    body = issue_deck.render_comment(
        1, "-x\n+y\n", "anki-tools: error: boom", summary="| section |\n"
    )
    assert "> [!WARNING]" in body
    assert "- error: boom" in body
    assert "anki-tools: error:" not in body
    assert "| section |" in body
    assert body.index("boom") < body.index("| section |")


def test_render_comment_truncates_with_link_outside_details() -> None:
    body = issue_deck.render_comment(
        1, "x" * (issue_deck.DIFF_LIMIT + 10), "", "https://example/full"
    )
    assert "gekürzt" in body
    assert "https://example/full" in body
    assert body.index("</details>") < body.index("gekürzt")
    assert "x" * (issue_deck.DIFF_LIMIT + 1) not in body


def test_render_comment_truncates_without_link() -> None:
    body = issue_deck.render_comment(1, "x" * (issue_deck.DIFF_LIMIT + 10), "")
    assert "Der Diff ist gekürzt." in body
    assert "](http" not in body


def test_render_comment_error() -> None:
    body = issue_deck.render_comment(2, "", "boom")
    assert "umbenennen" in body
    assert "boom" in body


def test_render_ack() -> None:
    body = issue_deck.render_ack()
    assert body.startswith(issue_deck.MARKER)
    assert "Bot" in body


def test_render_pr_body() -> None:
    body = issue_deck.render_pr_body(7, "```diff\n+x\n```\n")
    assert "Closes #7" in body
    assert "+x" in body


def test_render_pr_body_includes_the_summary() -> None:
    body = issue_deck.render_pr_body(7, "```diff\n+x\n```\n", "| section |\n")
    assert "Closes #7" in body
    assert "| section |" in body


def test_render_pr_body_truncates() -> None:
    body = issue_deck.render_pr_body(7, "x" * (issue_deck.DIFF_LIMIT + 10))
    assert "gekürzt" in body


def test_strip_issue_prefix_removes_marker() -> None:
    assert issue_deck.strip_issue_prefix("[Änderung] advocō korrigiert") == (
        "advocō korrigiert"
    )


def test_strip_issue_prefix_case_insensitive() -> None:
    assert issue_deck.strip_issue_prefix("[ÄNDERUNG] x") == "x"


def test_strip_issue_prefix_without_marker() -> None:
    assert issue_deck.strip_issue_prefix("Deck kaputt") == "Deck kaputt"


def test_strip_issue_prefix_only_marker() -> None:
    assert issue_deck.strip_issue_prefix("[Änderung] ") == ""


def test_render_commit_message_uses_title() -> None:
    message = issue_deck.render_commit_message(
        7, "[Änderung] advocō korrigiert", "Erika <42+erika@users.noreply.github.com>"
    )
    lines = message.splitlines()
    assert lines[0] == "advocō korrigiert"
    assert lines[-1] == "Co-authored-by: Erika <42+erika@users.noreply.github.com>"
    assert message.endswith("\n")


def test_render_commit_message_without_coauthor() -> None:
    message = issue_deck.render_commit_message(7, "advocō korrigiert")
    assert "Co-authored-by" not in message


def test_render_commit_message_falls_back_on_empty_title() -> None:
    message = issue_deck.render_commit_message(7, "[Änderung] ")
    assert message.splitlines()[0] == "Deck: Änderungen aus #7"


def test_render_apply_result_failure() -> None:
    body = issue_deck.render_apply_result(
        ok=False,
        changed=False,
        pr_url=None,
        message="issue_deck: boom",
        run_url="https://run",
    )
    assert issue_deck.APPLY_MARKER in body
    assert "boom" in body
    assert "issue_deck:" not in body


def test_render_apply_result_failure_without_message() -> None:
    body = issue_deck.render_apply_result(
        ok=False, changed=False, pr_url=None, message="", run_url="https://run"
    )
    assert "https://run" in body


def test_render_apply_result_unchanged() -> None:
    body = issue_deck.render_apply_result(
        ok=True, changed=False, pr_url=None, message="", run_url="https://run"
    )
    assert "nichts zu übernehmen" in body


def test_render_apply_result_pr() -> None:
    body = issue_deck.render_apply_result(
        ok=True, changed=True, pr_url="https://pr/1", message="", run_url="https://run"
    )
    assert "https://pr/1" in body


def test_render_apply_result_pr_failed() -> None:
    body = issue_deck.render_apply_result(
        ok=True, changed=True, pr_url=None, message="", run_url="https://run"
    )
    assert "fehlgeschlagen" in body
    assert "https://run" in body


def test_artifact_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_gh(monkeypatch, artifact="42")
    url = issue_deck.artifact_url("o/r", "9", "deck-diff")
    assert url == "https://github.com/o/r/actions/runs/9/artifacts/42"


def test_artifact_url_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_gh(monkeypatch, artifact="")
    assert issue_deck.artifact_url("o/r", "9", "deck-diff") is None


def test_post_links_full_diff(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}
    _patch_gh(monkeypatch, artifact="42", capture=captured)
    issue_deck.post(
        code=1,
        diff="x" * (issue_deck.DIFF_LIMIT + 1),
        error="",
        summary="",
        issue=7,
        repo="o/r",
        run_id="9",
    )
    assert "https://github.com/o/r/actions/runs/9/artifacts/42" in captured["body"]


def test_post_short_diff_skips_artifact_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake(command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(" ".join(command))
        if "--paginate" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 0, "https://example/comment", "")

    monkeypatch.setattr(issue_deck, "run", fake)
    issue_deck.post(
        code=1, diff="-x\n+y\n", error="", summary="", issue=7, repo="o/r", run_id="9"
    )
    assert not any("/artifacts" in call for call in calls)


def test_post_updates_existing_comment(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake(command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(" ".join(command))
        if "--paginate" in command:
            return subprocess.CompletedProcess(command, 0, "456", "")
        return subprocess.CompletedProcess(command, 0, "https://example/comment", "")

    monkeypatch.setattr(issue_deck, "run", fake)
    issue_deck.post(
        code=2, diff="", error="boom", summary="", issue=7, repo="o/r", run_id="9"
    )
    assert any("PATCH" in call and "/comments/456" in call for call in calls)


def test_report_apply(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}
    _patch_gh(monkeypatch, capture=captured)
    issue_deck.report_apply(
        7,
        "o/r",
        ok=True,
        changed=True,
        pr_url="https://pr/1",
        message="",
        run_url="https://run",
    )
    assert issue_deck.APPLY_MARKER in captured["body"]
    assert "https://pr/1" in captured["body"]


def test_upsert_comment_creates(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake(command: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(" ".join(command))
        if "--paginate" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 0, "https://c/1", "")

    monkeypatch.setattr(issue_deck, "run", fake)
    url = issue_deck._upsert_comment("o/r", 7, "<!-- m -->", "body")
    assert url == "https://c/1"
    assert any("/issues/7/comments" in call for call in calls)
    assert not any("/issues/comments/7" in call for call in calls)


def test_upsert_comment_raises_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake(command: list[str]) -> subprocess.CompletedProcess[str]:
        if "--paginate" in command:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 1, "", "boom")

    monkeypatch.setattr(issue_deck, "run", fake)
    with pytest.raises(issue_deck.IssueError):
        issue_deck._upsert_comment("o/r", 7, "<!-- m -->", "body")


def test_comment_ids_raises_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, "", "boom")

    monkeypatch.setattr(issue_deck, "run", fake)
    with pytest.raises(issue_deck.IssueError):
        issue_deck._comment_ids("o/r", 7, "<!-- m -->")


def test_parse_diff_without_url(tmp_path: Path) -> None:
    issue_deck.parse_diff("no link", tmp_path)
    assert (tmp_path / "code.txt").read_text().strip() == "2"
    assert "Kein Anhang" in (tmp_path / "error.txt").read_text()


def test_parse_diff_creates_workdir(tmp_path: Path) -> None:
    workdir = tmp_path / "missing" / "out"
    issue_deck.parse_diff("no link", workdir)
    assert (workdir / "code.txt").read_text().strip() == "2"


def test_parse_diff_junk_attachment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(url: str, dest: Path) -> None:
        del url
        dest.write_bytes(b"junk")

    monkeypatch.setattr(issue_deck, "fetch_attachment", fetch)
    issue_deck.parse_diff("https://github.com/user-attachments/x", tmp_path)
    assert (tmp_path / "code.txt").read_text().strip() == "2"
    assert "kein Anki-Deck" in (tmp_path / "error.txt").read_text()


def test_parse_diff_fetch_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fetch(url: str, dest: Path) -> None:
        del url, dest
        raise OSError("boom")

    monkeypatch.setattr(issue_deck, "fetch_attachment", fetch)
    issue_deck.parse_diff("https://github.com/user-attachments/x", tmp_path)
    assert (tmp_path / "code.txt").read_text().strip() == "2"
    assert "konnte nicht geladen" in (tmp_path / "error.txt").read_text()


def test_parse_diff_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_diff(monkeypatch, 0)
    issue_deck.parse_diff("https://github.com/user-attachments/x", tmp_path)
    assert (tmp_path / "code.txt").read_text().strip() == "0"


def test_parse_diff_changed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_diff(monkeypatch, 1, out="-x\n+y\n")
    issue_deck.parse_diff("https://github.com/user-attachments/x", tmp_path)
    assert (tmp_path / "code.txt").read_text().strip() == "1"
    assert "+y" in (tmp_path / "diff.txt").read_text()


def test_parse_diff_tool_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_diff(monkeypatch, 2, err="bad package")
    issue_deck.parse_diff("https://github.com/user-attachments/x", tmp_path)
    assert (tmp_path / "code.txt").read_text().strip() == "2"
    assert "bad package" in (tmp_path / "error.txt").read_text()


def test_parse_apply_changed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_run(
        monkeypatch, diff_code=1, diff_out="```diff\n+x\n```\n", summary_out="| s |\n"
    )
    changed = issue_deck.parse_apply(
        "https://github.com/user-attachments/x", tmp_path, 7
    )
    assert changed is True
    body = (tmp_path / "pr-body.md").read_text()
    assert "Closes #7" in body
    assert "| s |" in body


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


def test_parse_apply_creates_workdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_run(monkeypatch, diff_code=0)
    workdir = tmp_path / "missing" / "change"
    changed = issue_deck.parse_apply(
        "https://github.com/user-attachments/x", workdir, 7
    )
    assert changed is False


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


def test_cli_ack(capsys: pytest.CaptureFixture[str]) -> None:
    assert issue_deck.main(["ack"]) == 0
    assert "Bot" in capsys.readouterr().out


def test_cli_comment(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    diff = tmp_path / "diff.txt"
    error = tmp_path / "error.txt"
    summary = tmp_path / "summary.txt"
    diff.write_text("")
    error.write_text("")
    summary.write_text("")
    assert issue_deck.main(["comment", "0", str(diff), str(error), str(summary)]) == 0
    assert "inhaltsgleich" in capsys.readouterr().out


def test_cli_pr_body(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    diff = tmp_path / "d.md"
    diff.write_text("x")
    assert issue_deck.main(["pr-body", "3", str(diff)]) == 0
    assert "Closes #3" in capsys.readouterr().out


def test_cli_commit_message(capsys: pytest.CaptureFixture[str]) -> None:
    assert issue_deck.main(["commit-message", "3", "[Änderung] x", ""]) == 0
    assert capsys.readouterr().out.splitlines()[0] == "x"


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
    assert issue_deck.main(["parse-diff", str(body), str(tmp_path)]) == 0
    assert (tmp_path / "code.txt").exists()


def test_cli_parse_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(issue_deck, "fetch_attachment", _fake_fetch_apkg)
    _patch_run(monkeypatch, diff_code=1)
    body = tmp_path / "body.txt"
    body.write_text("https://github.com/user-attachments/x")
    assert issue_deck.main(["parse-apply", str(body), str(tmp_path), "7"]) == 0
    assert capsys.readouterr().out.strip() == "true"


def test_cli_post(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_gh(monkeypatch)
    diff = tmp_path / "diff.txt"
    error = tmp_path / "error.txt"
    summary = tmp_path / "summary.txt"
    diff.write_text("")
    error.write_text("")
    summary.write_text("")
    args = ["post", "0", str(diff), str(error), str(summary), "7", "o/r", "9"]
    assert issue_deck.main(args) == 0


def test_cli_report_apply(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_gh(monkeypatch)
    message = tmp_path / "message.txt"
    message.write_text("")
    code = issue_deck.main(
        ["report-apply", "7", "o/r", "true", "false", "-", str(message), "https://run"]
    )
    assert code == 0


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
