---
domain: workflow
type: note
status: locked
scope: theory-and-manuscript
evidence: theory-lock-process
tags: [graph-engineering, research-loop, memory]
---

# Research loop

## Graph engineering

The semantic spine is

`closest work -> research gap -> architecture -> CCA -> interface -> NMPC -> proof -> evaluation`.

Source nodes connect to the concept they support. Operational logs, protocols,
run IDs, and raw results remain outside the vault.

## Loop engineering

Each iteration must challenge the closest-work boundary, update the gap matrix,
map claims to tests, and reject any component novelty contradicted by prior work.

## Harness engineering

The current harness is a theory checklist: every retained claim must trace to a
DOI boundary, equation, assumption, falsifiable hypothesis, claim limit, and
future validation item. Executable checks are deferred to
`IMPLEMENTATION_PLAN.md`.

## Context engineering

Root `MEMORY.md` is the single durable context contract. It records scope,
authority, evidence limits, baseline fairness, code layout, and stop conditions.

## Prompt engineering

`research/RESEARCH_PROMPT.md` reloads the context, instructs a skeptical DOI audit,
and prevents invented novelty or results. The prompt is subordinate to evidence.

## Exit condition

Exit the research loop only when every contribution has:

1. a closest DOI-bearing source;
2. a precise unresolved limitation;
3. a falsifiable hypothesis;
4. a matched baseline and metric;
5. an equation-to-future-implementation mapping;
6. an explicit claim boundary;
7. a consistent English theory block in the Overleaf manuscript.

## Links

[[cca-nmpc-research]] · [[01_Problem/research-gap]] ·
[[02_Literature/closest-work]] · [[02_Literature/evidence-synthesis]] ·
[[04_Evaluation/baseline-contract]] ·
[[04_Evaluation/claim-evidence-boundary]]
