# S_RAG portfolio evolution: problem-first discovery

Date: 2026-08-31

> **Status:** Superseded by the adversarial decision in
> [`06-problem-first-red-team-decision.md`](06-problem-first-red-team-decision.md).
> Handoff Trial survived only as the narrower **HandoffProof** mechanism-validation
> candidate. PromiseLedger and AccessDrill are no-go. No product implementation has
> started.

## Outcome

The previous concept-search cycle correctly ended with a no-go. This new cycle does
not search for an unusual feature to attach to RAG. It starts with difficult,
expensive or neglected workflows and asks whether RAG is necessary inside a product
that produces a real action artifact.

The first pass rejected seven crowded directions and retained three candidates for
adversarial research:

1. **Handoff Trial — prove whether a role handover works by attempting representative
   tasks before the expert leaves**
2. **PromiseLedger — trace public-project commitments across changing documents and
   show which promises have evidence, changed meaning or disappeared**
3. **AccessDrill — stress-test evacuation plans against disability-specific scenarios
   and produce concrete drill failures rather than generic accessibility advice**

These are discovery candidates only. None is selected or approved for implementation.

## The new search rule

The product must be explainable without mentioning RAG first:

> A specific user has a costly job. The system produces an artifact that changes
> what the user can test, approve, challenge, repair or execute. RAG is necessary
> because the job depends on retrieving the correct evidence from messy, changing
> source documents.

“RAG plus agents,” “RAG plus vision” and “RAG plus a knowledge graph” are not product
ideas. Those technologies may appear only after the user job is defensible.

## Gates for this cycle

A candidate advances only if it has all of the following:

1. **Named user and moment:** who uses it, and at what exact point in a workflow?
2. **Painful failure:** what happens today when the job is done badly?
3. **Action artifact:** what exists after use other than an answer or summary?
4. **Structural RAG need:** why must the system retrieve versioned, scoped evidence?
5. **Second AI capability with a job:** simulation, execution, vision or another
   technique must verify or transform something—not decorate the demo.
6. **Portfolio data:** the central claim can be demonstrated with public, synthetic
   or safely generated data without pretending it is production evidence.
7. **Objective evaluation:** at least one core result can be scored without asking
   an LLM to judge its own prose.
8. **Five-minute distinction:** a reviewer can see why it is not “chat with PDFs.”
9. **Prior-art survival:** the exact user job and output contract survive product,
   research, patent and GitHub searches.

## Directions rejected in the first pass

### 1. Organization-grounded tabletop exercise generator

**Reject.** This looked strong because it turns plans into exercises, timed injects,
scoring and after-action reports. The workflow is already a current product category.

- [ORNA](https://www.orna.app/) uploads incident plans, playbooks, policies and
  network diagrams to customize AI cyber exercises.
- [Opsbook](https://opsbook.ai/) connects organizational documents, playbooks,
  exercises and after-action reports, traces findings to sources and recommends
  improvements.
- [Tabletop.ai](https://www.tabletop.ai/) generates custom, red-teamed exercises,
  role-specific injects, after-action reports and governance artifacts.
- [Transilience](https://www.transilience.ai/platforms/tabletop-exercise) generates
  exercises from live asset inventories and scores role-specific responses.

The market is not merely adjacent; it already uses the proposed input and output.

### 2. Legacy-system decommissioning rehearsal

**Reject.** Dependency discovery, application retirement, archive preservation and
safe shutdown are mature enterprise categories.

- [Cella](https://cellasoftware.com/) reports more than 600 systems decommissioned
  and preserves searchable, compliant legacy data.
- [OpenText](https://www.opentext.com/uk/solutions/legacy-application-decommissioning)
  provides legacy application decommissioning and governed archival access.
- Application portfolio tools already map dependencies to understand migration and
  decommissioning impact.
- A 2026 patent application, [US20260133778](https://patents.justia.com/patent/20260133778),
  explicitly covers data-application linkages and dependent-entity decommissioning.

A “rehearsal” interface would narrow the experience, not create a defensible product
center.

### 3. Permit or regulation-to-workflow compiler

**Reject.** Products already review submitted documents against local rules, extract
permit obligations and generate trackable workflows.

- [PermitSight](https://permitsight.ai/) reviews permit submissions against
  checklists, rules and code requirements with source-backed findings.
- [Oracle Public Sector Permitting](https://docs.oracle.com/en/cloud/saas/public-sector-compliance-regulation-common/26b/pscii/implementing-your-cloud-integrations.pdf)
  includes AI-assisted plan review and inspection summaries.
- [PermitAI](https://www.pnnl.gov/projects/permitai) is a national-laboratory effort
  applying AI to environmental-review and permitting documents, processes, public
  comments and geographic records.
- Recent research already derives traceable software requirements from regulation:
  [regulation-to-requirements pipeline](https://arxiv.org/abs/2607.04448).

### 4. Engineering substitute validator

**Reject.** BOM risk, obsolete-part detection, alternative discovery and datasheet-
backed form-fit-function comparison are active commercial capabilities.

- [Z2Data](https://www.z2data.com/landing/lpb/cross-reference) grades alternatives,
  compares electrical/package/compliance properties and flags engineering-review
  risk.
- [PartGenie](https://www.partgenie.ai/ai-bom-analyzer) finds BOM alternatives with
  datasheet evidence and human approval.
- August 2026 research already combines datasheets, design graphs and deterministic
  compatibility scripts: [datasheet-aware hardware compatibility
  verification](https://arxiv.org/abs/2608.25217).

### 5. Assurance-case or regulatory-change compiler

**Reject.** Assurance-case creation and maintenance are established disciplines,
and current work already applies agentic RAG to the exact workflow.

- Safety-case change impact was studied decades ago:
  [systematic safety-case maintenance](https://doi.org/10.1016/S0951-8320(00)00079-X).
- Automated assurance-case instantiation with LLMs is active research:
  [assurance cases from patterns](https://arxiv.org/abs/2410.05488).
- An August 2026 paper is directly titled
  [An Agentic RAG and Evaluation Framework for Assurance Case
  Generation](https://arxiv.org/abs/2608.19509).

### 6. Video-based SOP adherence verifier

**Reject.** The combination of procedure documents, temporal vision and step-level
verification is technically attractive but already commercialized and researched.

- [Indra](https://indra.software/) markets real-time procedural verification in
  which AI agents verify each step against an SOP.
- [Darkfield](https://linox.co.uk/use-cases/sop-adherence.html) detects whether SOP
  steps occurred in the correct order and duration.
- [IndustReal](https://github.com/TimSchoonbeek/IndustReal) provides a public
  procedure-step-recognition dataset with execution errors.
- [STORM-PSR](https://arxiv.org/abs/2510.12385) recognizes correctly completed
  procedural steps and their order in egocentric video.

### 7. Denial-to-appeal evidence packet

**Reject.** Healthcare and insurance appeal generation is exceptionally crowded.
Current products already ingest denial letters and records, retrieve payer policies
and clinical guidance, identify missing evidence, generate submission-ready appeal
packets and track outcomes. Examples include
[WestHeal](https://westheal.com/), [Appealio](https://appealio.co/) and
[GetPreAuth](https://getpreauth.com/).

## Candidate 1: Handoff Trial

### One-line explanation

**Most knowledge-transfer tools help a departing expert create more documentation.
Handoff Trial gives a simulated successor representative tasks, lets it work only
from the approved handover corpus, and converts every blocked or wrongly completed
step into a targeted question while the expert is still available.**

### User and moment

An engineering manager, operations lead or knowledge-management owner uses it during
the notice period of a specialist, before the final handover is approved.

### Why the problem is real

NASA's report on [ensuring knowledge continuity during employee
transitions](https://ntrs.nasa.gov/api/citations/20210026226/downloads/Ensuring%20Knowledge%20Continuity%20during%20Employee%20Transitions%20Report.pdf)
recommends structured capture around departures and explicitly suggests asking
colleagues what knowledge they fear losing.

Current products focus on capture:

- [TacitTransfer](https://tacittransfer.com/) maps role knowledge, gaps and
  continuity risks.
- [Flamekeeper](https://www.useflamekeeper.com/) uses guided interviews to capture
  tacit knowledge and produce a reviewed handover.
- [Stepwright](https://www.stepwright.com/use-cases/knowledge-transfer/) records an
  expert performing tasks and turns that performance into instructions.

The first search did not find a dominant product whose primary acceptance test is:
**can a bounded successor actually complete representative tasks using only the
handover package?**

### Action artifact

A **handover acceptance packet**:

- representative task and success oracle;
- retrieved handover evidence used at each step;
- completed, blocked, guessed and incorrectly completed steps;
- exact missing fact, access, exception or decision rule;
- targeted interview question for the departing expert;
- approved answer and resulting document patch;
- before/after task replay result;
- residual risks requiring a human successor.

### Why RAG is necessary

The test subject must operate from a scoped, versioned collection of runbooks,
architecture notes, tickets, handover files and approved examples. Retrieval quality
is part of the result: failure may mean the fact is absent, poorly indexed or buried
under the wrong terminology.

### The second AI capability

A sandboxed task agent performs bounded tasks and records its execution trace. RAG
supplies evidence; task execution tests whether the evidence is operationally
sufficient.

### Portfolio MVP

Create a synthetic but realistic small service owned by a departing maintainer:

- repository, runbooks, architecture notes and ticket history;
- ten representative tasks with hidden deterministic acceptance tests;
- deliberately missing exception knowledge in four tasks;
- a simulated expert-answer round that patches the handover package;
- replay showing which tasks become solvable.

### Objective evaluation

- task success before and after knowledge capture;
- unsupported action and guess rate;
- retrieval recall for task-critical facts;
- missing-knowledge localization precision;
- percentage of generated expert questions judged necessary by a gold set;
- replay reproducibility;
- comparison against full-context, direct-search and no-RAG baselines.

### Main kill condition

Agent failure may reveal a weak agent rather than weak documentation. The candidate
survives only if controlled oracle-document and oracle-tool experiments can separate
agent capability failure from knowledge-corpus failure.

### Discovery verdict

**Advance to adversarial research. Current rank: 1.**

## Candidate 2: PromiseLedger

### One-line explanation

**PromiseLedger reconstructs the lifecycle of a public infrastructure commitment—
where it was made, how later documents changed it, how it was legally secured and
what public evidence shows it was completed—without treating a progress statement
as proof.**

### User and moment

A local journalist, civil-society researcher or affected community uses it after a
large project is approved and new amendments, construction plans, monitoring reports
and progress updates begin to accumulate.

### Why the problem is real

Official environmental guidance treats a commitment register as a mechanism for
making mitigation measures traceable, assigning responsibility and monitoring
implementation. Public planning files already include large
[commitment trackers](https://infrastructure.planninginspectorate.gov.uk/wp-content/ipc/uploads/projects/TR050006/TR050006-001193-Doc%206.11B%20-%20Updated%20Commitments%20Tracker.pdf),
but the evidence is distributed across versions and later project records.

Adjacent systems prove the need while also defining the competition:

- [CompliantMine](https://compliantmine.com/) turns permit and ESIA conditions into
  an operator-facing obligations register with evidence and corrective actions.
- [InfraTracker](https://www.infratracker.org/en/about) is a public-interest system
  that traces infrastructure cost facts to source documents.
- [Cloudsyte](https://cloudsyte.com/) tracks public-program delivery and commitments.

The possible wedge is citizen-side **semantic commitment lineage**, not internal
compliance management or generic project tracking.

### Action artifact

A **public commitment lifecycle record**:

- original promise and exact source;
- project phase, location, responsible party and trigger;
- legal or procedural mechanism said to secure it;
- semantically corresponding text in each later version;
- narrowed, weakened, split, deferred, superseded or missing changes;
- implementation claim separated from independent evidence;
- unresolved evidence request suitable for a journalist or public-record inquiry.

### Why RAG is necessary

The same commitment changes wording and location across environmental statements,
consultation responses, permits, amendments, contractor plans and monitoring
reports. Semantic retrieval, temporal entity resolution and provenance are central
to following it without losing its scope.

### The second AI capability

A temporal provenance graph represents commitment versions and evidence events.
Deterministic diff rules and human review constrain the LLM's semantic matches.

### Portfolio MVP

Use one public infrastructure project with a bounded set of official documents.
Hand-label 30 commitments across three document generations and seed several
controlled weakening, disappearance and evidence-status cases.

### Objective evaluation

- commitment extraction precision/recall;
- cross-version identity-link accuracy;
- change-type classification accuracy;
- exact citation coverage;
- unsupported “completed” claim rate;
- temporal ordering accuracy;
- agreement with a small human-authored gold ledger.

### Main kill conditions

- a current product already exposes public, cross-version commitment lineage;
- deciding “weakened” requires legal interpretation that the system cannot support;
- project websites do not provide stable, machine-collectable source documents;
- the output becomes a political claim generator rather than an evidence tracker.

### Discovery verdict

**Advance cautiously to adversarial research. Current rank: 2.**

## Candidate 3: AccessDrill

### One-line explanation

**AccessDrill does not merely check whether an evacuation plan mentions disability.
It constructs a concrete building-and-occupant scenario in which the written plan
cannot evacuate someone safely, then turns that failure into a drill inject and a
source-cited review question.**

### User and moment

A facility safety lead, accessibility officer or emergency-planning reviewer uses
it before approving or rehearsing an evacuation plan.

### Why the problem is real

Research on [emergency evacuation of people with
disabilities](https://doi.org/10.1080/23311916.2018.1506304) reports that many models
and drills inadequately represent disability-specific behavior, accessible
wayfinding and real-world uncertainty.

This is not an empty technical field:

- [exitus](https://doi.org/10.1016/j.eswa.2012.01.169) used agent-based simulation
  to evaluate evacuation strategies for people with disabilities.
- A 2025 [digital-twin review](https://doi.org/10.1016/j.aei.2025.103419) covers
  building/occupant simulation, planning and risk assessment.
- Recent [inclusive crowd simulation](https://pubmed.ncbi.nlm.nih.gov/41068262/)
  explicitly models wheelchair users and visually impaired occupants.

The possible wedge is not evacuation simulation itself. It is compiling messy plan
documents, staff assignments and floor constraints into **reviewable failure
witnesses and drill injects**.

### Action artifact

An **inclusive evacuation failure packet**:

- concrete occupant, location, hazard and unavailable-resource scenario;
- plan clauses and floor constraints used;
- simulated transition at which evacuation becomes blocked;
- inaccessible or ambiguous dependency;
- drill inject that tests the same dependency with humans;
- review question and proposed owner;
- explicit model assumptions and refusal to claim real-world safety.

### Why RAG is necessary

Roles, elevator rules, refuge areas, communication methods, assistance assignments
and exception procedures are distributed through emergency plans, accessibility
policies, floor plans and contact documents. A simulation is meaningful only if its
constraints remain traceable to the correct source and version.

### The second AI capability

A small agent-based or graph simulation searches for blocked states. The LLM helps
extract candidate constraints; the simulator, not the LLM, produces the failure
trace.

### Portfolio MVP

Use a synthetic two-floor facility, an intentionally incomplete plan and several
occupant profiles. Seed inaccessible routes, missing assistants, failed audible
alerts and contradictory elevator assumptions. Generate drill packets, never live
emergency instructions.

### Objective evaluation

- constraint-extraction accuracy;
- seeded failure recall and false-positive rate;
- validity and minimality of the simulated failure trace;
- citation coverage;
- drill-inject coverage of discovered failures;
- correct refusal when geometry or plan data is insufficient.

### Main kill conditions

- prior art shows the exact document-to-failure-witness workflow;
- simplified simulation produces misleading safety conclusions;
- floor-plan extraction is too large a dependency for a credible MVP;
- domain experts would not use generated scenarios without expensive validation.

### Discovery verdict

**Advance cautiously to adversarial research. Current rank: 3.**

## Comparative discovery score

Scores are early research judgments from 1 to 10, not market facts.

| Candidate | Need | Distinct job after first search | RAG necessity | Demo strength | Public/MVP data | Objective evaluation | Overall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Handoff Trial** | 9 | 8.5 | 8.5 | 10 | 8 | 9.5 | **8.9** |
| **PromiseLedger** | 9 | 8 | 9.5 | 9 | 9.5 | 9 | **8.8** |
| **AccessDrill** | 10 | 7.5 | 8.5 | 10 | 7 | 9 | **8.7** |

## Why Handoff Trial currently leads

It produces the strongest before/after proof:

```text
handover documents exist
  does not prove a successor can do the work

representative task replay
  exposes the exact missing knowledge
  asks the expert while they are still available
  reruns the task after repair
```

The result is visually clear, reuses the current local document pipeline, adds a
meaningful agent/sandbox capability and can be measured with deterministic task
oracles. Its central risk is equally measurable: an agent can fail even when the
documentation is sufficient.

## Required next round

Do not select Handoff Trial yet. The next round must try to kill all three by:

1. searching patents and products under alternate vocabulary;
2. finding direct implementations hidden inside adjacent categories;
3. testing whether the claimed output changes a real user's work;
4. checking whether the MVP can prove more than a synthetic demo;
5. defining a non-LLM gold set and baseline for every core claim;
6. deciding one-survivor, narrower-survivor or no-go without forcing a build.

No architecture, UI design or implementation begins before that round.
