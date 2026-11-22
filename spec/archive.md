# Portable project archives

A file named `name.agsdl` contains a snapshot of one [AgSDL project](project.md).
A reader can open that snapshot offline. Programs, remote content, and secret
values required to run it come from the destination host. An optional Git
bundle carries the selected version and its ancestry.

## Container and inventory

Use a single-volume ZIP32 file with regular-file entries, stored or deflated,
without encryption or a ZIP comment. The only root entries are `archive.json`
and the optional `history.bundle`. Store the original project files beneath
`project/`, including `project/agsdl.json`. Directories are implicit.

`archive.json` uses [strict JSON](document.md#json-input) and the
[inventory schema](../schema/archive.schema.json). Its `archiveFormat` is
`agsdl-archive-1`. The `files` map keys are paths relative to `project/`.
Each value gives the uncompressed byte length, lowercase hexadecimal SHA-256
of the exact bytes, and a boolean `executable` flag. Restore the executable
bit on filesystems that support it. `archive.json` excludes itself from the
inventory. The optional `history` object gives the bundle's byte length,
SHA-256 and selected Git commit. Include it exactly when the bundle is present.

## Selecting files

Collect the manifest, all referenced component and settings files, local
content and skill URIs, secret declarations and declared MCP files. A local
skill contributes every regular file under the directory containing its
entry file. That directory must be inside the project and distinct from its
root. Preserve authored bytes, names and relative references. Deduplicate a
file reached more than once. An external reference stays in its source file.

Ignore unrelated files. Reject a selected symlink or special file, including
a symlink in a selected path. Reject a selected path containing a component
named `.git`, `.env`, `.env.*` (any suffix), or `.agsdl-history.bundle`,
case insensitively. These rules apply throughout skill trees. Secret
requirements name the values a server needs. Authors control the content of
every selected script, instruction and skill file.

Use relative paths with UTF-8 names separated by `/`. Reject empty, dot
and parent components, trailing spaces and dots, Unicode category C characters,
Windows reserved device names and the characters `< > : " \\ | ? *`.
Reject paths that collide after case folding and NFC normalization, including
ancestor directories. An archive path can have up to 64 components, 255 UTF-8
bytes per component and 4096 bytes in total, measured from the project root.
A relative reference inside an authored file can still use `..` within the
project as defined by the project format. A directory traversed only on the
way to `..` can be absent after extraction. Check existing components of
the authored path for symlinks before resolving the final file.

## Reading and writing

Verify the inventory against the complete set of ZIP entries. Reject
duplicates, file/directory conflicts, and any size or digest mismatch.
Check the complete stored or deflated stream against its declared size and
CRC, including the data descriptor when present.
Read into a new private directory, validate the assembled project and compare
its discovered files with the inventory before publishing the result.
The reference tool limits an archive to 8192 entries, 256 MiB of uncompressed
data in total, a 2 MiB inventory, an 8 MiB central directory and a 512 MiB
container. It caps the selected paths (including directories) at 16384. For JSON declarations
the reader allows 1 MiB per read and 8 MiB in total, nesting to depth 64,
and arrays of at most 1024 items. These JSON limits do not apply to opaque
resource files. Hosts may enforce lower resource limits.

Extracting a snapshot reads data. It never starts a flow, loads a skill into
an agent, installs software or retrieves external content. A reader without Git
can verify the bundle as opaque bytes and open the snapshot. A reader importing
the history must additionally verify its Git contents.

For reproducible snapshot exports, the reference tool sorts the entries,
uses a fixed ZIP timestamp and records only the executable bit from the source
mode. Different ZIP encoders can represent the same inventory and files.

## Project version history

A version records all portable project files as a Git tree, with blob bytes
and modes `100644` or `100755`. Its commit message describes the version.
A history writer takes each snapshot from the project reader, independently
of any surrounding working repository. The store contains the selected
commit and its ancestors, including files removed in subsequent versions.
An export of only the current snapshot omits the entire history.

Use a self-contained version 2 Git bundle with SHA-1 object IDs, no prerequisites and
one advertised reference, `refs/heads/versions`. Its tip must be the
inventory's `history.commit`. A history reader verifies the bundle in an
empty repository. Every reachable commit must carry the same project ID.
Its tree must contain exactly the files selected by that revision's manifest,
including its complete local skill directories. Apply the portable path and
file type rules to each revision. Compare the tip's complete tree, including
paths, file contents and executable bits, with the snapshot. Opening an old version
uses ordinary Git history. Creating a version based on an older commit in
the reference tool writes a separate bundle so the original versions remain
available.

The reference Git reader accepts up to 64 MiB of bundle bytes, 10000 objects
and 128 MiB of expanded content. It checks the expansion limit on both the
packed object data and the reconstructed object sizes before importing the
pack. Its Git operation budget is 60 seconds.
These implementation limits are separate from snapshot import. A snapshot
reader can access the current project regardless of Git availability.
