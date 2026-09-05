# A2UI research for AgSDL

Status: research note, non-normative
Last reviewed: 2026-09-02
Reviewed upstream commit:
[`715abe092b9ba12174a579c2de75b6dd0c90a502`](https://github.com/a2ui-project/a2ui/tree/715abe092b9ba12174a579c2de75b6dd0c90a502)

## Purpose and method

This note examines A2UI as an external format for declarative, agent-generated
user interfaces. It separates facts stated by A2UI from AgSDL mapping
conclusions. It does not change AgSDL semantics, define AgSDL syntax, or claim
that an AgSDL implementation can produce, consume, or round-trip A2UI.

The review uses the A2UI repository at the commit above. The upstream project
had no GitHub release and published no `v0.9.1` or `v1.0` tag at the review
date. The repository did have `v0.8` and `v0.9` tags, both resolving to commit
`19919ef4c8ad3185867f70386fa4669284d7714c`. References below therefore pin the
reviewed commit as well as the versioned directory. A later change to the same
directory or public specification URL is not part of this review.

## Version status

### Source facts

The upstream [project
README](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/README.md)
calls A2UI an early-stage public preview. It identifies `v0.9.1` as the current
production release in the stable `v0.9` family, `v1.0` as a release candidate,
and `v0.8` as legacy.

The [`v0.9.1`
README](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/README.md)
calls that specification current, production, and closed to changes. Its
[protocol](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/docs/a2ui_protocol.md)
accepts both `v0.9` and `v0.9.1` envelope values. The [evolution
guide](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/docs/evolution_guide.md)
records two changes from `v0.9`: the media type became
`application/a2ui+json`, and a deleted surface identifier may be reused after
deletion rather than remaining unique for the renderer lifetime.

The [`v1.0`
README](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v1_0/README.md)
states that `v1.0`, previously called `v0.10`, is a candidate. It will become
stable only after renderer ports and feedback meet the upstream project's bar.
The candidate can still change.

### AgSDL assessment

An A2UI dependency needs two identities: the advertised A2UI protocol version
and an immutable identity for the reviewed external artifacts. `v0.9.1` alone
does not reproduce the reviewed schemas because upstream did not publish a
matching tag or release. A binding that cites the candidate must also say that
it is a candidate and pin a commit or content digest. An implementation must
not negotiate `v1.0` from the old name `v0.10`.

The `v0.9` and `v0.9.1` envelope compatibility claim does not establish
behavioral equivalence for every transport binding. The media type and surface
identifier lifecycle changed. AgSDL should preserve those differences when
they affect routing, state correlation, or renderer behavior.

The reviewed `v0.9.1` directory also retains `v0_9` schema identifiers and
`v0.9` keys in the client and server capability schemas. Its envelope and
client-data-model schemas accept both `v0.9` and `v0.9.1`, while the A2A
extension examples advertise `v0.9.1` capability metadata. A binding cannot
infer one normalized version from the directory name. It must identify the
exact schema set and define which version spellings it accepts in each
location.

## Protocol model

### Source facts

The `v0.9.1` protocol defines a stream of JSON messages from a server role to a
client role. Four messages maintain a surface:

- `createSurface` selects a `surfaceId`, a `catalogId`, optional theme data,
  and optional full data-model synchronization;
- `updateComponents` adds or replaces entries in a flat component list whose
  child relationships use component identifiers;
- `updateDataModel` replaces data at a JSON Pointer, replaces the full model at
  the root, or removes a value when the `value` member is absent;
- `deleteSurface` removes the surface, its components, and its data.

A surface must exist before updates target it. One component eventually has the
identifier `root`. Component references and data bindings may be unresolved
when an update arrives, so a renderer can display placeholders while later
messages complete the surface. A surface's catalog and identifier are fixed
until deletion.

The renderer sends an `action` event to report a user interaction. The event
contains an action name, surface identifier, source component identifier,
timestamp, and context after resolving its data bindings. The renderer can
also return validation or generic errors. These structures are defined by the
[`server_to_client.json`](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/json/server_to_client.json)
and
[`client_to_server.json`](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/json/client_to_server.json)
schemas.

The `v1.0` candidate renames the roles from server and client to agent and
renderer. Its [evolution
guide](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v1_0/docs/evolution_guide.md)
also adds initial components and data to `createSurface`, mixed catalogs on one
surface, namespaced metadata extensions, composition constraints, and
bidirectional function calls. It removes theme data, requires `null` rather
than an absent `value` to delete data, and changes several schema names. It
requires a surface identifier to be unique for the renderer session. These are
material changes, not editorial renames.

### AgSDL assessment

A2UI is a specialized external format. Its surface, component, catalog, data
binding, and renderer roles do not need new core AgSDL entities.

- An active A2UI surface is runtime presentation state and a governable
  Resource. Its changing component graph and data model produce State
  occurrences governed by one or more State definitions. Neither is a static
  Agent definition.
- A catalog is a separately governed external artifact plus renderer
  implementation behavior. A catalog identifier is not necessarily
  resolvable, so it cannot serve as content integrity evidence.
- A2UI envelopes are Message occurrences at Interface operations. Each
  operation makes exactly one protocol Action available. Their required
  ordering and surface lifecycle are a candidate Protocol mapping.
- An A2UI `action` is a user-interaction message whose Interface operation makes
  a protocol Action available. The message requests a separate business Action
  only when the binding names that Action and maps its inputs and Resources. The
  event does not prove user identity, intent, approval, authorization, or an
  external Effect.
- Remote renderer or agent function calls in the `v1.0` candidate are Interface
  operations, each of which makes an Action available even when it has no
  possible Effect. Catalog caller restrictions describe implementation support.
  They do not grant authority.

## Catalogs and executable behavior

### Source facts

The upstream README describes A2UI as declarative data rather than agent-
generated executable code. A renderer maps catalog component names to locally
implemented widgets. In `v0.9.1`, the client advertises supported catalog
identifiers through
[`client_capabilities.json`](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/json/client_capabilities.json).
It may also supply `inlineCatalogs` there when the server advertises
`acceptsInlineCatalogs` through
[`server_capabilities.json`](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/json/server_capabilities.json).

The `v0.9.1` envelope schema is catalog-agnostic. Validation substitutes the
selected catalog for the generic `catalog.json` reference. A custom catalog
must use the A2UI `ComponentId` and `ChildList` schema definitions for fields
that create structural links, otherwise generic validators cannot check those
links. The [`v0.9.1` basic catalog implementation
guide](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/docs/basic_catalog_implementation_guide.md)
also defines renderer functions. Its `openUrl` function causes a side effect
and mandates URL parsing, an HTTP or HTTPS scheme allowlist, and browser
tab-nabbing protections.

The `v1.0` candidate catalog metadata adds function caller boundaries and a
user-activation requirement. The candidate protocol requires the renderer to
reject unknown or disallowed remote function calls. It also permits multiple
catalogs in one surface and defines explicit catalog resolution order.

### AgSDL assessment

An allowlisted catalog narrows the names an agent may request. It does not prove
that a widget implementation is safe, that two implementations behave the same,
or that visible content is honest. A catalog mapping must keep these subjects
separate:

- catalog schema identity and content;
- renderer implementation identity and version;
- component or function support claimed by that renderer;
- authority to invoke a function or perform an Effect;
- execution evidence that the renderer enforced the claimed restriction.

Client-supplied inline catalogs expand the schema and function vocabulary that
the agent may generate against. The agent's acceptance policy should identify
which renderer Principals may supply them, which immutable content is allowed,
and what happens when validation or integrity checks fail. The renderer must
still restrict execution to its implemented and permitted catalog behavior.
Merely recognizing a catalog identifier is not enough because the identifier
may be non-resolvable and mutable associations can change outside the A2UI
message.

## Data models and progressive updates

### Source facts

Dynamic component properties can contain literal values, JSON Pointer data
bindings, or catalog function calls. Input components update the renderer's
local data model. When `sendDataModel` is true, the renderer sends the full
current model in transport metadata on every renderer-to-agent message sent to
the server that created the surface. Passive local changes wait for the next
outbound message; they do not initiate transmission on their own. The
[`client_data_model.json`](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/json/client_data_model.json)
schema groups models by surface identifier.

A2UI uses RFC 6901 JSON Pointer for absolute data paths and extends it inside
collection templates. A path without a leading slash resolves relative to the
current collection item. That relative form is A2UI behavior, not strict RFC
6901 syntax, and an adapter must preserve or reject it explicitly.

The [`v0.9.1` A2A extension](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/docs/a2ui_extension_specification.md)
says a DataPart contains an array of A2UI messages and requires sequential
processing. The array is not a transaction. A receiver continues after a
message fails, although a renderer should delay repainting until it has
processed the array.

### AgSDL assessment

Progressive rendering exposes intermediate state. A binding must state whether
users may interact before all required components, bindings, validation rules,
and policy controls resolve. It also needs failure behavior for dangling
references, invalid later updates, duplicate surface creation, message loss,
and partial list application. Schema-valid messages alone cannot establish a
valid final component graph or a safe intermediate interface.

Full model synchronization is an information flow across a trust boundary. A
portable declaration should identify the data classes, destination principal,
purpose, minimization rule, retention rule, and failure behavior. The surface
identifier does not authenticate the intended agent. Transport metadata is not
confidential or integrity-protected merely because A2UI assigns it a field.

## Transport bindings

### Source facts

The core protocol requires ordered message delivery and message framing. It
also requires a metadata facility for full data-model synchronization and
capability exchange. Interactive use needs a return channel. The core does not
mandate a transport.

The protocol documentation lists A2A, AG-UI, MCP, SSE with JSON-RPC,
WebSockets, and REST as possible carriers. Only a specific transport binding
defines placement, activation, correlation, security, and delivery details.
The reviewed A2A extension uses the media type `application/a2ui+json`, A2A
DataParts, versioned extension URIs, and A2A message metadata for capabilities
and synchronized data models.

The pinned [extension
document](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/specification/v0_9_1/docs/a2ui_extension_specification.md)
is internally inconsistent with its schemas, examples, and reviewed [Python
SDK](https://github.com/a2ui-project/a2ui/blob/715abe092b9ba12174a579c2de75b6dd0c90a502/agent_sdks/python/a2ui_agent/src/a2ui/a2a/parts.py):

- the prose places the A2UI media type at `DataPart.data.metadata`, while its
  examples and the reviewed Python SDK place it at `DataPart.metadata`;
- the core protocol maps each A2UI envelope to one A2A Part, while the extension
  requires a list of messages in each DataPart; the reviewed Python SDK follows
  the core protocol and emits one DataPart for each message;
- its server-to-client example uses a wrapped component form
  `{"Text": {...}}`, while the pinned envelope and catalog schemas require a
  flat component object with `id` and `component` fields;
- the extension says AgentCard `params` corresponds directly to the server
  capability schema, but its example omits the schema's required top-level
  `v0.9` wrapper; the following prose instead refers to a nonexistent `v0.9.1`
  object in that schema;
- the client capability example uses a `v0.9.1` object key, while the pinned
  client capability schema requires the `v0.9` key;
- two prose assignments place `a2uiClientCapabilities` and
  `a2uiClientDataModel` directly under the A2A message, while their examples,
  the core protocol, and other extension passages place both under message
  metadata.

These conflicts are source facts, not AgSDL interpretations. A transport
binding cannot claim conformance to the extension document as a whole without
selecting an interpretation and testing it.

### AgSDL assessment

An AgSDL A2UI mapping should have a transport-independent format binding and a
separate transport binding. Naming A2A, MCP, WebSockets, or REST does not prove
that the required order, framing, metadata, peer identity, confidentiality,
integrity, replay handling, or return path exists. Each selected transport
needs its own binding requirements and tests. It must also define which pinned
artifact prevails when protocol prose, schemas, examples, and SDK behavior
disagree, and record every known exception to that rule.

The reviewed A2A extension is a candidate external binding, not an AgSDL-A2A
integration. AgSDL has not yet implemented or tested an A2A adapter. No A2UI
mapping may inherit an A2A compatibility claim from the presence of an
extension URI or media type.

## Trust limits

The following are AgSDL conclusions drawn from the reviewed contracts:

- Declarative input reduces direct code injection, but local components and
  functions still execute implementation code and can cause network or other
  Effects.
- Catalog support is an implementation feature, not authorization.
- Component text, labels, choices, and layout can deceive a user even when the
  payload validates structurally.
- A renderer must treat agent-supplied components, bindings, URLs, action
  context, and extensions as untrusted content until applicable policy accepts
  them.
- An agent must treat renderer-supplied capabilities, inline catalogs, action
  context, and synchronized data as untrusted input. A timestamp and source
  component identifier are claims in a message, not authentication evidence.
- Rendering an approval control does not create an AgSDL Approval decision.
  Protected Actions still require Authorization decisions at the applicable
  Policy application points. When an Authorization requirement requires human
  approval, its permitted decision also requires a matching, unexpired Approval
  decision from an identified human Principal for the same Action, Resources,
  principal scope, and material context.
- Accessibility metadata, visible labels, and validation messages need renderer
  behavior and human-interface testing. Schema validation cannot prove their
  effective presentation.

## Verification boundary

The upstream repository contains version-specific JSON schemas and schema test
runners. It also has an evolving language-agnostic conformance directory. Those
artifacts can test A2UI processors within their stated scope. They do not test
an AgSDL mapping.

AgSDL currently has no normative serialization, adapter contract, or A2UI
implementation feature. The useful deliverable at this stage is a proposed
mapping and a loss inventory. Executable AgSDL-A2UI conformance tests become
possible only after the project accepts representation rules and defines an
adapter subject with observable inputs and results. Until then, the project
must report A2UI integration as proposed and unimplemented.
