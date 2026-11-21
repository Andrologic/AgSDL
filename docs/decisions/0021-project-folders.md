# 0021. Standalone project folders

A system author can edit an agent and its instructions together, move them
to another folder and update one reference. The flow addresses the agent by
ID throughout. Explicit file declarations keep scratch files and host display
preferences outside the system definition.

A separately versioned project manifest assembles the same document that the
0.4.0 validator and renderer already consume. This preserves their semantics
and avoids reviving the package identities and transitive dependency resolution
discussed in earlier editions. MCP file and secret requirements stay available
to the host alongside the document. [Project folders](../../spec/project.md)
defines the format.
