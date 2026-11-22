# Project folders

Project format 1 is an authoring format for an AgSDL 0.4.0 document and its
local dependencies. The document contract governs the assembled agents and
flow. A host that opens a project also receives the declared MCP files and
secret requirements.

## Entry and components

Open the directory or its root file, `agsdl.json`. Read the manifest and each
referenced JSON file using the [strict JSON rules](document.md#json-input).
The manifest carries `"projectFormat": "agsdl-project-1"`, the document
contract, ID and agents. It can also carry the other document fields. Its
optional `$schema` describes the manifest and is omitted from the assembled
document. See the [manifest schema](../schema/project.schema.json).

Each named agent, composition, content source, skill or MCP server, and the
optional flow, takes either its ordinary document form or an object containing
only `file`, a project path. The referenced JSON file contains that one
component in document form. Files inside components cannot include further
component definitions. IDs and references between components have the same
scope as in a single document.

A reader MUST assemble only declared components. Directory names and nesting
are the author's choice. Files beside an agent can hold its instructions.
A skill's `uri` identifies its `SKILL.md` as in the document contract.
An author's notes or an application's display settings can coexist with the
project and have no effect on assembly.

## Files and URIs

File declarations use relative POSIX paths based at the file that declares
them. A local file MUST exist and be a regular file. Reject absolute paths,
URI schemes in file paths, backslashes, control characters, and paths or
symbolic links that resolve outside the project. Resolve in-project symbolic
links before resolving a component's references. The manifest has the project
root as its base. Reject referenced canonical names that would collide on a
case-insensitive filesystem, including the names of parent directories.

Within a component, a relative content or skill URI refers to its declaring
file. Decode the URI path as UTF-8 to locate the local file. A query or
fragment alone refers to the declaring file. When assembling, express the
canonical path relative to the project root as a URI and retain the query and
fragment. Reject rooted and network-path references and absolute file URIs.
Leave external URIs intact. The reader never fetches them. A remote MCP
endpoint requires an absolute URI with a scheme other than `file`.

Apply these rules at content sources in agents, steps, route messages and
named content, and at skill URIs. Literal JSON values and harness settings
retain their contents. Keep command strings and arguments verbatim. Execution
permissions and working directories follow the host and document contracts.

## Project declarations

| Field | Meaning |
| --- | --- |
| `settingsFiles` | Map from agent ID to the path of a JSON object supplying its `harnessSettings`. An agent can supply settings either inline or here. The assembled settings are checked against the harness module. |
| `secrets` | A `file` reference to a requirements file mapping MCP server IDs to nonempty lists of distinct secret names. Names use ASCII letters, digits and underscores and start with a letter or underscore. |
| `mcpFiles` | Map from local command server ID to a nonempty list of distinct project paths for its scripts or other assets. The host receives the root-relative paths. A command argument by itself does not declare a file. |

All three fields are optional. For example, a requirements file containing
`{"issues":["ISSUES_TOKEN"]}` tells the host which secret the issues server
needs. The host supplies its value and controls its delivery to the server.
Opening a project requires neither the value nor access to a vault.
Readers MUST reject undeclared server or agent IDs in these maps.

## Validation

Validate the manifest, assemble the document and apply the ordinary document
and harness checks. Keep the component filename and local JSON pointer so an
author can locate a defect. Project read or assembly failures use the
`PROJECT` diagnostic in the reference tool. The document validator accepts
the assembled document independently of the project reader.

See the [review project](../examples/review-project/agsdl.json) for an
editable example.
