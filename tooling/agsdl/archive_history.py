"""Store private project snapshots in a self-contained Git bundle."""

import os
import signal
import shutil
import struct
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import threading
import time


_REF = "refs/heads/versions"
_OID = re.compile(r"[0-9a-f]{40}\Z")
_MAX_BUNDLE = 64 * 1024 * 1024
_MAX_EXPANDED = 128 * 1024 * 1024
_MAX_OBJECTS = 10000
_MAX_OUTPUT = 128 * 1024 * 1024
_MAX_STREAM = 2 * 1024 * 1024
_MAX_MEMORY = 512 * 1024 * 1024
_MAX_SECONDS = 60


# Apply limits in a fresh interpreter, avoiding preexec_fn in a threaded host.
_LIMIT_EXEC = """import os, resource, sys
for name, value in ((resource.RLIMIT_AS, int(sys.argv[1])),
                    (resource.RLIMIT_FSIZE, int(sys.argv[2])),
                    (resource.RLIMIT_CPU, int(sys.argv[3]))):
    soft, hard = resource.getrlimit(name)
    limit = min(value, hard) if hard != resource.RLIM_INFINITY else value
    resource.setrlimit(name, (limit, limit))
os.execvp('git', ['git'] + sys.argv[4:])
"""


class _Repository:
    def __init__(self, directory, deadline=None):
        if shutil.which("git") is None:
            raise ValueError("Git is required to record or verify project history")
        self.deadline = deadline or time.monotonic() + _MAX_SECONDS
        self.directory = Path(directory)
        self.path = Path(directory) / "repo.git"
        self.env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR")
                    if key in os.environ}
        self.env.update({"HOME": directory, "XDG_CONFIG_HOME": directory,
                         "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
                         "GIT_AUTHOR_NAME": "AgSDL Archive",
                         "GIT_AUTHOR_EMAIL": "archive@invalid",
                         "GIT_COMMITTER_NAME": "AgSDL Archive",
                         "GIT_COMMITTER_EMAIL": "archive@invalid"})
        self.run("init", "--bare", "--object-format=sha1", "--template=", str(self.path), repo=False)

    def run(self, *args, data=None, repo=True):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Git history operation exceeded its time limit")
        git_args = (["--git-dir", str(self.path)] if repo else []) + list(args)
        if os.name == "posix":
            command = ([sys.executable, "-I", "-c", _LIMIT_EXEC, str(_MAX_MEMORY),
                        str(_MAX_OUTPUT), str(_MAX_SECONDS)] + git_args)
        else:
            command = ["git"] + git_args
        process = subprocess.Popen(command, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env,
                                   start_new_session=(os.name == "posix"))
        output = [bytearray(), bytearray()]
        exceeded = threading.Event()

        def stop():
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass

        def read_stream(stream, buffer):
            try:
                while True:
                    chunk = os.read(stream.fileno(), 65536)
                    if not chunk:
                        break
                    if len(buffer) + len(chunk) > _MAX_STREAM:
                        exceeded.set()
                        stop()
                        break
                    buffer.extend(chunk)
            finally:
                stream.close()

        def write_input():
            try:
                process.stdin.write(data)
            except (BrokenPipeError, OSError):
                pass
            finally:
                try:
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass

        readers = [threading.Thread(target=read_stream, args=(stream, buffer), daemon=True)
                   for stream, buffer in zip((process.stdout, process.stderr), output)]
        for thread in readers:
            thread.start()
        writer = None
        if data is not None:
            writer = threading.Thread(target=write_input, daemon=True)
            writer.start()
        try:
            process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            stop()
            process.wait()
            raise ValueError("Git history operation exceeded its time limit") from None
        finally:
            # Descendants can inherit pipes; never wait beyond the operation deadline.
            for thread in readers + ([writer] if writer else []):
                thread.join(max(0, self.deadline - time.monotonic()))
        if any(thread.is_alive() for thread in readers):
            stop()
            raise ValueError("Git history operation exceeded its time limit")
        if exceeded.is_set():
            raise ValueError("Git output exceeds the size limit")
        if process.returncode:
            detail = bytes(output[1][:4096]).decode("utf-8", "replace").strip()
            raise ValueError("Git {} failed: {}".format(args[0], detail))
        return bytes(output[0])

    def load(self, bundle):
        # Copy once so validation and Git see the same regular file.
        copy = self.directory / "input.bundle"
        if not stat.S_ISREG(bundle.lstat().st_mode):
            raise ValueError("history bundle must be a regular file within the size limit")
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(str(bundle), flags)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_BUNDLE:
            os.close(fd)
            raise ValueError("history bundle must be a regular file within the size limit")
        with os.fdopen(fd, "rb") as source, copy.open("wb") as target:
            copied = 0
            while True:
                chunk = source.read(min(1024 * 1024, _MAX_BUNDLE + 1 - copied))
                if not chunk:
                    break
                copied += len(chunk)
                if copied > _MAX_BUNDLE:
                    raise ValueError("history bundle exceeds the size limit")
                target.write(chunk)
        with copy.open("rb") as source:
            header = source.readline(128)
            reference = source.readline(128)
            blank = source.readline(2)
            if header != b"# v2 git bundle\n" or blank != b"\n":
                raise ValueError("history must be a standalone v2 SHA-1 bundle with one reference")
            match = re.fullmatch(rb"([0-9a-f]{40}) refs/heads/versions\n", reference)
            if not match:
                raise ValueError("history bundle must contain only refs/heads/versions")
            tip = match.group(1).decode("ascii")
            pack = source.read(12)
            if len(pack) != 12:
                raise ValueError("history bundle has an incomplete pack")
            signature, version, count = struct.unpack(">4sII", pack)
            if signature != b"PACK" or version not in (2, 3) or count > _MAX_OBJECTS:
                raise ValueError("history bundle has an invalid or oversized pack")
        self.run("bundle", "verify", str(copy))
        self.run("bundle", "unbundle", str(copy))
        if self.run("cat-file", "-t", tip).strip() != b"commit":
            raise ValueError("history tip must be a commit")
        objects = self.run("cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objectsize)")
        total = 0
        lines = objects.splitlines()
        if len(lines) != count:
            raise ValueError("history bundle has duplicate or missing objects")
        for line in lines:
            try:
                oid, size = line.split()
                total += int(size)
                if len(oid) != 40 or total > _MAX_EXPANDED:
                    raise ValueError
            except ValueError:
                raise ValueError("history objects exceed the expansion limit or are invalid") from None
        unreachable = self.run("fsck", "--strict", "--unreachable", "--no-reflogs", tip)
        if unreachable.strip():
            raise ValueError("history bundle contains unreachable objects")
        self.run("update-ref", _REF, tip)
        return tip

    def select(self, tip, requested):
        if requested is None:
            return tip
        _check_oid(requested)
        self.run("cat-file", "-e", requested + "^{commit}")
        self.run("merge-base", "--is-ancestor", requested, tip)
        return requested

    def tree(self, snapshot, executables=None):
        snapshot = Path(snapshot)
        if not snapshot.is_dir() or snapshot.is_symlink():
            raise ValueError("snapshot must be a directory")
        entries = bytearray()
        total = 0
        count = 0
        batch = []
        batch_length = 0

        def add_batch():
            if not batch:
                return
            result = self.run("hash-object", "-w", "--no-filters", "--",
                              *(str(path) for path, _, _ in batch)).splitlines()
            if len(result) != len(batch) or any(not re.fullmatch(rb"[0-9a-f]{40}", oid) for oid in result):
                raise ValueError("Git returned invalid snapshot object IDs")
            for (_, relative, executable), oid in zip(batch, result):
                entries.extend((b"100755" if executable else b"100644") + b" " + oid + b"\t" + relative + b"\0")
            batch.clear()

        for root, dirs, files in os.walk(snapshot, followlinks=False):
            dirs.sort()
            files.sort()
            for name in dirs:
                path = Path(root) / name
                if not stat.S_ISDIR(path.lstat().st_mode):
                    raise ValueError("snapshot contains a non-directory: {}".format(path))
            for name in files:
                path = Path(root) / name
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("snapshot contains a non-regular file: {}".format(path))
                count += 1
                total += info.st_size
                if count > _MAX_OBJECTS or total > _MAX_EXPANDED:
                    raise ValueError("snapshot exceeds the file count or size limit")
                relative = os.fsencode(path.relative_to(snapshot).as_posix())
                executable = bool(info.st_mode & 0o111) if executables is None else os.fsdecode(relative) in executables
                if len(entries) + batch_length + len(relative) > _MAX_OUTPUT - 64:
                    raise ValueError("snapshot paths exceed the size limit")
                # Keep Windows command lines below its 32767 UTF-16 unit limit.
                path_length = len(str(path).encode("utf-16-le")) // 2 + 3
                if path_length > 16000:
                    raise ValueError("snapshot path exceeds the Git command limit")
                if batch and (len(batch) >= 128 or batch_length + path_length > 16000):
                    add_batch()
                    batch_length = 0
                batch.append((path, relative, executable))
                batch_length += path_length
        add_batch()
        if entries:
            self.run("update-index", "-z", "--index-info", data=bytes(entries))
        return self.run("write-tree").strip().decode("ascii")


def _check_oid(value):
    if not isinstance(value, str) or not _OID.fullmatch(value):
        raise ValueError("commit ID must be a full lowercase SHA-1 hex string")


def _paths(snapshot, bundle):
    snapshot, bundle = Path(snapshot).absolute(), Path(bundle).absolute()
    try:
        bundle.resolve().relative_to(snapshot.resolve())
    except ValueError:
        return snapshot, bundle
    raise ValueError("history bundle must be outside the snapshot")


def record_version(snapshot: Path, bundle: Path, message: str, parent=None) -> str:
    """Append a snapshot, optionally branching from a reachable commit."""
    snapshot, bundle = _paths(snapshot, bundle)
    if not isinstance(message, str) or not message.strip() or "\0" in message:
        raise ValueError("commit message must be a nonempty string without NUL")
    if len(message.encode("utf-8")) > _MAX_EXPANDED:
        raise ValueError("commit message exceeds the size limit")
    if parent is not None:
        _check_oid(parent)
    lock = bundle.with_name(bundle.name + ".lock")
    fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with tempfile.TemporaryDirectory(prefix="agsdl-history-") as temp:
            repo = _Repository(temp)
            if bundle.exists():
                tip = repo.load(bundle)
                chosen = repo.select(tip, parent)
            else:
                if parent is not None:
                    raise ValueError("parent requires an existing history bundle")
                chosen = None
            tree = repo.tree(snapshot)
            args = ["commit-tree", tree]
            if chosen:
                args.extend(["-p", chosen])
            commit = repo.run(*args, data=message.encode("utf-8")).strip().decode("ascii")
            repo.run("update-ref", _REF, commit)
            # Create beside the destination so replacement is atomic on its filesystem.
            with tempfile.NamedTemporaryFile(prefix=".agsdl-history-", dir=str(bundle.parent), delete=False) as out:
                temporary = Path(out.name)
            try:
                repo.run("bundle", "create", "--version=2", str(temporary), _REF)
                validation_dir = Path(temp) / "validation"
                validation_dir.mkdir()
                validated = _Repository(str(validation_dir), repo.deadline).load(temporary)
                if validated != commit:
                    raise ValueError("generated history bundle has an unexpected tip")
                os.replace(str(temporary), str(bundle))
            finally:
                temporary.unlink(missing_ok=True)
            return commit
    finally:
        lock.unlink(missing_ok=True)


def verify_history(bundle: Path, snapshot: Path, expected=None, *, executables=None) -> str:
    """Verify a selected reachable commit against a private snapshot."""
    snapshot, bundle = _paths(snapshot, bundle)
    if expected is not None:
        _check_oid(expected)
    with tempfile.TemporaryDirectory(prefix="agsdl-history-") as temp:
        repo = _Repository(temp)
        selected = repo.load(bundle)
        if expected is not None and selected != expected:
            raise ValueError("archive commit must match the history tip")
        actual = repo.tree(snapshot, executables)
        recorded = repo.run("rev-parse", selected + "^{tree}").strip().decode("ascii")
        if actual != recorded:
            raise ValueError("history tree does not match snapshot files and modes")
        return selected
