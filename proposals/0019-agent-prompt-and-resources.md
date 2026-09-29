# Proposal 0019: persistent Agents, prompt and resources

Status: **draft 0.2 model proposal; not an adopted contract or candidate edition.**
The maintainer requested persistent Agents, a separation between their prompt
and accessible information, and support for multimodal inputs and outputs.
The concrete model below is proposed for review.
[0017](0017-agent-only-kiss-0.2.md) remains the implemented experimental contract;
[release status](../README.md#release-status-and-history) remains authoritative.

## Problem and scope

The current experiment applies Instructions `before-invoke` and describes an
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
requirements extend the proposed Interface contract, not the current readers.

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
and [Decision 0010](../docs/decisions/0010-human-and-software-agents.md) if adopted.
It retains their common Agent concept. Those historical texts and the existing
candidate are not rewritten by this draft.

## Minimum content model

These are semantic shapes, not a new serialization accepted by the readers.
They describe the content part of an Agent, not its complete declaration.

| Element | Shape and meaning |
| --- | --- |
| Initial prompt | A nonempty ordered sequence of content sources carrying requests or instructions. It establishes the Agent's initial direction. |
| Accessible resources | A collection of content sources with names local to the Agent. It may be empty. Names let a prompt or later request identify a resource without embedding its location. Collection order carries no meaning. |
| Content source | Exactly one inline value or one URI reference, with an optional media type describing the intended representation. Either role may use text, structured data or other media, including images, audio and video. |

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
authored explicitly, just as for text. Prompt sources must be made usable in the
intended role before their instructions can be applied; text extraction is not
a universal substitute for receiving the original media. Unavailable initial
prompt content prevents successful initialization rather than silently
shortening the prompt.

Resources can be shared between Agents by referring to the same source. Shared
resources do not merge Agent contexts. Reading a resource does not give its text
instruction authority. An author deliberately assigns content to the prompt
when the Agent is meant to follow it as instructions.

Later interactions can bring further requests and resources to the same Agent.
They do not replace the initial prompt or erase earlier context. This describes
continuity, not a standardized messaging API or automatic catalog-update rule.
Changing the declared initial prompt, resource collection or Engine selection
still requires stopping, modifying and starting the system. Continuity concerns
the Agent context; it does not guarantee continued availability or unchanged
content of referenced resources. Those depend on the source and integration.

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
directory. Resource access grants no write or execution permission. Credentials
and access enforcement stay with the consuming application.

## Multimodal input and output

Keep three questions distinct: what an Agent needs to receive or produce, what
its selected Model supports when it uses one, and what the selected Engine can
actually deliver. Engine includes the harness and its integration here; this
proposal adds no separate Harness entity or mandatory Model for every Agent.

Use the existing Interface concept for input and output requirements. Describe
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

## Worked example

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

## Decisions still needed before a new executable candidate

- Set the exact serialization and relationship with existing Instructions,
  slots, Applications, Interface media requirements and Definition identity. This
  draft does not authorize a silent reinterpretation of `before-invoke` or of
  existing `invoke` semantics.
- Specify how later exchanges target an existing Agent and carry multiple
  content items; keep initial setup distinct from a new request. Concurrency,
  dynamic Agent creation and durable resumption are outside this content model.
- Specify resource version expectations where reproducibility is required.
  Referenced content may change independently of the AgSDL artifact. Neither
  snapshotting nor live-refresh semantics can be inferred from this draft.

A new candidate must test at least mixed resource types, inline versus referenced
content, unresolved access, instruction/resource role separation, a multimodal
prompt, distinct input/output support, a Model/harness mismatch, an explicit
conversion, combined media, output-format validation, and two successive
interactions with one Agent versus two independently initialized Agents. Static comparison can establish declaration agreement; context continuity
and actual access need runtime evidence from consuming implementations.
