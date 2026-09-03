# ADR-0001: Build the v1 Evidence Agent with LangGraph

Date: 2026-09-03
Status: Accepted

## Decision

The v1 Evidence Agent (Section 9) is implemented with LangGraph. LangGraph stays scoped to the Evidence Agent; the fixed pipeline keeps calling the Responses API directly (Section 12.1). A post-v1 experiment may rebuild the same agent without LangGraph and compare the two.

## Context

The owner wants hands-on LangGraph practice inside the portfolio project, and this repository is the only place where that practice can be public and evaluated. The Evidence Agent is the one component whose shape (tool loop, turn limits, checkpoints) matches what LangGraph provides.

## Rejected

- Rejected: LangGraph as a post-v1 experiment only, with a framework-free v1 baseline (previous Section 9.6). Delays the practice until after the agent milestone.
- Rejected: LangGraph or LangChain in the fixed pipeline. Would hide prompt inputs and tool calls behind framework abstractions and dilute the direct Responses API and structured-output evidence the portfolio claims.
- Rejected: OpenAI Agents SDK for v1. Deferred to the post-v1 comparison (Section 23).

## Consequences

- Section 18.4's "measured use case before adoption" rule now names LangGraph as the scoped exception; it still applies to any further framework.
- Section 12.3 telemetry must be captured from LangGraph callbacks so the Run record stays complete.
- Week 8 stays where it is in the schedule; only its deliverable changed.
