"""Pack, inspect and unpack portable AgSDL projects; optionally record Git versions."""

import argparse
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import sys
import tempfile
import unicodedata
import zipfile
import zlib

from . import jsoninput
from .archive_files import check_portable_name, discover_project, open_portable_file, portable_files
from .archive_history import record_version, verify_history
from .archive_publish import publish_new
from .archive_zip import member_ends, read_member
from .project import ProjectError
from .schemacheck import SchemaChecker
from .validator import SCHEMA_DIR

FORMAT = "agsdl-archive-1"
SCHEMA = SchemaChecker(jsoninput.load(Path(SCHEMA_DIR) / "archive.schema.json"))
MAX_ENTRIES = 8192
MAX_TOTAL = 256 * 1024 * 1024
MAX_INDEX = 2 * 1024 * 1024
MAX_DIRECTORY = 8 * 1024 * 1024
HISTORY_FILE = ".agsdl-history.bundle"
NATIVE_EXECUTABLE_BITS = os.name != "nt"
MODE_SIDECAR = ".agsdl-executables"
MODE_HEADER = b"AgSDL executable paths v1\n"


def mode_sidecar(files):
    """Find a root-level name outside the project's declared paths."""
    roots = {name.partition("/")[0].casefold() for name in files}
    name = MODE_SIDECAR
    suffix = 0
    while name in roots:
        suffix += 1
        name = f"{MODE_SIDECAR}.{suffix}"
    return name


def restored_executables(project, files):
    if NATIVE_EXECUTABLE_BITS:
        return set()
    # An edit can free (or claim) the original sidecar's preferred filename.
    # Read only root-level metadata outside the project's current selection.
    selected = {name.casefold() for name in files}
    with os.scandir(project) as entries:
        for entry in entries:
            name = entry.name
            prefix = MODE_SIDECAR
            if name != prefix:
                suffix = name[len(prefix) + 1:]
                if not name.startswith(prefix + ".") or not (suffix.isascii() and suffix.isdecimal()):
                    continue
            if name.casefold() in selected or not entry.is_file(follow_symlinks=False):
                continue
            with open_portable_file(project, name) as source:
                if source.read(len(MODE_HEADER)) != MODE_HEADER:
                    continue
                raw = source.read(MAX_INDEX + 1)
            if len(raw) > MAX_INDEX:
                raise ValueError(f"{name}: executable metadata exceeds the size limit")
            return set(raw.decode("utf-8").split("\n")).intersection(files)
    return set()


def copy_and_hash(source, target, limit):
    digest = hashlib.sha256()
    size = 0
    while True:
        block = source.read(1024 * 1024)
        if not block:
            break
        size += len(block)
        if size > limit:
            raise ValueError("archive exceeds its size limit")
        digest.update(block)
        target.write(block)
    return {"size": size, "sha256": digest.hexdigest()}


def copy_file(source, dest, limit):
    dest.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    if source.is_symlink():
        raise ValueError(f"expected a regular file: {source}")
    with os.fdopen(os.open(source, flags), "rb") as input_file:
        info = os.fstat(input_file.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError(f"expected a bounded regular file: {source}")
        with dest.open("xb") as output_file:
            return copy_and_hash(input_file, output_file, limit)


def stage_snapshot(project, snapshot):
    """Freeze the declared bytes once, then validate that exact copy."""
    snapshot.mkdir()
    assembled, files = discover_project(project, validate=False)
    project = assembled.root
    if len(files) + 1 > MAX_ENTRIES:
        raise ValueError("too many project files")
    total = 0
    inventory = {}
    remembered = restored_executables(project, files)
    for name in sorted(files):
        target = snapshot / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with open_portable_file(project, name) as source, target.open("xb") as dest:
            entry = copy_and_hash(source, dest, MAX_TOTAL - total)
            entry["executable"] = (name in remembered or
                                   bool(os.fstat(source.fileno()).st_mode & 0o111))
        total += entry["size"]
        target.chmod(0o755 if entry["executable"] else 0o644)
        inventory[name] = entry
    if portable_files(snapshot).keys() != inventory.keys():
        raise ValueError("project dependencies changed during export")
    return inventory


def write_member(archive, name, source):
    info = zipfile.ZipInfo(name)  # ZIP epoch, independent of the source clock.
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    with archive.open(info, "w") as dest:
        shutil.copyfileobj(source, dest)


def pack(project, output, history=None):
    if output.suffix != ".agsdl":
        raise ValueError("archive output must end in .agsdl")
    if os.path.lexists(output):
        raise FileExistsError(f"destination exists: {output}")
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        snapshot = work / "project"
        files = stage_snapshot(project, snapshot)
        index = {"archiveFormat": FORMAT, "files": files}
        payload = {f"project/{name}": snapshot / name for name in files}
        total = sum(entry["size"] for entry in files.values())
        if history is not None:
            bundle = work / "history.bundle"
            info = copy_file(history, bundle, MAX_TOTAL - total)
            info["commit"] = verify_history(bundle, snapshot, executables={
                name for name, row in files.items() if row["executable"]})
            index["history"] = info
            total += info["size"]
            payload["history.bundle"] = bundle
        raw = (json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if len(raw) > MAX_INDEX or total + len(raw) > MAX_TOTAL or len(payload) + 1 > MAX_ENTRIES:
            raise ValueError("archive inventory exceeds format limits")
        (work / "archive.json").write_bytes(raw)
        payload["archive.json"] = work / "archive.json"
        # Publish a complete file, without overwriting a concurrent export.
        with tempfile.TemporaryDirectory(dir=output.parent) as spool:
            tmp = Path(spool) / "packed"
            with zipfile.ZipFile(tmp, "w", allowZip64=False) as archive:
                for name, path in sorted(payload.items()):
                    with path.open("rb") as source:
                        write_member(archive, name, source)
            with tmp.open("rb") as handle:
                preflight(handle)
            tmp.chmod(0o600)
            publish_new(tmp, output)


def preflight(handle):
    """Bound the central directory before ZipFile allocates an object per entry."""
    size = handle.seek(0, os.SEEK_END)
    if size < 22 or size > 2 * MAX_TOTAL:
        raise ValueError("invalid archive size")
    handle.seek(-22, os.SEEK_END)
    signature, disk, start, count, entries, length, offset, comment = struct.unpack(
        "<4s4H2IH", handle.read(22))
    if (signature != b"PK\x05\x06" or disk or start or comment or count != entries
            or not 1 <= entries <= MAX_ENTRIES or length > MAX_DIRECTORY
            or offset + length != size - 22):
        raise ValueError("expected a single-volume ZIP32 archive with a bounded directory")
    # ZipFile checks for a ZIP64 locator just before the footer even when the
    # ordinary footer has usable fields. Both readers must use the same bounds.
    if size >= 42:
        handle.seek(size - 42)
        if handle.read(4) == b"PK\x06\x07":
            raise ValueError("ZIP64 archives are outside format 1")
    handle.seek(offset)
    end = offset + length
    for _ in range(entries):
        header = handle.read(46)
        if len(header) != 46 or header[:4] != b"PK\x01\x02":
            raise ValueError("invalid ZIP directory entry count")
        name_len, extra_len, comment_len = struct.unpack_from("<3H", header, 28)
        handle.seek(name_len + extra_len + comment_len, os.SEEK_CUR)
        if handle.tell() > end:
            raise ValueError("truncated ZIP directory")
    if handle.tell() != end:
        raise ValueError("unexpected ZIP directory data")
    return entries


def members(archive, expected_count):
    infos = archive.infolist()
    if len(infos) != expected_count or sum(i.file_size for i in infos) > MAX_TOTAL:
        raise ValueError("ZIP contents exceed the declared limits")
    by_name = {}
    for info in infos:
        name = info.orig_filename
        if (name != info.filename or name in by_name or info.flag_bits & 1
                or (not name.isascii() and not info.flag_bits & 0x800)
                or info.compress_type not in (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED)
                or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)
                or info.external_attr & 0x10):
            raise ValueError(f"invalid ZIP entry: {name!r}")
        if name.startswith("project/"):
            path = name[len("project/"):]
            check_portable_name(path)
        elif name not in ("archive.json", "history.bundle"):
            raise ValueError(f"unknown ZIP entry: {name!r}")
        by_name[name] = info
    return by_name


def extract(archive_path, work, check_history=False, modules=None):
    index, _ = _extract_project(archive_path, work, check_history, modules)
    return index


def _extract_project(archive_path, work, check_history=False, modules=None):
    snapshot = work / "project"
    snapshot.mkdir(mode=0o700)
    with archive_path.open("rb") as handle:
        count = preflight(handle)
        with zipfile.ZipFile(handle) as archive:
            table = members(archive, count)
            if "archive.json" not in table or table["archive.json"].file_size > MAX_INDEX:
                raise ValueError("missing or oversized archive.json")
            ends = member_ends(archive)
            raw = io.BytesIO()
            info = table.pop("archive.json")
            read_member(archive, info, raw, ends[info.header_offset])
            index = jsoninput.parse_bytes(raw.getvalue())
            problems = SCHEMA.check(index)
            if problems:
                where, message = problems[0]
                raise ValueError(f"archive.json#{where}: {message}")
            files = index["files"]
            declared = {f"project/{name}": entry for name, entry in files.items()}
            if "history" in index:
                declared["history.bundle"] = index["history"]
            if declared.keys() != table.keys() or "agsdl.json" not in files:
                raise ValueError("inventory and ZIP entries do not match")
            check_tree_names(files)
            for name, entry in declared.items():
                info = table[name]
                if info.file_size != entry["size"]:
                    raise ValueError(f"incorrect size: {name}")
                # JSON Schema also accepts integral decimals (e.g. 1.0).
                entry["size"] = info.file_size
                dest = work / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open("xb") as target:
                    actual = read_member(archive, info, target, ends[info.header_offset])
                if actual["sha256"] != entry["sha256"] or actual["size"] != entry["size"]:
                    raise ValueError(f"incorrect file contents: {name}")
                if name == "history.bundle":
                    dest.chmod(0o600)
                else:
                    dest.chmod(0o755 if entry["executable"] else 0o644)
    project, selected = discover_project(snapshot, modules=modules)
    if selected.keys() != files.keys():
        raise ValueError("inventory includes files outside the declared project")
    if check_history:
        if "history" not in index:
            raise ValueError("archive contains no Git history")
        verify_history(work / "history.bundle", snapshot, index["history"]["commit"],
                       executables={name for name, row in files.items() if row["executable"]})
    return index, project


def check_tree_names(files):
    """Reject file/directory conflicts and aliases before writing project files."""
    spellings = {}
    for name in files:
        current = []
        for part in name.split("/"):
            current.append(part)
            path = "/".join(current)
            key = unicodedata.normalize("NFC", path.casefold())
            if spellings.setdefault(key, path) != path:
                raise ValueError(f"case collision: {path}")
            if len(spellings) > 16384:
                raise ValueError("too many project paths")
            if path != name and path in files:
                raise ValueError(f"file used as directory: {path}")


@contextmanager
def open_archive(path, modules=None):
    """Keep the verified project's root alive while a consumer reads it."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        try:
            _, project = _extract_project(path, work, modules=modules)
        except (ValueError, jsoninput.InputError, zipfile.BadZipFile, zlib.error, EOFError, RecursionError) as error:
            raise ProjectError(str(error)) from None
        yield project


def inspect_archive(path):
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        index, project = _extract_project(path, work)
        servers = project.document.get("mcpServers", {})
        inventory_bytes = json.dumps(index["files"], ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")
        return {
            "contentSha256": hashlib.sha256(inventory_bytes).hexdigest(),
            "project": project.document["id"],
            "inventory": index,
            "requiredSecrets": project.secrets,
            "mcpPrograms": {key: server["command"][0] for key, server in servers.items() if "command" in server},
            "remoteMcpServers": {key: server["url"] for key, server in servers.items() if "url" in server},
        }


def unpack(path, destination, with_history=False):
    if os.path.lexists(destination):
        raise FileExistsError(f"destination exists: {destination}")
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        work = Path(tmp)
        index = extract(path, work, with_history)
        project = work / "project"
        if not NATIVE_EXECUTABLE_BITS:
            files = index["files"]
            executable = sorted(name for name, row in files.items() if row["executable"])
            if executable:
                with (project / mode_sidecar(files)).open("xb") as sidecar:
                    sidecar.write(MODE_HEADER + "\n".join(executable).encode("utf-8"))
        if with_history:
            (work / "history.bundle").rename(project / HISTORY_FILE)
        if os.name == "nt":
            # Windows rename refuses an existing destination.
            project.rename(destination)
        else:
            # Reserve the name exclusively before replacing our own empty directory.
            destination.mkdir(mode=0o700)
            try:
                project.replace(destination)
            except OSError:
                destination.rmdir()
                raise


def check_store_location(project, store):
    root = project.resolve()
    path = store.resolve()
    if path.is_relative_to(root) and path != root / HISTORY_FILE:
        raise ValueError(f"keep the version store outside the project or use {HISTORY_FILE} at its root")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agsdl.archive", description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    export = sub.add_parser("pack", help="export the declared project files")
    export.add_argument("project", type=Path)
    export.add_argument("output", type=Path)
    export.add_argument("--history", type=Path, help="include a matching project version bundle")
    show = sub.add_parser("inspect", help="verify the snapshot and print its inventory")
    show.add_argument("archive", type=Path)
    imp = sub.add_parser("unpack", help="restore a project into a new directory")
    imp.add_argument("archive", type=Path)
    imp.add_argument("destination", type=Path)
    imp.add_argument("--with-history", action="store_true", help="verify and keep the Git bundle")
    version = sub.add_parser("version", help="record the project's portable files as a Git version")
    version.add_argument("project", type=Path)
    version.add_argument("store", type=Path, help="dedicated project history bundle")
    version.add_argument("-m", "--message", required=True)
    version.add_argument("--parent", help="base the version on an earlier commit in the store")
    version.add_argument("--fork", type=Path, help="new bundle for a version based on --parent")
    args = parser.parse_args(argv)
    try:
        if args.action == "pack":
            pack(args.project, args.output, args.history)
        elif args.action == "inspect":
            print(json.dumps(inspect_archive(args.archive), indent=2, ensure_ascii=False))
        elif args.action == "unpack":
            unpack(args.archive, args.destination, args.with_history)
        else:
            check_store_location(args.project, args.store)
            if args.fork is not None:
                check_store_location(args.project, args.fork)
            with tempfile.TemporaryDirectory() as tmp:
                snapshot = Path(tmp) / "project"
                files = stage_snapshot(args.project, snapshot)
                if (args.parent is None) != (args.fork is None):
                    raise ValueError("use --parent and --fork together to preserve the original history")
                commit = record_version(snapshot, args.store, args.message, args.parent,
                                        fork=args.fork, executables={
                                            name for name, row in files.items() if row["executable"]})
                print(commit)
    except (ValueError, OSError, jsoninput.InputError, zipfile.BadZipFile, zlib.error, EOFError, RecursionError) as error:
        print(f"agsdl.archive: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
