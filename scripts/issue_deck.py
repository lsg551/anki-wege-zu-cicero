"""Helpers for the deck issue workflows.

The workflows keep their inline shell minimal and call this module instead, so
the branches that matter (finding an attachment, normalizing it to a package,
rendering a comment) are unit tested.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path
from typing import cast

MARKER = "<!-- anki-tools-diff -->"
APPLY_MARKER = "<!-- anki-tools-apply -->"
DIFF_LIMIT = 60_000

BOT_NOTE = (
    "> [!NOTE]\n"
    "> 🤖 Diese Antwort wurde automatisch erstellt. Ich bin ein Bot und kann "
    "keine Fragen beantworten. Ein Maintainer prüft deinen Vorschlag und "
    "meldet sich."
)

_URL_RE = re.compile(r"https?://[^\s)]+")
_ATTACHMENT_SUFFIX_RE = re.compile(r"\.(?:apkg|zip)$", re.IGNORECASE)


class IssueError(Exception):
    """A failure that stops the workflow with a message."""


class NotAPackageError(IssueError):
    """The attachment is not an Anki package."""


def find_attachment_url(body: str) -> str | None:
    """Return the first attachment URL in *body*, or None.

    GitHub renders an uploaded file as a link to a user-attachments URL whose
    link text carries the file name, so either signal identifies it.
    """
    matches = cast("list[str]", _URL_RE.findall(body))
    for url in matches:
        if "user-attachments" in url or _ATTACHMENT_SUFFIX_RE.search(url):
            return url
    return None


def normalize_attachment(source: Path, dest: Path) -> None:
    """Write the Anki package in *source* to *dest*.

    The workflows ask users to rename the ``.apkg`` to ``.zip``, so *source* is
    usually the package itself. Fall back to a nested ``.apkg`` in case the file
    was compressed instead.

    Raises:
        NotAPackageError: if *source* holds no Anki package.
    """
    if _has_collection(source):
        shutil.copyfile(source, dest)
        return
    try:
        with zipfile.ZipFile(source) as archive:
            members = [m for m in archive.infolist() if _is_apkg_name(m.filename)]
            for member in members:
                data = archive.read(member)
                if _has_collection_bytes(data):
                    dest.write_bytes(data)
                    return
    except (OSError, zipfile.BadZipFile) as exc:
        raise NotAPackageError(str(source)) from exc
    raise NotAPackageError(str(source))


def fetch_attachment(url: str, dest: Path) -> None:
    """Download *url* to *dest*."""
    with urllib.request.urlopen(url, timeout=60) as response:
        dest.write_bytes(response.read())


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run *command* and capture its output as text."""
    return subprocess.run(command, capture_output=True, text=True, check=False)


def diff_against_dump(apkg: Path, diff: Path, error: Path) -> int:
    """Write the ``anki-tools diff`` output for *apkg* to *diff* and *error*."""
    result = run(
        ["anki-tools", "diff", "dump", str(apkg), "--with-deck-configs", "--no-media"]
    )
    diff.write_text(_relabel_diff(result.stdout))
    error.write_text(result.stderr)
    return result.returncode


def render_comment(
    code: int, diff: str, error: str, full_url: str | None = None
) -> str:
    """Return the issue comment body for a comparison result."""
    lines = [MARKER, BOT_NOTE, "", "### Deck-Vorschlag", ""]
    if code == 0:
        lines.append(
            "Der angehängte Export ist inhaltsgleich mit <code>dump/</code> "
            "(keine Änderungen)."
        )
    elif code == 1:
        truncated = len(diff) > DIFF_LIMIT
        lines += [
            "<details><summary>Änderungen gegenüber <code>dump/</code></summary>",
            "",
            "```diff",
            (diff[:DIFF_LIMIT] if truncated else diff).rstrip("\n"),
            "```",
            "",
            "</details>",
        ]
        if truncated:
            lines.append("")
            if full_url is not None:
                lines.append(
                    f"Der Diff ist gekürzt. [Vollständiger Diff als Datei]({full_url})"
                )
            else:
                lines.append("Der Diff ist gekürzt.")
    else:
        lines += [
            "Der Export konnte nicht gelesen werden:",
            "",
            "```",
            error[:4000].rstrip("\n"),
            "```",
            "",
            "Bitte die exportierte <code>.apkg</code>-Datei in <code>.zip</code> "
            "umbenennen und erneut anhängen.",
        ]
    return "\n".join(lines) + "\n"


def render_ack() -> str:
    """Return the comment posted while the comparison runs."""
    note = (
        "> [!NOTE]\n"
        "> 🤖 Danke für deinen Vorschlag. Ich bin ein Bot und vergleiche deine "
        "Datei gerade mit dem Deck im Repository. Das dauert etwa eine "
        "Minute. Danach meldet sich ein Maintainer."
    )
    return f"{MARKER}\n{note}\n"


def render_pr_body(issue: int, diff: str) -> str:
    """Return the pull request body for an applied issue."""
    lines = [
        f"Übernimmt die an #{issue} angehängte `.apkg`-Datei.",
        "",
        f"Closes #{issue}",
        "",
        "<details><summary>Änderungen</summary>",
        "",
    ]
    if len(diff) > DIFF_LIMIT:
        lines += [diff[:DIFF_LIMIT], "", "... gekürzt."]
    else:
        lines.append(diff.rstrip("\n"))
    lines += ["", "</details>"]
    return "\n".join(lines) + "\n"


def parse_diff(body: str, workdir: Path) -> None:
    """Compare an issue attachment with ``dump/`` and write the results.

    Always writes ``code.txt``, ``diff.txt`` and ``error.txt`` in *workdir*, so
    a bad attachment becomes a comment instead of a failed job.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    diff_path = workdir / "diff.txt"
    error_path = workdir / "error.txt"
    diff_path.write_text("")
    url = find_attachment_url(body)
    if url is None:
        error_path.write_text("Kein Anhang gefunden.")
        code = 2
    else:
        attachment = workdir / "attachment"
        apkg = workdir / "issue.apkg"
        try:
            fetch_attachment(url, attachment)
            normalize_attachment(attachment, apkg)
        except NotAPackageError:
            error_path.write_text("Die Datei ist kein Anki-Deck.")
            code = 2
        except OSError as exc:
            error_path.write_text(f"Der Anhang konnte nicht geladen werden: {exc}")
            code = 2
        else:
            code = diff_against_dump(apkg, diff_path, error_path)
    (workdir / "code.txt").write_text(f"{code}\n")


def artifact_url(repo: str, run_id: str, name: str) -> str | None:
    """Return the web URL of artifact *name* of run *run_id*, or None."""
    result = run(
        [
            "gh",
            "api",
            f"repos/{repo}/actions/runs/{run_id}/artifacts",
            "--jq",
            f'.artifacts[] | select(.name == "{name}") | .id',
        ]
    )
    ids = result.stdout.split()
    if not ids:
        return None
    return f"https://github.com/{repo}/actions/runs/{run_id}/artifacts/{ids[0]}"


def post(code: int, diff: str, error: str, issue: int, repo: str, run_id: str) -> None:
    """Post the comparison result, linking the full diff when truncated."""
    full_url = None
    if code == 1 and len(diff) > DIFF_LIMIT:
        full_url = artifact_url(repo, run_id, "deck-diff")
    _upsert_comment(repo, issue, MARKER, render_comment(code, diff, error, full_url))


def render_apply_result(
    *,
    ok: bool,
    changed: bool,
    pr_url: str | None,
    message: str,
    run_url: str,
) -> str:
    """Return the reply to the ``/apply`` command."""
    lines = [APPLY_MARKER, BOT_NOTE, "", "### Übernahme", ""]
    if not ok:
        text = message.strip()
        prefix = "issue_deck: "
        if text.startswith(prefix):
            text = text[len(prefix) :]
        lines += [
            "Ich konnte den Vorschlag nicht übernehmen:",
            "",
            "```",
            (text or f"Details im CI-Lauf: {run_url}")[:4000],
            "```",
        ]
    elif not changed:
        lines.append(
            "Der Vorschlag ist inhaltsgleich mit dem Repository; es gibt "
            "nichts zu übernehmen."
        )
    elif pr_url is not None:
        lines.append(f"Übernommen: {pr_url}")
    else:
        lines.append(f"Die Übernahme ist fehlgeschlagen. Details im CI-Lauf: {run_url}")
    return "\n".join(lines) + "\n"


def report_apply(
    issue: int,
    repo: str,
    *,
    ok: bool,
    changed: bool,
    pr_url: str | None,
    message: str,
    run_url: str,
) -> None:
    """Post the ``/apply`` outcome as an issue comment."""
    body = render_apply_result(
        ok=ok, changed=changed, pr_url=pr_url, message=message, run_url=run_url
    )
    _upsert_comment(repo, issue, APPLY_MARKER, body)


def _comment_ids(repo: str, issue: int, marker: str) -> list[str]:
    """Return the ids of the issue comments that carry *marker*."""
    result = run(
        [
            "gh",
            "api",
            f"repos/{repo}/issues/{issue}/comments",
            "--paginate",
            "--jq",
            f'.[] | select(.body | contains("{marker}")) | .id',
        ]
    )
    if result.returncode != 0:
        raise IssueError(result.stderr.strip() or "could not list comments")
    return result.stdout.split()


def _upsert_comment(repo: str, issue: int, marker: str, body: str) -> str:
    """Create or update the bot comment that carries *marker*."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
        handle.write(body)
        path = Path(handle.name)
    try:
        ids = _comment_ids(repo, issue, marker)
        if ids:
            command = [
                "gh",
                "api",
                "-X",
                "PATCH",
                f"repos/{repo}/issues/comments/{ids[0]}",
                "-F",
                f"body=@{path}",
                "--jq",
                ".html_url",
            ]
        else:
            command = [
                "gh",
                "api",
                f"repos/{repo}/issues/{issue}/comments",
                "-F",
                f"body=@{path}",
                "--jq",
                ".html_url",
            ]
        result = run(command)
        if result.returncode != 0:
            raise IssueError(result.stderr.strip() or "could not post the comment")
        return result.stdout.strip()
    finally:
        path.unlink(missing_ok=True)


def _relabel_diff(text: str) -> str:
    """Replace a unified diff header's input paths with stable labels."""
    lines = text.splitlines(keepends=True)
    for index in range(len(lines) - 1):
        if lines[index].startswith("--- ") and lines[index + 1].startswith("+++ "):
            lines[index] = "--- Repository\n"
            lines[index + 1] = "+++ Vorschlag\n"
            break
    return "".join(lines)


def parse_apply(body: str, workdir: Path, issue: int) -> bool:
    """Turn an issue attachment into a dump and a package in *workdir*.

    Returns:
        Whether the new dump differs from the committed one.

    Raises:
        IssueError: if there is no attachment or anki-tools fails.
    """
    url = find_attachment_url(body)
    if url is None:
        raise IssueError("no attachment link found")
    workdir.mkdir(parents=True, exist_ok=True)
    attachment = workdir / "attachment"
    apkg = workdir / "issue.apkg"
    fetch_attachment(url, attachment)
    normalize_attachment(attachment, apkg)

    dump = workdir / "dump"
    commands = [
        [
            "anki-tools",
            "dump",
            str(apkg),
            "-o",
            str(dump),
            "--with-deck-configs",
            "--no-media",
        ],
        ["anki-tools", "build", str(dump), "-o", str(workdir / "deck.apkg")],
    ]
    for command in commands:
        result = run(command)
        if result.returncode != 0:
            raise IssueError(result.stderr.strip() or "anki-tools failed")

    result = run(["anki-tools", "diff", "dump", str(dump), "-f", "markdown"])
    if result.returncode == 2:
        raise IssueError(result.stderr.strip() or "anki-tools diff failed")
    (workdir / "pr-body.md").write_text(
        render_pr_body(issue, _relabel_diff(result.stdout))
    )
    return result.returncode == 1


def _is_apkg_name(name: str) -> bool:
    """Return whether *name* is an ``.apkg`` file name."""
    return name.lower().endswith(".apkg")


def _has_collection(path: Path) -> bool:
    """Return whether *path* is a zip holding an Anki collection."""
    try:
        with zipfile.ZipFile(path) as archive:
            return _has_collection_names(archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return False


def _has_collection_bytes(data: bytes) -> bool:
    """Return whether *data* is a zip holding an Anki collection."""
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            return _has_collection_names(archive.namelist())
    except zipfile.BadZipFile:
        return False


def _has_collection_names(names: list[str]) -> bool:
    """Return whether any archive member is a collection database."""
    return any(name.startswith("collection.anki") for name in names)


def _read_body(path: str) -> str:
    """Return the issue body from *path*, or stdin for ``-``."""
    if path == "-":
        return cast("str", sys.stdin.read())
    return Path(path).read_text()


def _cmd_url(args: argparse.Namespace) -> int:
    """Print the attachment URL, or return 1 when there is none."""
    url = find_attachment_url(_read_body(args.body))
    if url is None:
        return 1
    print(url)
    return 0


def _cmd_normalize(args: argparse.Namespace) -> int:
    """Write an ``.apkg`` from an attachment."""
    normalize_attachment(args.source, args.dest)
    return 0


def _cmd_comment(args: argparse.Namespace) -> int:
    """Print the issue comment body."""
    print(
        render_comment(args.code, args.diff.read_text(), args.error.read_text()),
        end="",
    )
    return 0


def _cmd_pr_body(args: argparse.Namespace) -> int:
    """Print the pull request body."""
    print(render_pr_body(args.issue, args.diff.read_text()), end="")
    return 0


def _cmd_parse_diff(args: argparse.Namespace) -> int:
    """Compare the attachment with ``dump/`` and write the results."""
    parse_diff(_read_body(args.body), args.workdir)
    return 0


def _cmd_ack(_args: argparse.Namespace) -> int:
    """Print the comment posted while the comparison runs."""
    print(render_ack(), end="")
    return 0


def _cmd_post(args: argparse.Namespace) -> int:
    """Post the comparison result as an issue comment."""
    post(
        args.code,
        args.diff.read_text(),
        args.error.read_text(),
        args.issue,
        args.repo,
        args.run_id,
    )
    return 0


def _cmd_report_apply(args: argparse.Namespace) -> int:
    """Post the ``/apply`` outcome as an issue comment."""
    message = ""
    if args.message != "-":
        path = Path(args.message)
        if path.is_file():
            message = path.read_text()
    report_apply(
        args.issue,
        args.repo,
        ok=args.ok == "true",
        changed=args.changed == "true",
        pr_url=None if args.pr_url == "-" else args.pr_url,
        message=message,
        run_url=args.run_url,
    )
    return 0


def _cmd_parse_apply(args: argparse.Namespace) -> int:
    """Turn the attachment into a dump and print whether it changed."""
    changed = parse_apply(_read_body(args.body), args.workdir, args.issue)
    print("true" if changed else "false")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser."""
    parser = argparse.ArgumentParser(prog="issue_deck", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    url = subparsers.add_parser("url", help="print the attachment URL")
    url.add_argument("body", help='body file ("-" for stdin)')
    url.set_defaults(func=_cmd_url)

    ack = subparsers.add_parser("ack", help="print the working comment")
    ack.set_defaults(func=_cmd_ack)

    normalize = subparsers.add_parser(
        "normalize", help="write an .apkg from an attachment"
    )
    normalize.add_argument("source", type=Path)
    normalize.add_argument("dest", type=Path)
    normalize.set_defaults(func=_cmd_normalize)

    comment = subparsers.add_parser("comment", help="print the issue comment")
    comment.add_argument("code", type=int)
    comment.add_argument("diff", type=Path)
    comment.add_argument("error", type=Path)
    comment.set_defaults(func=_cmd_comment)

    pr_body = subparsers.add_parser("pr-body", help="print the pull request body")
    pr_body.add_argument("issue", type=int)
    pr_body.add_argument("diff", type=Path)
    pr_body.set_defaults(func=_cmd_pr_body)

    parse_diff = subparsers.add_parser(
        "parse-diff", help="compare an issue attachment with dump/"
    )
    parse_diff.add_argument("body", help='body file ("-" for stdin)')
    parse_diff.add_argument("workdir", type=Path)
    parse_diff.set_defaults(func=_cmd_parse_diff)

    parse_apply = subparsers.add_parser(
        "parse-apply", help="turn an issue attachment into a dump"
    )
    parse_apply.add_argument("body", help='body file ("-" for stdin)')
    parse_apply.add_argument("workdir", type=Path)
    parse_apply.add_argument("issue", type=int)
    parse_apply.set_defaults(func=_cmd_parse_apply)

    post = subparsers.add_parser("post", help="post the comparison comment")
    post.add_argument("code", type=int)
    post.add_argument("diff", type=Path)
    post.add_argument("error", type=Path)
    post.add_argument("issue", type=int)
    post.add_argument("repo")
    post.add_argument("run_id")
    post.set_defaults(func=_cmd_post)

    report_apply = subparsers.add_parser("report-apply", help="post the /apply outcome")
    report_apply.add_argument("issue", type=int)
    report_apply.add_argument("repo")
    report_apply.add_argument("ok")
    report_apply.add_argument("changed")
    report_apply.add_argument("pr_url")
    report_apply.add_argument("message", help='message file ("-" for none)')
    report_apply.add_argument("run_url")
    report_apply.set_defaults(func=_cmd_report_apply)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface and return an exit code."""
    args = _build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (IssueError, OSError) as exc:
        print(f"issue_deck: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
