# S_RAG portfolio evolution: problem-first red-team decision

Date: 2026-09-01

## Final outcome

This round tried to disprove all three problem-first candidates. Two are no-go and
one survives only in a narrower form.

| Candidate | Decision | Reason |
| --- | --- | --- |
| Handoff Trial | **Conditional go as HandoffProof** | The business problem and human validation workflow are established, but the exact product loop—controlled agent task replay that attributes failure to the handover corpus, asks the departing expert only for isolated missing knowledge, patches the corpus and reruns the task—did not surface as a current product in the bounded search. |
| PromiseLedger | **No-go as a standalone project** | Official infrastructure guidance already defines a live, versioned commitments register, and current products extract, structure, assign, monitor and evidence those commitments. A citizen-facing interface changes the audience more than the core mechanism. |
| AccessDrill | **No-go** | Commercial evacuation tools already model assisted evacuation, and current research automates floor-plan ingestion, code-grounded assessment and simulation. The remaining document-to-drill packaging is too small relative to the validation and safety burden. |

The selected direction is therefore **HandoffProof**, subject to a small mechanism
validation before product implementation. This is not approval to build a complete
application yet.

## The honest originality claim

The evidence does **not** support saying that nobody has ever thought of testing a
handover, diagnosing RAG failures, or using simulation for knowledge transfer.
Each of those ideas exists independently.

The defensible claim is narrower:

> HandoffProof is a controlled acceptance test for a handover corpus. A bounded
> successor agent attempts representative tasks using only approved handover
> evidence. Counterfactual reruns separate missing documentation from missed
> retrieval and agent inability. Only failures isolated to missing documentation
> become targeted expert questions; approved answers patch the corpus, and the same
> task is replayed to produce before/after proof.

The uncommon part is the **product contract and closed loop**, not a newly invented
retrieval algorithm:

```text
approved handover corpus
  -> representative task with deterministic success oracle
  -> bounded successor execution with cited evidence
  -> controlled failure attribution
  -> targeted expert question only when the corpus caused the failure
  -> approved corpus patch
  -> identical task replay
  -> handover acceptance or residual-risk record
```

This is a synthesis of known practices that were not found combined into the same
primary workflow during this research. That is strong enough for a distinctive
portfolio project if the mechanism works. It is not evidence for a universal
“never built before” claim, and it is not patent clearance.

## Red-team result 1: Handoff Trial

### What already exists

The surrounding market is crowded:

- [Flamekeeper](https://www.useflamekeeper.com/) identifies continuity risks,
  interviews leavers and colleagues, drafts handover documents, tracks actions and
  produces an approved pack.
- [TacitTransfer](https://tacittransfer.com/) maps role knowledge, decisions,
  exceptions and gaps into handover and onboarding artifacts.
- [Handover](https://www.gethandover.ai/) generates contextual questions, captures
  video or screen-share knowledge and creates a searchable knowledge base.
- [ExitNiq](https://www.exitniq.com/) conducts an AI exit interview, generates a
  handoff document and gives the successor a chat interface.
- [The University of Iowa's current guidance](https://hr.uiowa.edu/development/consultations-support/org-dev-toolkit/knowledge-transfer)
  already recommends using AI to interview the departing employee and identify
  missing or unclear material in SOPs and handover documents.

The core human practice is also established. A current knowledge-transfer checklist
recommends having the successor independently complete core workflows, reviewing
the gaps that surface, updating the documentation and only then signing off the
handover. This means “validate by doing” is not itself novel:
[Enboarder knowledge-transfer checklist](https://enboarder.com/blog/checklist-knowledge-transfer/).

Simulation-based knowledge transfer is mature in specialized domains. For example,
[Honeywell's process training simulator](https://process.honeywell.com/us/en/products/industrial-software/workforce-competency/workforce-competency)
uses realistic plant simulation to develop operator competency without risking the
real plant.

### The technical novelty also has prior art

RAG evaluation already separates retrieval and generation failures. Mature open
source frameworks make generic “RAG evaluation” a weak portfolio claim:

| Repository | Stars observed on 2026-09-01 | What it already covers |
| --- | ---: | --- |
| [DeepEval](https://github.com/confident-ai/deepeval) | 18,015 | LLM and RAG evaluation |
| [Ragas](https://github.com/vibrantlabsai/ragas) | 15,568 | RAG evaluation |
| [Phoenix](https://github.com/Arize-ai/phoenix) | 11,267 | AI observability and evaluation |
| [TruLens](https://github.com/truera/trulens) | 3,531 | LLM and agent experiment evaluation |

Recent research is even closer to the proposed causal controls:

- [Pair-ID](https://arxiv.org/abs/2608.08944) holds the query, retrieval state and
  reader constant while adding missing support and removing non-supporting evidence.
- [AgenticRAG-FP](https://arxiv.org/abs/2608.20627) injects known faults and uses
  counterfactual repairs to test causal failure attribution in multi-hop agentic RAG.
- [MissDiag](https://arxiv.org/abs/2608.18489) applies typed missing-evidence
  interventions while keeping the question and gold answer fixed.
- [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) already
  provides tasks in a simulated software company, so an office-task sandbox alone
  is not distinctive.

Therefore, “we use an agent to test documents” and “we diagnose RAG failures with
counterfactuals” are both insufficient claims.

### What survived

The bounded search did not find a current handover product whose primary loop does
all of the following:

1. accepts an approved, versioned handover corpus;
2. runs a bounded successor task against a deterministic oracle;
3. reruns the same task under controlled corpus and retrieval interventions;
4. distinguishes absent knowledge, failed retrieval and incapable agent behavior;
5. asks the available expert only for the missing facts isolated by the controls;
6. patches the approved corpus with provenance;
7. replays the same task and issues an evidence-bearing acceptance result.

This intersection is the remaining portfolio opportunity. The product is not an
HR offboarding assistant and not another RAG evaluation dashboard. It is a **proof
system for whether an operational handover package is sufficient for specified
tasks**.

### Required four-cell diagnosis

Every failed task must be rerun with the same model, tools, task and verifier:

| Corpus | Retrieval | Interpretation |
| --- | --- | --- |
| Sparse/actual | Normal | Real observed outcome |
| Sparse/actual | Oracle evidence selection | Tests whether the evidence exists but retrieval missed it |
| Gold/complete | Normal | Tests whether corpus repair is enough under the real retriever |
| Gold/complete | Oracle evidence selection | Capability ceiling; failure here is not a documentation gap |

Classification rules:

- **Corpus gap:** gold/complete succeeds while both sparse/actual arms fail.
- **Retrieval gap:** sparse/actual with oracle evidence succeeds while normal
  retrieval fails.
- **Agent/tool gap:** gold/complete with oracle evidence still fails.
- **Mixed or unresolved:** outcomes are unstable or multiple interventions are
  required; do not generate a confident expert question.

This design prevents the attractive but false result “the documentation is missing”
when the agent simply cannot perform the task.

### Why a real user may care

The manager's current sign-off often proves that files were produced and reviewed,
not that the contained knowledge supports the work. The established practice of
independent successor execution shows that task completion is the meaningful
acceptance standard. HandoffProof makes a bounded version repeatable before the
expert's final day and retains an auditable trace of what was tested, what failed,
what was added and what still needs a human successor.

The need is credible. Commercial demand is not yet proven. A synthetic technical
MVP can validate the mechanism and portfolio story, but only interviews or a pilot
could validate willingness to adopt or pay.

### Remaining kill conditions

Stop HandoffProof before full implementation if any of these occurs:

- repeated runs cannot reliably classify the seeded failure cause;
- a generated expert question is not necessary, specific and answerable from the
  seeded missing fact;
- the corpus patch improves prose but not deterministic task success;
- the agent succeeds through prior model knowledge or unrestricted search instead
  of the approved handover evidence;
- the agent fails most gold-corpus/oracle-retrieval tasks;
- the result cannot outperform a simple checklist plus human runbook walkthrough;
- a direct product with the same controlled acceptance loop is found.

### Decision

**Conditional go, renamed HandoffProof.** The broad Handoff Trial concept is too
easy to confuse with existing capture and training systems. The controlled
handover-corpus acceptance loop is the selected wedge.

## Red-team result 2: PromiseLedger

### Direct collision with the official workflow

The latest [UK Planning Inspectorate commitments-register guidance](https://www.gov.uk/guidance/nationally-significant-infrastructure-projects-commitments-register)
defines a register as a live document spanning scoping, application, examination,
decision and post-consent delivery. It specifically calls for tracking changes and
their reasons, how commitments are secured, discharged and monitored, and whether
early commitments remain at later stages.

That is extremely close to PromiseLedger's proposed lifecycle model. The source
material and public-interest need are real, but the conceptual record is already an
official part of the workflow.

### Current products close the remaining gap

- [EnSis](https://www.haskoning.com/en/services/ensis-commitment-management-platform)
  generates and structures commitments registers, links commitments to source
  information, removes duplicates, assigns work and tracks evidence of compliance.
- [CompliantMine](https://compliantmine.com/obligation-register/) maintains legal,
  permit and ESIA obligations with ownership, status and evidence.
- [KNOY](https://knoy.app/) turns environmental project folders into cited
  requirements matrices, issue registers, commitments registers and missing-
  information lists.

A public, journalist-oriented view is useful, but public access and semantic
cross-version matching do not create enough separation from the required register
plus current extraction/tracking systems. Labels such as “weakened” also introduce
legal and political judgment that a portfolio MVP cannot validate responsibly.

### Decision

**No-go as a standalone portfolio project.** A later civic product could reuse the
provenance and version-diff idea as a feature, but S_RAG should not be repositioned
around it.

## Red-team result 3: AccessDrill

### The core simulation is already mature

[Pathfinder](https://www.thunderheadeng.com/pathfinder/) is an established agent-
based egress simulator with CAD/BIM import, behavior modeling and validation tests.
Its [assisted-evacuation documentation](https://www.thunderheadeng.com/docs/2025-1/pathfinder/advanced/assisted-evacuation/)
explicitly models wheelchair users, hospital beds, assistants, teams, refuges and
partial-route assistance.

The [Federal Railroad Administration](https://railroads.dot.gov/elibrary/evaluation-egress-models-passenger-rail-cars-emergency-and-non-emergency-scenarios)
has evaluated commercial egress models including Pathfinder and railEXODUS, further
showing this is an established engineering category rather than an open product
space.

Current research also reaches directly into the proposed AI workflow.
[ChatEvac](https://doi.org/10.1016/j.engappai.2026.116075) automates evacuation
assessment from uploaded floor plans using segmentation, simulation, LLM
orchestration, retrievable building-code provisions and human review.

### Safety burden defeats the remaining wedge

The remaining distinction—retrieving written plan clauses and turning simulated
failures into drill injects—is an output layer on top of mature simulation. It does
not justify rebuilding the simulation stack, and a simplified model would carry a
high risk of producing persuasive but invalid safety claims. Pathfinder itself
warns that its results supplement qualified judgment and may not predict a specific
real situation.

### Decision

**No-go.** The concept is important, but it is neither sufficiently open nor safely
demonstrable at this project's scope.

## Why HandoffProof is worth one validation round

It has four portfolio strengths that the rejected candidates lost:

1. **A visible before/after claim:** the same task fails, the isolated missing fact
   is captured, and the same task then passes.
2. **RAG is structurally necessary:** the system must restrict execution to an
   approved, versioned handover corpus and preserve evidence used at each step.
3. **The second AI capability has a real job:** the agent executes bounded work;
   it does not merely produce another answer.
4. **The hardest criticism is measurable:** the four-cell controls can falsify the
   claim that documentation caused a failure.

The five-minute portfolio explanation becomes:

> Most handover AI writes documents. HandoffProof tests them. A successor agent
> attempts real, sandboxed tasks using only the approved handover corpus. Controlled
> reruns show whether failure came from missing knowledge, bad retrieval or the
> agent itself. It asks the departing expert only for proven gaps, patches the
> source with provenance and reruns the same task to produce an acceptance record.

## Next step: mechanism validation, not product construction

The next authorized phase should be a deliberately small experiment:

- one synthetic software service;
- four representative tasks, not ten;
- one deterministic verifier per task;
- one seeded corpus gap, one seeded retrieval miss, one seeded agent/tool failure
  and one fully supported control;
- repeated runs to measure classification stability;
- a hand-written gold set for required evidence and expert questions;
- checklist, full-context and normal-RAG baselines;
- no HR system, authentication, multi-user product, polished UI or deployment.

Passing target:

- at least 90% seeded-cause classification accuracy across repeated runs;
- zero corpus-gap claims when the gold/oracle arm fails;
- every proposed expert question maps to a gold missing fact and exact task step;
- at least three of four tasks reproduce their expected before/after behavior;
- all successful task actions cite approved evidence or deterministic tool output.

Only after that result should architecture and UI design begin.

## Research limits

This was a bounded search of current product pages, official guidance, research,
patent keywords and GitHub repositories under multiple descriptions. It can support
“no direct product was found in this search”; it cannot prove universal novelty,
market demand, freedom to operate or safety. Product pages describe vendor claims,
not independently verified capability. GitHub star counts are a dated snapshot and
measure attention, not technical quality.
