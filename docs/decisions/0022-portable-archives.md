# 0022. Editable snapshots with optional Git history

A host can open the current project with a ZIP reader and the ordinary project
loader. Keeping the authored files preserves the locations that diagnostics
and editors use. An inventory ties those files to the exported snapshot.

An author may also share earlier versions. Git commits already describe
ancestry and file changes. A self-contained bundle lets the recipient inspect
them offline. Keeping the current snapshot separately costs space but allows
every project reader to open it without Git. A dedicated history contains only
the versions recorded for this project. The [archive format](../../spec/archive.md)
defines its representation.
