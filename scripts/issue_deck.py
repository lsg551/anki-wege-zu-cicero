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
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path
from typing import cast

MARKER = "<!-- anki-tools-diff -->"
DIFF_LIMIT = 60_000

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
    diff.write_text(result.stdout)
    error.write_text(result.stderr)
    return result.returncode


def render_comment(code: int, diff: str, error: str, run_url: str) -> str:
    """Return the issue comment body for a comparison result."""
    lines = [MARKER, "### Deck-Vorschlag", ""]
    if code == 0:
        lines.append(
            "Der angehängte Export ist inhaltsgleich mit <code>dump/</code> "
            "(keine Änderungen)."
        )
    elif code == 1:
        lines += [
            "<details><summary>Änderungen gegenüber <code>dump/</code></summary>",
            "",
            "```diff",
        ]
        if len(diff) > DIFF_LIMIT:
            lines += [
                diff[:DIFF_LIMIT],
                "",
                f"... gekürzt, vollständiger Diff: {run_url}",
            ]
        else:
            lines.append(diff.rstrip("\n"))
        lines += ["```", "", "</details>"]
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


def parse_diff(body: str, workdir: Path, run_url: str) -> None:
    """Compare an issue attachment with ``dump/`` and write the comment.

    Always writes ``code.txt``, ``diff.txt``, ``error.txt`` and ``body.md`` in
    *workdir*, so a bad attachment becomes a comment instead of a failed job.
    """
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
    (workdir / "body.md").write_text(
        render_comment(code, diff_path.read_text(), error_path.read_text(), run_url)
    )


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
    (workdir / "pr-body.md").write_text(render_pr_body(issue, result.stdout))
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
        render_comment(
            args.code, args.diff.read_text(), args.error.read_text(), args.run_url
        ),
        end="",
    )
    return 0


def _cmd_pr_body(args: argparse.Namespace) -> int:
    """Print the pull request body."""
    print(render_pr_body(args.issue, args.diff.read_text()), end="")
    return 0


def _cmd_parse_diff(args: argparse.Namespace) -> int:
    """Compare the attachment with ``dump/`` and write the results."""
    parse_diff(_read_body(args.body), args.workdir, args.run_url)
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
    comment.add_argument("run_url")
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
    parse_diff.add_argument("run_url")
    parse_diff.set_defaults(func=_cmd_parse_diff)

    parse_apply = subparsers.add_parser(
        "parse-apply", help="turn an issue attachment into a dump"
    )
    parse_apply.add_argument("body", help='body file ("-" for stdin)')
    parse_apply.add_argument("workdir", type=Path)
    parse_apply.add_argument("issue", type=int)
    parse_apply.set_defaults(func=_cmd_parse_apply)

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
