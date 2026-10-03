# Proposal 0019: persistent Agents, prompt and resources

Status: **0.2 design directions accepted under
[Decision 0011](../docs/decisions/0011-message-based-agent-model.md); not an
adopted contract or candidate edition.**
The directions cover persistent Agents, distinct prompt and resources,
multimodal Messages, optional initial prompt and output constraints, and
configured workspace access.
Concrete shapes and binding rules below remain proposed for the next candidate.
The [bounded flow candidate](../experimental/agent-flow-0.2/README.md) provides
partial static checks of these directions. [0017](0017-agent-only-kiss-0.2.md)
remains a separate frozen experiment; neither is a normative adoption.
[Release status](../README.md#release-status-and-history) remains authoritative.

## Problem and scope

The 0017 experiment applies Instructions `before-invoke` and describes an
Agent definition independently of a running instance. It does not establish
context continuity between calls. Adding documents to that structure as more
Instructions would also confuse information with behavioral direction.

Describe an Agent that continues across interactions, with two content roles:

- **Prompt**: the requests and instructions addressed to the Agent.
- **Accessible resources**: the documents and information made available to that
  Agent, called resources below. They are distinct from effect-scope resources,
  which describe the targets of an action in the existing candidate.

Both roles are independent of storage and delivery. A referenced instructions
file contributes to the prompt; an inline report remains a resource.
Engine selection and Tool contracts remain separate. This proposal does not
redesign graphs, approvals or the complete configuration grammar. Media
requirements extend the proposed Interface contract, not the 0017 readers.

## Agent continuity

An **Agent** is an initialized participant instance that retains its context
across interactions during its lifetime. A completed request does not end that
lifetime. Further requests addressed to the same Agent continue with that
context. This definition applies to human and software participation alike.
For a human participant, context means the system's continuing interaction with
that participant, not control over the person's memory.

An AgSDL declaration describes how to initialize an Agent; the declaration is
not itself a running instance. Reusing its initialization content can create
another Agent with a separate context. A declaration id is not a globally unique
runtime instance id. Within a running system, addressing a declared Agent means
continuing with its associated instance, not silently creating one per request.
A separate system start creates new instances unless a future resumption
contract explicitly provides otherwise.

There is no context-reset operation. A fresh context requires a new Agent.
The Engine manages context storage and representation. Continuity does not
promise an unlimited model window or verbatim retention of every exchange;
silent replacement by an empty session does not satisfy continuity.
Durable recovery after a process restart is not promised here.

This revises the definition-oriented wording in [0018](0018-human-and-software-agents.md)
and [Decision 0010](../docs/decisions/0010-human-and-software-agents.md) for the
next 0.2 model, as recorded in Decision 0011. It retains their common Agent
concept. The historical definitions and the existing candidate are not rewritten.

## Messages are the basic interaction

A Message is the unit exchanged with an Agent. It may carry a request and
supporting resources, or a result, using the content model below. A Message
addressed to an Agent targets its existing instance; receiving another Message
continues that Agent's context.
Keep instruction and information roles explicit within a Message, regardless of
media type. Sending information alone does not turn it into an instruction.

A basic exchange does not require a named Operation. Use Interface constraints
when software needs a more precise contract. Named Operations may be a later
specialization; the message model does not require an operation catalog for
every Agent. This changes the proposed authoring baseline, not the semantics
of existing 0017 `invoke` records.

A Message is an exchange description, not a new transport or runtime API.
[Proposal 0020](0020-blueprint-flow-0.2.md) supplies the accepted directions for
completion, result transfer, queueing or steering, loops and parallel flow.
Its candidate work includes correlation and delivery rules. Neither proposal
imposes exactly-once processing or a mandatory one-request/one-response pattern.

## Minimum content model

These are semantic shapes, not a new serialization accepted by the readers.
They describe the content part of an Agent, not its complete declaration.

| Element | Shape and meaning |
| --- | --- |
| Initial prompt | An optional ordered sequence of content sources carrying requests or instructions. When supplied, it establishes the Agent's initial direction. An Agent without an initial prompt waits for its first Message. |
| Accessible resources | A collection of explicitly supplied content sources with names local to the Agent. It may be empty. Names let a prompt or later request identify a resource without embedding its location. Collection order carries no meaning; this is not an exhaustive workspace inventory. |
| Content source | Exactly one inline value or one URI reference, with an optional media type describing the intended representation. Either role may use text, structured data or other media, including images, audio and video. |

Instructions and information remain distinct roles, independent of storage or
media type. Omitting the initial prompt does not change the separately declared
Engine, Tools, access or other configuration. It supplies no implicit task to run.
The grammar must define omission and any equivalent empty representation.

One source rule serves both roles. A source is either supplied content or a
location through which the recipient obtains content. Supplying both is
ambiguous and invalid; there is no precedence or fallback between them. An inline
value may be a JSON scalar, object or array. An inline string is literal content,
never implicitly a path or URL. Binary content can use a URI reference; the core
needs no additional binary embedding format.
A source URI is distinct from an AgSDL Definition reference: it accesses content,
not another Agent, graph or executable module.

A media type describes content, not its delivery strategy or trust. It is needed
when a format-specific compatibility claim is made; otherwise it may be absent.
It can distinguish a PDF, image or JSON document when that matters. An omitted
type makes no claim about representation; it does not mean plain text or grant
permission to discard visual information. If supplied, the integration checks
that it can support the declared representation and reports incompatibility.

Prompt order is preserved; it does not establish provider-specific system/user
roles or resolve contradictory instructions. An audio recording can supply a
spoken request; a video can supply instructions by demonstration. Their role is
authored explicitly, just as for text. Supplied prompt sources must be made usable in the
intended role before their instructions can be applied; text extraction is not
a universal substitute for receiving the original media. Unavailable supplied
initial prompt content prevents successful initialization rather than silently
shortening the prompt. This differs from an intentionally omitted initial prompt.

Resources can be shared between Agents by referring to the same source. Shared
resources do not merge Agent contexts. Reading a resource does not give its text
instruction authority. An author deliberately assigns content to the prompt
when the Agent is meant to follow it as instructions.

Later Messages can bring further requests and resources to the same Agent. They
do not replace the initial prompt or erase earlier context. Editing the declared
initial setup or Engine selection still requires stopping, modifying and
starting the system. Reading or editing workspace files and exchanging Messages
are ordinary activity within the selected configuration, not such a reconfiguration.

## Declared access and delivery limits

A resource declaration identifies information the Agent is intended to be able
to consult. An integration claiming to honor that declaration must provide the
content or a means to consult it; printing a path alone is insufficient. It may
supply native content, read a local file, retrieve a remote document or provide
a search tool. It preserves resource names in the presentation or access
tools so the Agent can identify them. An unsupported format or inaccessible
source is reported when discovered; listing resources does not require fetching
all of them during initialization. A static reader can check a declaration, not
prove that access works.
External content is not fetched by static validation.

Availability does not mean the Agent has consulted the resource or that all of
it is present in a model request. A search result need not contain an entire
document. This draft defines no general equivalence between full delivery,
lookup and search. Delivery choices must account for explicit task needs:
search-only access cannot be claimed equivalent to reading a complete document
when the task requires the latter. Unsupported needs must be reported. Whether
the Agent actually followed a natural-language reading instruction requires
execution evidence; static validation cannot establish it.

For example, "use these reports if needed" and "read both reports before
answering" use the same resource declarations with different prompt text. The
core needs no `eager`, `lazy`, `inject`, `RAG` or `mustRead` field. An integration
can offer additional documented capabilities without making them universal.

A URI declares a location, not permission, verified availability or an immutable
version. A relative URI needs an explicit source base supplied with the artifact;
without that base it remains unresolved, rather than using the reader's working
directory. A resource reference alone grants no write or execution permission.
AgSDL configuration declares the access made available through the selected
Engine and Tools; the consuming implementation enforces it. Credentials remain
external to content declarations.

## Workspace access belongs to configuration

The AgSDL configuration describes the workspace exposed to the Agent, its access
rules and the Tools available there, through the Engine settings and Tool
bindings. Their concrete contracts can be integration-specific; a static reader
must not infer their behavior from opaque parameters. No additional Workspace
entity or universal filesystem-permission schema is introduced here.

An Agent with a writable coding workspace can inspect and edit files using its
configured Tools. A read-only configuration permits inspection, not editing.
Accessible files need not each appear in the resource collection, and ordinary
file changes do not require new resource declarations or a fresh Agent.

The core imposes no general frozen/live resource switch, automatic snapshot or
refresh policy. File persistence, shared access and version pinning, when needed,
follow the configured Engine and Tool contracts. A reference does not itself
make a copy or pin a version. Changed files are observed through access Tools;
they do not automatically rewrite the Agent's existing context or initial prompt.
This resolves the resource-lifetime question at the configuration boundary
rather than making it another required Agent choice.

## Multimodal input and output

Keep three questions distinct: what an Agent needs to receive or produce, what
its selected Model supports when it uses one, and what the selected Engine can
actually deliver. Engine includes the harness and its integration here; this
proposal adds no separate Harness entity or mandatory Model for every Agent.

Use the existing Interface concept for declared input and output constraints.
Output constraints are optional. Without a declared output contract, replies
remain free within the requested instructions and configured capabilities; no
fixed output format, object shape or result set is inferred. When constraints
are declared, they must be explicit and checked against the produced result.

Distinguish permitted formats from required results. Allowing text or audio does
not require both. Requiring a JSON report and an audio file requires both; an
optional audio result must be declared optional. A failed constraint is reported,
not presented as a conforming result or used to silently replace the Agent.
The exact syntax for these constraints remains to be specified. Describe
the concrete format with an open media type, such as `text/plain`, `image/png`,
`audio/wav`, `video/mp4` or `application/json`. These are examples, not a closed
format list. Accepting audio input says nothing about producing audio output.
Multiple input or output items can carry different formats in one interaction.
The future Interface syntax must distinguish formats offered as alternatives
from items required together, without repeating those contracts on each call.

The same inline-or-URI source rule represents produced content. For example, an
Agent may return an inline textual explanation and a reference to an audio file.
For incoming content, the receiving integration obtains the referenced content.
For produced content, the producing integration exposes the result for the
recipient to obtain. An output URI refers to that result; it is not an
instruction to create content at a future destination.
A format requirement is separate from this actual content. An output reference
must come with a usable access path under the integration's delivery contract;
a URI alone does not prove that the recipient can retrieve the result.
`application/json` alone does not promise a particular object structure. If a
specific shape is required, declare that constraint in the Interface contract
and check the produced value against it.

Keep support declarations with the selected configuration and its integration,
including the selected Model where applicable. Reuse the existing distinction
between required capabilities, support claims and evidence. Do not derive
support from an Engine or Model name, or invent a default Model. Binding details
remain for the next candidate; no universal provider catalog is introduced.

For native model input or output, every component on the selected path must
support the required representation and direction. A Model supporting an image
does not help if its harness drops that image. An Engine accepting an audio file
through a Tool does not establish native audio support in its Model. Support
must apply to the intended prompt or resource role and the selected delivery
path, not just to a broad label such as "multimodal".

An explicitly selected Tool or documented integration can supply a conversion
or produce media even when the Model cannot do so natively. Report what that
path actually supplies. A transcript is text; sampled video frames are images;
an audio file produced by a Tool is that Tool's output. These do not establish
native audio/video understanding or generation by the Model. Transcription,
frame sampling and similar substitutions must not silently satisfy a requirement
for the original media or discard a required track. Conversion fidelity and
acceptable losses require an explicit contract for that path.

Assess the actual combination of formats and any relevant declared constraints,
such as codec, duration or number of items. Separate support for text and images
does not prove support for their simultaneous use. A MIME type is insufficient
to establish codec, size, timing or audiovisual-track support. The core need not
standardize every limit; unresolved requirements remain unknown, not supported.
Keep declared support, declared incompatibility and unknown support distinct.
A static claim is not execution evidence. Produced outputs still need checking
against the requested contract; a support claim does not guarantee every result.

| Illustrative requirement and configuration | Assessment |
| --- | --- |
| Image input; Model supports it but harness accepts text only | Native image input is incompatible on this path. |
| Audio input; a declared transcription Tool supplies text to a text Model | A conversion path, not native audio support; suitable only when its text result meets the declared need. |
| Audio output; Model can produce audio but harness returns only text | Required audio output is incompatible on this path. |
| Text explanation and image together; separate support claims only | Combined output support is unknown. |

These are hypothetical configurations, not claims about named products. Streaming,
synchronization protocols and codec registries are outside this proposal.

## Worked examples

An Agent called `reviewer` is initialized with:

| Part | Content |
| --- | --- |
| Prompt, first part | Inline instruction: "Compare the proposals using the criteria. Explain any missing information." |
| Prompt, second part | Text from the shared instructions file `./instructions/review.md`. |
| Resource `proposal_a` | The document at `./documents/a.pdf`, declared as `application/pdf`. |
| Resource `proposal_b` | The document at `./documents/b.pdf`, declared as `application/pdf`. |
| Resource `criteria` | Inline structured data containing the budget and required features. |

The integration makes both documents and the criteria available and applies the
prompt. A later request, "Now compare their maintenance costs", addresses the
same reviewer and continues its context. Another Agent can use the same prompt
and resources with an independent context. Changing Engine bindings changes how
content is delivered, not whether it is an instruction or a resource. Declared
content roles alone do not prove equivalent behavior across Engines.

For a coding Agent, configuration can expose a writable project directory with
file-editing and test-running Tools. A Message says "Fix the failing test" and
may name the relevant files. The Agent reads and edits those files without
listing the whole directory as resources or restarting after each correction.
A later Message, "Also test negative inputs", continues the same Agent. Its
explanation can remain free text, or an optional declared output contract can
require a report with specified fields. The file edits are Tool effects;
reporting them in a Message does not replace their access and effect controls.

## Alternatives and impact

| Alternative | Reason not to use it as the core model |
| --- | --- |
| One undifferentiated prompt containing all material | Loses the distinction between instructions and supporting information. |
| Separate File, Attachment, KnowledgeBase and InlineData entities | Models delivery mechanisms as separate concepts although the Agent needs access to their information. |
| Mandatory full insertion of every resource | Does not fit large collections or Engines that consult resources through tools. |
| New Agent for every request, with optional session settings | Makes the requested continuity optional and adds lifecycle choices to the simple case. |

This draft adds no memory catalog, reset switch, inheritance, default Engine,
per-resource adapter registry or generic content-loading policy. Existing engine
integration remains the place for provider-specific behavior. Resources do not
replace Tool contracts, access controls, or the effect scopes of governed calls.
In particular, 0017 `scope.resources` describes the targets of effects; it is not
the accessible-information collection defined here.

## Work remaining before a new executable candidate

- Set the exact serialization and relationship with existing Instructions,
  slots, Applications, Interface media requirements and Definition identity. This
  draft does not authorize a silent reinterpretation of `before-invoke` or of
  existing `invoke` semantics.
- Specify the Message envelope, how it targets an existing Agent and carries
  multiple content items, and how optional output constraints are declared. Keep
  initial setup distinct from later Messages. Coordinate flow and concurrent
  delivery with 0020. Arbitrary dynamic Agent creation and durable resumption
  remain outside this content model.
- Specify how Engine settings and Tool contracts expose declared workspace access
  for compatibility assessment, without a universal permission vocabulary or
  resource snapshot policy.

These are serialization and integration tasks; they do not reopen the accepted
Agent continuity, content roles or optional initial prompt. The
[0.2 preparation index](../docs/0.2/README.md) tracks the document hierarchy.

A new candidate must test at least an Agent initialized without a prompt and
waiting for its first Message, a supplied but unavailable prompt, mixed resource
types, inline versus referenced
content, unresolved access, instruction/resource role separation, a multimodal
prompt, distinct input/output support, a Model/harness mismatch, an explicit
conversion, combined media, output-format validation, and two successive
interactions with one Agent versus two independently initialized Agents. Include
a free reply, a constrained reply, and writable versus read-only workspace
configurations without per-file resource declarations. Static comparison can
establish declaration agreement; context continuity and actual access need
runtime evidence from consuming implementations.

## Proposed c1 input and response precision

The [c1 candidate](../experimental/agent-flow-0.2/README.md) distinguishes a
Message's authored content roles from flow-result data. Delivery adaptation
occurs after the one-time configuration choice. Result objects cannot assign
themselves instruction authority by containing `prompt` or `resources` keys.
Explicit Prepare source selection preserves non-text references as information.

Response text belongs to the current work occurrence, including acknowledged
steering, rather than to the Agent's whole conversation. The candidate defines
exact assembly and an optional recorded-parts check. Empty text is valid when
required outputs are satisfied. It does not permit silently dropping media,
claiming actual support or replacing a persistent Agent after correction.

## Proposed bounded declaration checks

The candidate now specifies [structured results, URI origins and scoped support](../experimental/agent-flow-0.2/README.md#structured-results-uri-origins-and-support).
These rules remain proposed. They add a closed structured-value vocabulary,
explicit source bases and exact requirement/claim matching. Static declarations
and supplied records cannot establish content access, permission or execution.
