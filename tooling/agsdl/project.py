"""Read a project folder and assemble its AgSDL document."""

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit

from . import jsoninput
from .graph import route_targets, step_routes
from .schemacheck import SchemaChecker, pointer
from .validator import DOCUMENT_SCHEMA, SCHEMA_DIR, Report, validate_document

MANIFEST = "agsdl.json"
SCHEMA = SchemaChecker(jsoninput.load(Path(SCHEMA_DIR) / "project.schema.json"),
                       {"agsdl.schema.json": DOCUMENT_SCHEMA})
SECTIONS = ("agents", "compositions", "content", "skills", "mcpServers")


class ProjectError(ValueError):
    """An invalid project declaration or local reference."""


@dataclass
class Project:
    root: Path
    document: dict
    secrets: dict = field(default_factory=dict)
    mcp_files: dict = field(default_factory=dict)
    origins: dict = field(default_factory=dict)
    _spellings: dict = field(default_factory=dict, repr=False)
    _file_observer: object = field(default=None, repr=False)
    _json_reader: object = field(default=None, repr=False)

    def location(self, where):
        """Locate a document JSON pointer in the file that supplied it."""
        prefix = where
        while prefix:
            if prefix in self.origins:
                break
            prefix = prefix.rpartition("/")[0]
        return f"{self.origins.get(prefix, MANIFEST)}#{where[len(prefix):]}"

    def local_file(self, owner, name):
        if (not name or name.startswith("/") or "\\" in name
                or re.match(r"[A-Za-z][A-Za-z0-9+.\-]*:", name)
                or any(ord(c) < 32 for c in name)):
            raise ProjectError(f"{owner}: invalid local path {name!r}")
        if self._file_observer is not None:
            self._file_observer(owner, name)
        try:
            target = (self.root / owner.parent / name).resolve()
            relative = target.relative_to(self.root)
        except (ValueError, OSError, RuntimeError):
            raise ProjectError(f"{owner}: path outside project or unresolvable: {name!r}") from None
        if not target.is_file():
            raise ProjectError(f"{owner}: expected a regular project file: {name!r}")
        for part in (relative, *relative.parents):
            previous = self._spellings.setdefault(part.as_posix().casefold(), part)
            if previous != part:
                raise ProjectError(f"{owner}: paths differ only in case: {previous} and {part}")
        return relative

    def read(self, relative):
        try:
            if self._json_reader is not None:
                return self._json_reader(relative)
            return jsoninput.load(self.root / relative)
        except jsoninput.InputError as error:
            raise ProjectError(f"{relative}: {error}") from None

    def component(self, value, where):
        if isinstance(value, dict) and set(value) == {"file"}:
            source = self.local_file(Path(MANIFEST), value["file"])
            self.origins[pointer(where)] = source
            return self.read(source)
        return value

    def rebase_uri(self, owner, obj, key):
        uri = obj[key]
        try:
            parts = urlsplit(uri)
        except ValueError as error:
            raise ProjectError(f"{owner}: invalid URI {uri!r}: {error}") from None
        if parts.scheme and parts.scheme.lower() != "file":
            return
        if parts.scheme or parts.netloc or uri.startswith("/"):
            raise ProjectError(f"{owner}: expected a project-relative URI or external scheme: {uri!r}")
        # Preserve even empty query and fragment delimiters.
        suffix = uri[len(parts.path):]
        try:
            name = unquote(parts.path, errors="strict")
        except UnicodeError:
            raise ProjectError(f"{owner}: invalid UTF-8 in URI {uri!r}") from None
        target = self.local_file(owner, name) if name else owner
        obj[key] = quote(target.as_posix(), safe="/-._~") + suffix

    def rebase_sources(self, kind, obj, owner):
        if kind in ("skills", "content"):
            sources = [obj]
        elif kind == "mcpServers":
            if "url" in obj and not re.match(r"[A-Za-z][A-Za-z0-9+.\-]*:", obj["url"]):
                raise ProjectError(f"{owner}: a remote MCP endpoint requires an absolute URI")
            if "url" in obj and obj["url"].lower().startswith("file:"):
                raise ProjectError(f"{owner}: a remote MCP endpoint cannot be a file URI")
            return
        else:
            sources = component_sources(kind, obj)
        for source in sources:
            if "uri" in source:
                self.rebase_uri(owner, source, "uri")


def message_sources(obj, prompt_key):
    prompt = obj.get(prompt_key)
    if isinstance(prompt, list):
        yield from prompt
    yield from obj.get("resources", {}).values()


def component_sources(kind, obj):
    if kind == "agents":
        yield from message_sources(obj, "instructions")
        return
    # A flow-level onError carries the same routes as a step's onError.
    for step in [obj, *obj["steps"].values()]:
        yield from message_sources(step, "prompt")
        for _, _, route, _ in step_routes(step, []):
            for _, _, message, _ in route_targets(route, []):
                if message:
                    yield from message_sources(message, "prompt")


def check_shape(checker, value, location, definition=None):
    errors = checker.check(value, definition)
    if errors:
        where, message = errors[0]
        raise ProjectError(f"{location(where)}: {message}")


def load_project(path, *, _file_observer=None, _json_reader=None):
    """Load a directory or its manifest. All paths in the result use its root."""
    path = Path(path)
    root = (path if path.is_dir() else path.parent).resolve()
    if not path.is_dir() and path.name != MANIFEST:
        raise ProjectError(f"expected {MANIFEST}")
    project = Project(root, {}, _file_observer=_file_observer, _json_reader=_json_reader)
    entry = project.local_file(Path(MANIFEST), MANIFEST)
    manifest = project.read(entry)
    return _assemble(project, manifest)


def _assemble(project, manifest):
    check_shape(SCHEMA, manifest, lambda where: MANIFEST + "#" + where)
    doc = project.document
    doc.update({k: manifest[k] for k in ("contract", "id", "title", "description") if k in manifest})
    components = []
    for kind in SECTIONS:
        if kind in manifest:
            doc[kind] = {}
            for name, item in manifest[kind].items():
                where = [kind, name]
                value = project.component(item, where)
                doc[kind][name] = value
                components.append((kind, value, where))
    if "flow" in manifest:
        doc["flow"] = project.component(manifest["flow"], ["flow"])
        components.append(("flow", doc["flow"], ["flow"]))

    # Check shapes before walking routes or treating any field as a URI.
    check_shape(DOCUMENT_SCHEMA, doc, project.location)
    for name, filename in manifest.get("settingsFiles", {}).items():
        agent = doc["agents"].get(name)
        if agent is None or "harnessSettings" in agent:
            raise ProjectError(f"{MANIFEST}#/settingsFiles/{name}: unknown agent or duplicate settings")
        path = project.local_file(Path(MANIFEST), filename)
        agent["harnessSettings"] = project.read(path)
        project.origins[pointer(["agents", name, "harnessSettings"])] = path
        if not isinstance(agent["harnessSettings"], dict):
            raise ProjectError(f"{path}: expected a settings object")

    for kind, value, where in components:
        owner = project.origins.get(pointer(where), Path(MANIFEST))
        project.rebase_sources(kind, value, owner)

    servers = doc.get("mcpServers", {})
    if "secrets" in manifest:
        path = project.local_file(Path(MANIFEST), manifest["secrets"]["file"])
        project.secrets = project.read(path)
        check_shape(SCHEMA, project.secrets, lambda where: f"{path}#{where}", "secretRequirements")
        for server in project.secrets:
            if server not in servers:
                raise ProjectError(f"{path}: unknown MCP server {server!r}")
    for server, names in manifest.get("mcpFiles", {}).items():
        if server not in servers or "command" not in servers[server]:
            raise ProjectError(f"{MANIFEST}#/mcpFiles/{server}: expected a local MCP server")
        project.mcp_files[server] = [project.local_file(Path(MANIFEST), n).as_posix() for n in names]
    return project


def read_input(path):
    """Return the document and optional project for a CLI input."""
    path = Path(path)
    if path.is_dir():
        project = load_project(path)
    else:
        # Explicitly supplied ordinary documents retain their original file semantics.
        value = jsoninput.load(path)
        if path.name != MANIFEST or not isinstance(value, dict) or "projectFormat" not in value:
            return value, None
        project = Project(path.parent.resolve(), {})
        project.local_file(Path(MANIFEST), MANIFEST)
        _assemble(project, value)
    return project.document, project


@contextmanager
def open_input(path, modules=None):
    path = Path(path)
    if path.suffix == ".agsdl" and not path.is_dir():
        from .archive import open_archive
        with open_archive(path, modules) as project:
            yield project.document, project
    else:
        yield read_input(path)


def validate_path(path, modules=None):
    try:
        with open_input(path, modules) as (doc, project):
            report = validate_document(doc, modules)
            if project:
                for item in report.diagnostics:
                    item["message"] = f"{project.location(item['path'])}: {item['message']}"
            return report
    except (jsoninput.InputError, ProjectError) as error:
        report = Report()
        report.error("PROJECT" if isinstance(error, ProjectError) else "PARSE", "", str(error))
        return report
