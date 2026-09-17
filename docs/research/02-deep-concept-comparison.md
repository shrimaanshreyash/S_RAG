# S_RAG portfolio evolution: deep concept comparison

Date: 2026-08-31

## Decision from this research round

Do **not** select RippleRAG in its original form.

The need is real, but the broad promise—trace the downstream impact of changing a
requirement—is already a core capability of established requirements-management
systems. [IBM DOORS](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors-next/7.3.0_beta?topic=requirements-traceability)
explicitly describes traceability-based impact analysis for proposed changes.
[Jama Connect](https://help2.jamasoftware.com/ah/en/getting-to-know-jama-connect-features/traceability-from-requirements-to-test.html)
and [Siemens Polarion](https://polarion.plm.automation.siemens.com/hubfs/Factsheets%20nd/Siemens-SW-Polarion-Requirements-FS-55623-D8.pdf)
occupy the same established category. A portfolio project must not present this
as a newly invented job.

The two concepts that survive this round are:

1. **ForkTrace — a temporally sealed decision replay lab**
2. **PlanMutate — mutation testing for operational runbooks and SOPs**

Neither is proven globally unique. That claim is impossible to establish from web
and GitHub search alone. They are the strongest *testable wedges* found so far:
each has documented need, clear adjacent competitors, an explainable difference,
objective evaluation and a feasible local-first MVP.

No implementation should begin until one of these two wedges passes the validation
gate at the end of this document.

## Evidence standard

This comparison uses a stricter meaning of “different”:

- A new model, vector database, graph or agent is not a product difference.
- Combining popular AI terms is not a product difference.
- A feature absent from one competitor page is not proof nobody has built it.
- Stars indicate developer attention, not product quality or market demand.
- A surviving concept needs a distinct user job, authoritative evidence of pain,
  visible competitors to compare against, a falsifiable positioning statement and
  measurable behavior beyond generated prose.

The public-search claim we can honestly make is:

> As of 2026-08-31, this research found adjacent products and prototypes, but no
> dominant open-source project or product publicly positioning itself around the
> exact workflow and evaluation contract described for ForkTrace or PlanMutate.

That statement must be rechecked before publishing the final portfolio.

## Why ordinary RAG is already saturated

Current GitHub counts were read through the GitHub API on 2026-08-31. They are a
snapshot and will change.

| Project | Public stars | What it makes non-distinct |
| --- | ---: | --- |
| [Dify](https://github.com/langgenius/dify) | 153,986 | general AI/agent application platform |
| [RAGFlow](https://github.com/infiniflow/ragflow) | 89,729 | production document RAG and agent workflows |
| [Docling](https://github.com/docling-project/docling) | 65,788 | advanced document parsing |
| [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) | 65,420 | local/private chat over documents |
| [PrivateGPT](https://github.com/zylon-ai/private-gpt) | 57,492 | private local document Q&A |
| [LlamaIndex](https://github.com/run-llama/llama_index) | 51,935 | broad retrieval and agent infrastructure |
| [LightRAG](https://github.com/HKUDS/LightRAG) | 39,286 | graph-enhanced RAG |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | 35,754 | graph-based corpus reasoning |
| [screenpipe](https://github.com/screenpipe/screenpipe) | 21,323 | local screen/audio memory |

Therefore these are rejected as primary claims: “private RAG,” “GraphRAG,”
“agentic RAG,” “multimodal RAG,” “better PDF parsing,” “chat with documents” and
“record the screen and remember it.” They can still be supporting technology.

## Paths investigated

### 1. ForkTrace — temporally sealed decision replay

#### One-line product explanation

**Normal RAG tells you what the full archive says now. ForkTrace reconstructs only
what a team could have known at the moment of a decision, exposes the assumptions
and missing evidence, and shows which later facts would have changed the choice.**

#### Specific user and moment

An engineering or operations lead reviewing an architecture choice, migration,
incident response or failed project decision after the fact.

The user asks:

- What evidence was actually available on the decision date?
- Which later documents must be excluded to avoid hindsight leakage?
- What alternatives and criteria were considered?
- Which statements were evidence, assumptions or unresolved unknowns?
- Was the choice poorly reasoned then, or merely overtaken by later events?
- What new evidence first made the original decision unsafe or stale?

#### Why the need is backed

[NASA's systems-engineering guidance](https://www.nasa.gov/reference/4-0-system-design-processes/)
says design decisions, requirement rationale, assumptions and relationships should
be documented because the reason can otherwise be lost. A separate
[NASA engineering-rationale report](https://ntrs.nasa.gov/api/citations/19900017959/downloads/19900017959.pdf)
describes the recurring need to answer why work was done a certain way when
documentation is missing and expertise has left. This is authoritative evidence
that the problem is not invented for an AI demo.

#### Direct and adjacent competition

- [Rationale](https://therationale.ai/) is the closest product. It extracts
  engineering decisions, evidence, alternatives, tradeoffs, timelines,
  supersession and outcomes from RFCs, tickets and wikis.
- [Assumption Mapper](https://assumption-mapper.com/) tracks startup assumptions,
  grades supporting/contradicting evidence, shows confidence drift and preserves a
  decision log.
- [Context Graph](https://github.com/dsivov/Context_Graph) is a 2026 open-source
  prototype for decision lineage, policy context, validity periods and provenance.
- Agent-observability and replay tools reconstruct AI-agent actions, but their user
  and evidence contract are different from retrospective human project decisions.

These competitors invalidate the broad ideas “organizational decision memory” and
“assumption ledger” as unique concepts.

#### Narrow wedge that remains

ForkTrace is not a decision wiki. Its central invariant is a **time-sealed evidence
boundary**. A replay for 2025-04-12 may retrieve only material that existed by that
date. Later artifacts are held in a separate reveal lane. The product then compares:

1. the decision record reconstructed from time-valid evidence;
2. explicit versus inferred assumptions and unknowns;
3. alternatives scored against the criteria known then;
4. later evidence that confirms, weakens or invalidates the reasoning; and
5. a counterfactual review of what additional evidence could have changed the
   recommendation, without claiming it can prove alternate real-world outcomes.

Public pages reviewed for Rationale and Assumption Mapper do not describe this
time-sealed, hindsight-controlled replay contract. That is a differentiation lead,
not proof of exclusivity.

#### Why RAG is necessary

The evidence is dispersed across dated RFCs, tickets, incident reports, meeting
notes and test results. Retrieval must enforce temporal filters and provenance
before generation. A language model alone with the whole archive would leak future
knowledge into the reconstructed past.

#### Supporting AI/technical capabilities

- temporal retrieval and document-version validity;
- structured extraction of decisions, alternatives, criteria and assumptions;
- contradiction and entailment checks;
- a decision/evidence dependency graph;
- counterfactual question generation with explicit uncertainty;
- citations for every reconstructed claim;
- human confirmation for inferred rationale.

#### Portfolio demo

Use a synthetic engineering project with dated artifacts around a database
migration. The archive includes an RFC, benchmark, risk note, meeting transcript,
incident, and a later vendor announcement.

The demo first replays the decision on its original date and visibly locks all
future evidence. It then advances the clock, reveals the first invalidating fact,
and shows exactly which assumption and dependent decision became stale.

#### Objective evaluation

- future-evidence leakage rate: target **0%**;
- decision/alternative/criterion/assumption extraction precision and recall;
- citation coverage and citation correctness;
- temporal classification accuracy;
- stale-assumption detection precision and recall;
- calibration of unknown/unsupported labels;
- reviewer agreement with a hand-authored decision graph;
- time saved answering a fixed decision-review questionnaire.

#### Main risks

- rationale absent from source material cannot be recovered honestly;
- counterfactual language can overstate causality;
- timestamps may not equal when information became available;
- the wedge may be absorbed quickly by a decision-memory incumbent.

The UI must visibly distinguish **documented**, **inferred**, **unknown** and
**learned later**.

### 2. PlanMutate — mutation testing for runbooks and SOPs

#### One-line product explanation

**PlanMutate compiles an operational procedure into an inspectable state machine,
mutates its assumptions one at a time, and shows exactly where the documented plan
can no longer be executed—with every gap linked to source text.**

#### Specific user and moment

An operations, reliability or continuity lead reviewing a runbook before a live
exercise or before approving a procedure change.

Examples of mutations:

- the named owner is unavailable;
- the identity provider is down;
- the primary communication channel fails;
- a referenced credential has expired;
- two steps require the same person simultaneously;
- a dependency returns a different state than the happy path;
- a time limit is shorter than the documented sequence can satisfy;
- an escalation role or recovery condition is missing.

#### Why the need is backed

[NIST SP 800-53 CP-4](https://pages.nist.gov/oscal-tools/demos/csx/baseline-reviewer/)
requires testing contingency plans to determine effectiveness and readiness, and
names walkthroughs, tabletop exercises, checklists and simulations as ways to
identify weaknesses. [NIST SP 800-84](https://www.nist.gov/publications/guide-test-training-and-exercise-programs-it-plans-and-capabilities)
describes tabletop exercises as a way to examine roles, responsibilities,
interdependencies and plans. [CISA exercise guidance](https://www.cisa.gov/sites/default/files/publications/CommunicationsSpecificTabletopExerciseMethodology_0.pdf)
similarly uses exercises and after-action reports to find gaps in SOPs, governance,
technology, training and usage.

#### Direct and adjacent competition

This field is active and cannot be called empty:

- [Tabletop.ai](https://www.tabletop.ai/) runs live, role-based cyber exercises,
  generates scenarios and produces governance reports.
- [ORNA](https://www.orna.app/) uploads response plans and playbooks to customize AI
  cyber-crisis simulations.
- [Transilience](https://www.transilience.ai/platforms/tabletop-exercise) generates
  exercises from live asset inventories and scores participants.
- [CyberTabletop](https://github.com/DrDeathLabs/cybertabletop) is a self-hosted 2026
  open-source AI tabletop platform.
- [Preppr](https://preppr.ai/) and other exercise platforms ground scenarios in an
  organization's documents.

These invalidate “AI tabletop exercise generator” as a unique claim.

#### Narrow wedge that remains

PlanMutate is a **preflight document test harness**, not a live training platform.
The procedure itself is the system under test:

1. compile its roles, preconditions, actions, dependencies, branches, evidence and
   completion conditions into a reviewable state machine;
2. reject or ask for confirmation where the source does not support a transition;
3. generate controlled single and paired mutations;
4. execute the model deterministically where possible;
5. report unreachable states, missing branches, dead ends, circular handoffs,
   undefined authority and unsupported recovery claims;
6. propose exact document edits, but require human approval.

The framing is analogous to mutation testing in software: if a small change to an
assumption makes the procedure fail and the document cannot explain recovery, the
plan has exposed a testable gap. Current products reviewed emphasize designing and
running human exercises, not a repeatable CI-like test suite for the procedure
artifact itself. Again, this is a research lead rather than proof of exclusivity.

#### Why RAG is necessary

Runbooks reference policies, diagrams, role matrices and recovery documents outside
the primary file. The compiler needs retrieval to resolve those dependencies and
must retain citations so every state transition and every reported gap can be
audited against the source corpus.

#### Supporting AI/technical capabilities

- schema-constrained process extraction;
- retrieval across referenced documents;
- state-machine or planning representation;
- constraint checking and graph analysis;
- mutation generation bounded by a typed catalog;
- contradiction detection;
- cited repair suggestions with human approval.

#### Portfolio demo

Use a synthetic incident-response corpus. The normal path works. Then toggle “SSO
unavailable” and watch the plan fail because the emergency credential procedure
also requires SSO. A second mutation removes the primary incident commander and
reveals that no delegation rule exists. The output is a reproducible failing test,
not merely an AI opinion.

#### Objective evaluation

- process-step and transition extraction precision/recall;
- source coverage for compiled transitions;
- known-gap detection precision/recall over a hand-authored mutation suite;
- false-positive rate on executable procedures;
- deterministic replay rate;
- mutation survival rate before and after document repair;
- reviewer agreement on suggested gaps;
- latency and local resource use.

#### Main risks

- prose procedures are often too ambiguous to compile automatically;
- real execution semantics may be unavailable without system integrations;
- generated mutations can become implausible noise;
- regulated or safety-critical use requires explicit non-automation boundaries.

The product must call itself a **review and test aid**, not a certification engine.

### 3. RippleRAG — unstructured change-impact discovery

#### Verdict: useful, but demoted

[IBM DOORS](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors-next/7.3.0_beta?topic=requirements-traceability)
already exposes traceability and impact analysis for proposed requirement changes.
Mature requirements tools make the original claim non-novel. A narrower version for
messy documents outside formal requirements systems could still be a useful feature
inside ForkTrace or PlanMutate, but it is not the strongest standalone portfolio
identity.

### 4. Executable Knowledge — prose policy to rules and tests

#### Verdict: technically strong, but research-active

[Apple Prose2Policy](https://machinelearning.apple.com/research/prose2policy)
already performs policy detection, structured extraction, Rego generation, schema
validation, linting, compilation and automated testing. It reports a 95.3% compile
rate for accepted policies, 82.2% positive-test pass rate and 98.9% negative-test
pass rate. The open Policy-to-Tests research direction also converts prose
governance into executable rules.

This path has excellent evaluation, but a general implementation would look like a
reproduction of current research. It should be reconsidered only with a very
specific domain and a clearly different execution target.

### 5. Evidence Journey — mixed-media case builder

#### Verdict: strong pain, weak differentiation and high stakes

Evidence timelines, claim organizers, investigation workspaces and legal discovery
tools are already numerous. A consumer dispute assistant would be easy to explain,
but legal and insurance stakes raise the cost of mistakes. Without a specific
underserved case type and access to representative data, it is not the best first
choice.

### 6. Procedural/physical twin — learn work from video and guide it live

#### Verdict: high visual impact, poor first-MVP feasibility

Screen-memory tools, workflow capture products and industrial multimodal assistants
already cover much of this surface. Reliable step recognition, spatial grounding
and live safety-aware guidance would demand more data and hardware validation than
the current local document baseline supports.

## Comparative score

Scores are current research judgments from 1 to 10, not market facts.

| Concept | Exact-claim novelty | Need evidence | Demo clarity | Defensibility | MVP feasibility | Evaluation strength | Weighted result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **ForkTrace** | 8.0 | 8.5 | 9.5 | 8.0 | 8.0 | 9.0 | **8.5** |
| **PlanMutate** | 8.0 | 9.0 | 9.5 | 8.5 | 7.0 | 9.5 | **8.5** |
| Executable Knowledge | 5.5 | 8.5 | 9.0 | 6.5 | 7.5 | 9.5 | 7.7 |
| RippleRAG | 5.0 | 9.0 | 9.0 | 6.0 | 8.0 | 8.5 | 7.5 |
| Evidence Journey | 4.5 | 9.0 | 8.5 | 5.0 | 6.5 | 7.0 | 6.8 |
| Procedural/physical twin | 5.5 | 8.0 | 10.0 | 7.0 | 4.0 | 6.0 | 6.7 |

ForkTrace and PlanMutate tie numerically for different reasons:

- **ForkTrace is the better portfolio story**: the time-lock prevents hindsight
  leakage, creates a memorable demo and makes RAG structurally necessary.
- **PlanMutate has the stronger objective test contract**: it can produce passing
  and failing procedure tests, but extraction and realistic mutation design are
  harder.

## Recommended validation before selection

Do not choose based on the names or scores. Build no product code yet. Run two
small, time-boxed evidence probes using synthetic documents and the current RAG
service only as a retrieval utility.

### Probe A: ForkTrace

Create 8–12 dated artifacts around one engineering decision and a hand-authored
answer key. Test whether the system can:

- exclude every future artifact at the original decision date;
- recover evidence, assumptions, alternatives and unknowns;
- identify the first later artifact that invalidates an assumption; and
- abstain when rationale was never documented.

Fail the concept if temporal leakage is non-zero after reasonable engineering, or
if most rationale must be invented rather than extracted.

### Probe B: PlanMutate

Create one 15–25 step incident runbook plus linked policy and ownership documents,
with 10 seeded gaps. Test whether the system can:

- compile a reviewable process graph;
- run a fixed mutation catalog;
- find seeded dead ends and missing branches;
- cite the source behind every transition; and
- avoid reporting speculative gaps as facts.

Fail the concept if reviewers cannot agree on the compiled process or if mutation
results are mostly subjective prose.

## Selection rule

Select the concept that achieves all of the following:

1. at least 80% precision on its core structured extraction;
2. at least 80% recall on the seeded decision facts or procedure gaps;
3. 100% citation coverage for claims presented as documented facts;
4. zero future-evidence leakage for ForkTrace, or deterministic reruns for
   PlanMutate;
5. a five-minute demo understandable without explaining vector databases; and
6. a differentiation sentence that remains true after directly comparing the
   prototype with its three closest competitors.

If neither passes, reject both and repeat concept discovery. That is cheaper and
more honest than forcing an ordinary RAG project into a novel-sounding description.

## Current recommendation

Advance **ForkTrace and PlanMutate only to validation probes**, not full
implementation. If forced to choose one before the probes, choose **ForkTrace**
because its temporal evidence boundary is easier to communicate, tightly uses the
existing provenance-aware RAG baseline, and creates a clear technical failure mode
that ordinary RAG does not address: hindsight leakage.

The strongest portfolio explanation would be:

> I did not build another document chatbot. I built a retrieval system that can
> replay a decision without cheating with future knowledge, separate evidence from
> assumptions, and show the exact later fact that should trigger reconsideration.
