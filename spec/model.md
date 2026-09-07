# Model and vocabulary

[Specification index](README.md).

A Document describes one version boundary, represented by its Root. A Definition
is a versioned description within that boundary. A Key is its exact scoped
identity, with the equality rules in [serialization](serialization.md).
A Principal Definition describes the accountable actor or actor class. An Agent
Definition describes an agent's interfaces and behavioral direction, independently
of the software that may execute it.

An Agent's Key identifies its Definition. Each Agent has exactly one `actsAs`
reference to a Principal Definition, and each invoke's `principal` equals that
reference under [G's agreement rules](graph.md). A Principal payload may describe
multiple identities; D does not interpret them. No separate Identity record,
authenticated actor, runtime instance or authority is inferred. Configuration
selects no Principal. Changing an engine keeps the same declared actor; concrete
authentication remains external evidence.

## Boundaries and references

A System Root describes a system boundary. A Fragment Root exports reusable
Definitions without becoming a System. A PackageVersion Root identifies an
immutable artifact boundary; it is not itself a Definition owned by that Root.
Each local Definition retains the Root as lifecycle owner. Imported Definitions
remain in separately supplied dependency Documents with their original owners.
Participation through a use relation is independent of ownership. A System can
use exclusively imported Agents.

A Ref declares a local Key or a Key in a named dependency. A declared external
reference is not evidence that its target exists. An annex is the supplied byte
artifact for a primary dependency id. Only direct annex resolution is supported,
with the exact boundary in [D](document.md). A missing permitted relation is a
Deferral, not a reference. Only the explicitly declared Fragment Interface
minimum may defer. Identity, owner, Principal and behavioral direction never do.

An Interface supplies addressable request/response Operations when selected by
G. An Action describes the proposed action of an invocation; a Resource names
its resource scope. Their payloads remain opaque. ApprovalRequirement supplies
human approver references and a validity window when selected by G. ControlFlow
is the Definition selected by a Graph, which declares scheduled invocations and
control transitions. Topology alone does not define scheduling. A transition
grants no permission to perform an effect, and a valid Graph proves no execution.

## Engines, tools and reusable content

An Engine is software that executes an Agent. Its Edition identifies a claimed
engine contract and version, not an Agent, runtime instance or acting identity.
A Tool describes a contract separately from an Implementation, a named concrete
adapter/function/service choice claiming to realize that Tool. Its Edition and
opaque parameters do not prove existence or support. Instructions describe
reusable content and an explicit application point. A Skill describes reusable
content with prerequisite content and Tool references. An Application names the
engine-specific adapter and parameters for applying that content.

A Configuration is one named set of graph choices: Agent engine assignments,
Tool choices, Applications and parameters. An AgentBinding assigns exactly one
Agent Definition; repeated invocations of that Agent share its assignment in
that Configuration. Configurations have no inheritance or implicit defaults.
A CapabilityClaim is an unverified declaration about an exact capability Edition.
R assesses these declarations only; it never retrieves or verifies their evidence.

An Execution is one concrete use of a Graph and selected Configuration outside
these static records. Occurrence identity, timing, authentication and state are
external. A Configuration id is local to its RuntimeDeclaration. The pair of
the containing artifact's byte hash and Configuration id pins its content for a
prospective Execution. The Graph and referenced Definitions retain their own
Keys, versions and dependency hashes. Editing a Configuration changes that pin
even when its id is reused, and requires stopping and starting a new Execution.
An edited Configuration cannot be presented as the same pinned Execution.
No launch API, hot reload, state migration or resumption contract is defined.

Other known Kinds receive only the checks expressly named in this edition.
Their payloads cannot introduce new portable semantics, runtime behavior or
conformance obligations. Semantic extensions have the explicit classification
and interpretation limits in [D](document.md).
