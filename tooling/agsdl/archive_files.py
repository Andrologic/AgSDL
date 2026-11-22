"""Find the files needed to move a project between filesystems."""

from contextlib import contextmanager
import os
from pathlib import Path
import re
import stat
import unicodedata
from urllib.parse import unquote, urlsplit

from . import jsoninput
from .project import load_project
from .validator import validate_document


_RESERVED = re.compile(r"^(con|prn|aux|nul|conin\$|conout\$|com[1-9¹²³]|lpt[1-9¹²³])(?:\..*)?$", re.I)
MAX_FILES = 8192
MAX_PATHS = 16384
MAX_JSON = 1024 * 1024
MAX_JSON_TOTAL = 8 * MAX_JSON


def check_portable_name(name: str):
    """Reject paths that are unsafe or ambiguous on common filesystems."""
    if not isinstance(name, str) or not name:
        raise ValueError(f"invalid portable path: {name!r}")
    if len(name.encode("utf-8")) > 4096 or name.count("/") >= 64:
        raise ValueError("portable path exceeds depth or length limit")
    for part in name.split("/"):
        folded = part.casefold()
        if (not part or part in (".", "..") or part[-1] in " ."
                or any(c in '<>:"\\|?*' or unicodedata.category(c).startswith("C") for c in part)
                or len(part.encode("utf-8")) > 255
                or _RESERVED.match(part) or folded in (".git", ".env", ".agsdl-history.bundle")
                or folded.startswith(".env.")):
            raise ValueError(f"invalid portable path: {name!r}")


@contextmanager
def open_portable_file(root: Path, name: str):
    """Open a regular file without following project path symlinks."""
    check_portable_name(name)
    if os.name == "posix":
        # Open every directory relative to its already checked parent.
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        absolute = Path(os.path.abspath(root))
        directory = os.open(absolute.anchor, flags)
        try:
            for part in (*absolute.parts[1:], *name.split("/")[:-1]):
                child = os.open(part, flags, dir_fd=directory)
                os.close(directory)
                directory = child
            fd = os.open(name.split("/")[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=directory)
        finally:
            os.close(directory)
    else:
        # Windows lacks dir_fd/O_NOFOLLOW. Check reparse points before and after
        # opening and compare the opened file with its directory entry.
        root = Path(os.path.abspath(root))
        paths = [*reversed(root.parents), root]
        paths.extend(root.joinpath(*name.split("/")[:i])
                     for i in range(1, len(name.split("/")) + 1))

        def check_paths():
            infos = []
            for index, path in enumerate(paths):
                info = path.lstat()
                if (stat.S_ISLNK(info.st_mode)
                        or getattr(info, "st_file_attributes", 0) & 0x400):
                    raise ValueError(f"reparse point in project: {path}")
                if not (stat.S_ISREG(info.st_mode) if index == len(paths) - 1
                        else stat.S_ISDIR(info.st_mode)):
                    raise ValueError(f"invalid project file: {path}")
                infos.append(info)
            return infos

        before = check_paths()
        fd = os.open(paths[-1], os.O_RDONLY | getattr(os, "O_BINARY", 0))
        try:
            after = check_paths()
            opened = os.fstat(fd)
            if (any(not os.path.samestat(a, b) for a, b in zip(before, after))
                    or not os.path.samestat(after[-1], opened)):
                raise ValueError(f"project file changed while opening: {name}")
        except BaseException:
            os.close(fd)
            raise
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError(f"expected regular file: {name}")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            yield handle
    finally:
        if fd != -1:
            os.close(fd)


def portable_files(project_root: Path, *, modules=None) -> dict:
    """Return declared project files and complete local skill directories."""
    root = Path(project_root)
    if root.is_symlink():
        raise ValueError("project root cannot be a symbolic link")
    root = root.resolve()
    files = {}
    spellings = {}
    walked = set()
    json_total = 0

    def inspect(relative):
        name = relative.as_posix()
        check_portable_name(name)
        key = unicodedata.normalize("NFC", name.casefold())
        previous = spellings.setdefault(key, name)
        if previous != name:
            raise ValueError(f"portable path collision: {previous!r} and {name!r}")
        if len(spellings) > MAX_PATHS:
            raise ValueError("too many project paths")
        path = root / relative
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ValueError(f"symbolic link in project: {name}")
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError(f"special file in project: {name}")
        return path, mode

    def add_file(relative, path):
        files[relative.as_posix()] = path
        if len(files) > MAX_FILES:
            raise ValueError("too many project files")

    def declared(owner, name):
        relative = owner.parent
        if len(name.encode("utf-8")) > 4096 or name.count("/") >= 64:
            raise ValueError("portable path exceeds depth or length limit")
        for part in name.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if relative == Path("."):
                    raise ValueError(f"path outside project: {name!r}")
                relative = relative.parent
                continue
            relative = relative / part
            inspect(relative)
        path, mode = inspect(relative)
        if not stat.S_ISREG(mode):
            raise ValueError(f"expected regular file: {relative}")
        add_file(relative, path)

    def read_json(relative):
        nonlocal json_total
        with open_portable_file(root, relative.as_posix()) as handle:
            data = handle.read(min(MAX_JSON, MAX_JSON_TOTAL - json_total) + 1)
        json_total += len(data)
        if len(data) > MAX_JSON or json_total > MAX_JSON_TOTAL:
            raise ValueError(f"{relative}: project JSON size limit exceeded")
        depth = 0
        quoted = escaped = False
        for byte in data:
            if quoted:
                if escaped:
                    escaped = False
                elif byte == 92:
                    escaped = True
                elif byte == 34:
                    quoted = False
            elif byte == 34:
                quoted = True
            elif byte in (91, 123):
                depth += 1
                if depth > 64:
                    raise ValueError(f"{relative}: project JSON nesting limit exceeded")
            elif byte in (93, 125):
                depth -= 1
        value = jsoninput.parse_bytes(data)
        pending = [value]
        while pending:
            item = pending.pop()
            if isinstance(item, list):
                if len(item) > 1024:
                    raise ValueError(f"{relative}: project JSON array limit exceeded")
                pending.extend(item)
            elif isinstance(item, dict):
                pending.extend(item.values())
        return value

    project = load_project(root, _file_observer=declared, _json_reader=read_json)
    report = validate_document(project.document, modules)
    if not report.valid:
        error = next(item for item in report.diagnostics if item["severity"] == "error")
        raise ValueError(f"{project.location(error['path'])}: {error['message']}")

    def walk(directory):
        if directory in walked:
            return
        walked.add(directory)
        with os.scandir(root / directory) as entries:
            for entry in entries:
                relative = directory / entry.name
                path, mode = inspect(relative)
                if stat.S_ISDIR(mode):
                    walk(relative)
                else:
                    add_file(relative, path)

    for skill in project.document.get("skills", {}).values():
        uri = urlsplit(skill["uri"])
        if uri.scheme:
            continue
        skill_path = Path(unquote(uri.path))
        if skill_path.parent == Path("."):
            raise ValueError("a local skill cannot be rooted at the project root")
        walk(skill_path.parent)
    return files
