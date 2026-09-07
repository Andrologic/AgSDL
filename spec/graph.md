# G: closed simple-graph grammar

[Specification index](README.md).

Conceptual example: draft through one Agent Interface, branch on its Boolean
needsReview output, obtain human approval for a second Agent invocation when
true, then finish. False returns the draft directly. The protected invocation
is still an Agent call; its Action reference describes the proposed action of
that call, not a second instruction or an `invokeAction` opcode.

When G is requested, graphs is Graph[]. An empty array is valid. Each graph's
definition uniquely selects a local ControlFlow. All graphs in this container
are checked; nested graphs, parallelism, arbitrary cycles and expressions are
outside G and fail its closed grammar if encoded as step kinds or fields.

| Record | Fields |
| --- | --- |
| Graph | `definition:Key`, `entry:text`, `inputs:Ports`, `outputs:Ports`, `steps:Step[]` with at least one step |
| invoke Step | `id:text`, `kind:"invoke"`, `operation:text`, `agent:Ref`, `interface:Ref`, `action:Ref`, `resources:Ref[]` nonempty, `principal:Ref`, `context:Binding`, `inputs:Ports`, `outputs:Ports`, `bindings:map<Binding>`, `success:text`, `failure:text` |
| condition Step | `id:text`, `kind:"condition"`, `test:Binding`, `true:text`, `false:text`, `failure:text` |
| approval Step | `id:text`, `kind:"approval"`, `call:text`, `requirement:Ref`, `timeoutMs:positive`, `approved:text`, `denied:text`, `failure:text` |
| success end Step | `id:text`, `kind:"end"`, `outcome:"success"`, `bindings:map<Binding>` |
| other end Step | `id:text`, `kind:"end"`, `outcome:"failure" or "denied"`, `reason:text` |
| Selected Interface payload | `operations:Operation[]` nonempty |
| Operation | `id:text`, `direction:"inbound" or "outbound" or "bidirectional"`, `mode:"request-response"`, `action:Ref`, `inputs:Ports`, `outputs:Ports` |
| Selected ApprovalRequirement payload | `approvers:Ref[]` nonempty, `validForMs:positive` |

## Interface operations

Operation ids are unique within the selected Interface. They are addressed by
Interface Ref plus operation id, never by searching other interfaces. Every
operation is a complete request/response contract; multi-message protocols and
notification dispatch need a separate future contract. This bounded interaction
mode is the existing invoke abstraction, not a restriction on open engine ids.
Direction is relative to the Agent exposing the Interface. Invoke selects an
inbound or bidirectional Operation; selecting outbound fails G-TARGET. Selected
operation Action and Ports equal invoke.action/inputs/outputs under shared
identity and exact-type rules. No operation is chosen by order or default.

G shape-checks the entire selected Interface payload, including all Operation
records. G-TARGET checks id uniqueness there; semantic Action resolution and
port agreement apply only to the selected operation. Bad fields on an unrelated
operation do not block readable fields on the selected one. Duplicate selected
id blocks its dependent lookup; an absent id fails at the consuming Step.
Annex payload findings use the annex G Result and operation record location;
id duplication points to its later Operation record. The primary comparison
still points to its Step. Unselected payloads remain opaque under the opaque-boundary rules.

## Targets, data and paths

Every G/R Ref obeys the same local/external declaration rules as D relations,
including dependency existence and scope matching; opaque D treatment does not
waive these checks when G/R interprets it. All selected graph refs are typed: agent Agent, interface Interface, action
Action, resources Resource, principal and approvers Principal, requirement
ApprovalRequirement. Resources and approvers have no duplicate Refs. Other
payloads, including Action/Principal/Resource and ControlFlow, are not evaluated.
G invents neither an acting identity nor authorization evidence from them.
An invoke's Interface is exposed by its Agent through one D relation, its
principal equals that Agent's actsAs target, and its action equals the Interface
selected Operation action. Equality here uses resolved keys when targets are available;
validateG checks known local matches and records external comparisons unchecked.
Refs inside a selected annex record use that annex as their local scope; the
primary invocation still identifies it using the external wrapper.

Selected Operation inputs/outputs equal the invoke's maps, including names and types.
The bindings map has exactly the invoke input names. Success terminals bind
exactly graph outputs; failure/denied terminals bind none. Context has type
json; condition test has type boolean. Binding input names exist in graph
inputs; step bindings name an invoke and one of its output ports. Types match
exactly, with no string-to-json coercion or selectors. All ports are required.
Only invoke produces ports. For every step-output binding, every path from entry
to its consumer must traverse that producer's success edge. Removing the success
edge must make the consumer unreachable. This also excludes self-use and
failure-path outputs. For an approval step, additionally check all bindings of
its call invoke, including context, at the approval step itself, because
the request presents those values before the invocation occurs.

Step ids are unique. Every successor and entry names a step. The graph is
acyclic, every step reachable from entry, every maximal path ends at an end
step. The only end steps have no successors. Successor labels are distinct
edges even if their target ids coincide. Conditions choose exactly true/false
for Boolean values; unusable values lead to failure. Invocations produce all
declared outputs on success; unusable/missing outputs lead to failure with no
partial outputs. These are declared meanings, not observations of a run.

## Sequential approvals for one call

Every approval names an invoke in the same graph. Its approved edge targets that
invoke or another approval with the same call. Following approved edges must
reach that call. A chain can contain any finite positive number of gates; each
gate is a distinct decision request even if requirements repeat.

For each protected call, its gates form one ordered chain: the invoke has only
the final gate's approved incoming edge; every gate after the first has only its
predecessor's approved incoming edge. The first gate can have ordinary incoming
edges or be entry. No denied or failure edge from any gate may reach its call or
any later gate in that chain. G-PATH still requires an acyclic, reachable graph.
A failed G-PATH check blocks chain reachability and incoming-path checks. Readable call links and target kinds still receive
independent checks.
These rules forbid alternate gate paths, skipping, parallel approval and quorum
without inventing a second orchestration system. Unprotected invokes remain legal.

Each gate's request scope is its call's selected Interface operation, Action,
resources, Principal definition, input values and context, plus the selected
configuration pin for a prospective execution. G validates the declared call
link and binding availability at every gate, not the existence of an execution
or a configuration selection. All call inputs/context must be available before
each gate under the producer-success rule above. Gates produce no ports.

The request permits approve/deny decisions by one of the requirement's declared
human Principal definitions. Validation checks references, not whether a real
human controls an identity. Authentication, authorization, decision matching and
timing evidence remain external; there is no executable decision intake API.
There is no graph-level timeout.

A valid approval within the gate's validity interval selects its approved edge.
Each gate's decision deadline is entry time plus min(timeoutMs, validForMs).
All earlier approvals must still be valid when entering later gates and when
admitting the call. Refusal selects the active gate's denied edge; no response,
invalid decision, or expiry of any needed decision selects its failure edge.
If expiry is detected at call admission, take the call's failure edge without
invoking it. Equality with a deadline counts as expired. Finite positive windows
do not prove that human decisions can arrive in time; static validation imposes
no invented timing inequality between gate durations.

All approvals are consumed only by that call in that execution. Stopping and
restarting, or changing the configuration pin, invalidates their use. There is
no reusable token API, decision intake service, authorization engine, migration
or runtime timing evidence here. The chain declares required control structure;
it neither authenticates an approver nor proves enforcement or permission.

ValidateG checks available local targets/payloads and all graph shapes, edges,
bindings and local agreements. An external Ref's declaration is checked, then
target-dependent checks are explicitly excluded at this phase, even if annexes
were supplied. ResolveG checks the same rules using its direct target set;
missing required G references fail and none may use a D deferral to pass.
The G verdict covers only this edition's selected target payload checks, not
full Interface, Action, approval or System validity.
