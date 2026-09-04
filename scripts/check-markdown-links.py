#!/usr/bin/env python3
"""Report missing local targets in the Markdown link forms used by AgSDL."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote


FENCE_OPEN_RE = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})[ \t]*$")
LINK_DESTINATION_RE = re.compile(
    r"(?<!\\)\]\(\s*(?:<(?P<angle>[^>\n]+)>|(?P<plain>[^)\s]+))"
)
INLINE_CODE_SPAN_RE = re.compile(
    r"(?<!`)(?P<ticks>`+)(?!`).*?(?<!`)(?P=ticks)(?!`)"
)
URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def markdown_files(paths):
    files = set()
    for path in paths:
        if path.is_file():
            if path.suffix.lower() == ".md":
                files.add(path.resolve())
            continue
        if path.is_dir():
            for candidate in path.rglob("*.md"):
                if ".git" not in candidate.parts:
                    files.add(candidate.resolve())
    return sorted(files)


def destinations(source):
    fence_character = None
    fence_length = 0

    with source.open(encoding="utf-8") as markdown:
        for line_number, line in enumerate(markdown, start=1):
            line_without_ending = line.rstrip("\r\n")

            if fence_character is not None:
                closing = FENCE_CLOSE_RE.fullmatch(line_without_ending)
                if closing:
                    marker = closing.group("marker")
                    if marker[0] == fence_character and len(marker) >= fence_length:
                        fence_character = None
                        fence_length = 0
                continue

            opening = FENCE_OPEN_RE.match(line)
            if opening:
                marker = opening.group("marker")
                fence_character = marker[0]
                fence_length = len(marker)
                continue

            searchable_line = INLINE_CODE_SPAN_RE.sub(
                lambda match: " " * len(match.group(0)), line
            )
            for match in LINK_DESTINATION_RE.finditer(searchable_line):
                yield line_number, match.group("angle") or match.group("plain")


def local_path(destination):
    if (
        destination.startswith("#")
        or destination.startswith("//")
        or destination.startswith("/")
        or "(" in destination
        or URI_SCHEME_RE.match(destination)
    ):
        return None

    path_text = re.split(r"[?#]", destination, maxsplit=1)[0]
    if not path_text:
        return None
    return Path(unquote(path_text))


def display_path(source, repository_root):
    try:
        return source.relative_to(repository_root)
    except ValueError:
        return source


def check(paths, repository_root):
    missing = []
    for source in markdown_files(paths):
        for line_number, destination in destinations(source):
            target_path = local_path(destination)
            if target_path is None:
                continue
            resolved = (source.parent / target_path).resolve()
            if not resolved.exists():
                missing.append((source, line_number, destination, resolved))

    for source, line_number, destination, resolved in missing:
        print(
            f"{display_path(source, repository_root)}:{line_number}: "
            f"missing local Markdown target {destination!r} ({resolved})",
            file=sys.stderr,
        )
    return 1 if missing else 0


def main():
    repository_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Markdown files or directories to check; defaults to the repository",
    )
    arguments = parser.parse_args()
    paths = arguments.paths or [repository_root]
    missing_paths = [path for path in paths if not path.exists()]
    if missing_paths:
        for path in missing_paths:
            print(f"Markdown check path does not exist: {path}", file=sys.stderr)
        return 2
    return check(paths, repository_root)


if __name__ == "__main__":
    sys.exit(main())
