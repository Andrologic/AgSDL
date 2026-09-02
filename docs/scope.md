# Scope

## Problem

Agent frameworks describe systems through framework-specific code and
configuration. The same concepts are represented differently or left implicit.
This makes systems difficult to inspect, compare, validate, migrate, and govern.

AgSDL aims to define a framework-independent model for an agentic system. The
model must represent both individual agents and the system-level relationships
that determine behavior.

## In scope

- system identity, boundaries, goals, ownership, and interfaces;
- agent definitions and reusable agent components;
- models, prompts, tools, skills, memory, knowledge, and state;
- orchestration, topology, routing, delegation, handoffs, and protocols;
- permissions, credentials references, policy, guardrails, and approvals;
- runtime and deployment requirements without prescribing an implementation;
- observability, evaluation, testing, conformance, and lifecycle metadata;
- references, packages, profiles, extensions, and version compatibility.

## Out of scope for the first draft

- a universal agent runtime;
- a new agent communication transport;
- a model-provider API;
- a graphical editor contract;
- framework-specific behavior presented as portable semantics;
- claims of interoperability without executable conformance tests.

## Success condition

The first public draft succeeds when two independent implementations can parse
the same conforming document, agree on its portable meaning, report the same
structural validation failures, and identify every implementation-specific
extension.
