# S_RAG portfolio evolution: Round 2 reverse-RAG concept search

Date: 2026-08-31

> **Status:** Superseded by the final red-team decision. All three shortlisted
> concepts received a no-go verdict. See
> [04-final-red-team-decision.md](04-final-red-team-decision.md).

## Outcome

Generic **Reverse RAG**—an assistant that detects missing information and asks the
next best question—is useful, but it is not sufficiently original as a standalone
product. Active-reasoning, active-information-acquisition and diagnostic-agent
research already studies this exact capability.

The research direction was still productive. It exposed three narrower product
contracts that appear less occupied and are stronger than “ask a better follow-up
question”:

1. **NullProof — corpus-bounded proof of absence and universal-claim verification**
2. **CollisionWitness — generate the smallest concrete scenario that makes two
   natural-language rules conflict**
3. **ShadowSOP — find recurring work performed during real exceptions but missing
   from the official procedure**

These are **Round 2 candidates, not selected products**. Each has adjacent prior
art and serious technical risk. They advance to the next red-team round only.

## What “less spoken about” means here

This document does not claim that nobody has ever considered these ideas. That is
not provable. The narrower and defensible claim is:

> A repeatable search on 2026-08-31 found active research on the component
> technologies, but did not find a dominant open-source project or commercial
> product publicly centered on the exact user job, output contract and evaluation
> described for the three shortlisted concepts.

The next round must try to falsify that statement using different terminology,
patent searches, adjacent industries and the strongest possible competitor framing.

## Round 2 gates

A concept may advance only if it satisfies all of these:

1. **Real failure:** authoritative sources, research or observed practice show that
   the underlying problem causes meaningful errors, rework, delay or risk.
2. **Different product job:** the output changes what a user can safely do; it is
   not merely a better answer, summary, graph or interface.
3. **RAG is structurally necessary:** source selection, corpus scope and provenance
   are part of correctness, not decorative citations.
4. **Non-LLM verification exists:** at least one core claim can be checked through
   deterministic coverage, constraints, replay or a hand-authored gold set.
5. **Honest uncertainty:** the UI can separate verified, inferred, missing and
   untestable states.
6. **Local MVP:** one engineer can demonstrate the central claim on a synthetic but
   realistic corpus without pretending to have production integrations.

## Research finding 1: generic Reverse RAG is already an active field

[AR-Bench](https://arxiv.org/abs/2506.08295) distinguishes passive reasoning from
active reasoning, where a model must acquire missing evidence. Its experiments find
that current models frequently fail to collect or use the information needed to
solve a task. The accompanying [AR-Bench repository](https://github.com/tmlr-group/AR-Bench)
had 47 public stars in the 2026-08-31 GitHub snapshot.

[MT-InfoSeek](https://arxiv.org/abs/2608.14808) evaluates what models ask, when they
ask it and whether the acquired information is sufficient. It reports that models
often underestimate how much information is missing, fail to identify a minimal
sufficient query set and stop too early.

[LLM-as-an-Investigator](https://arxiv.org/abs/2606.13220) is even closer to the
initial product idea. It generates competing explanations, asks targeted questions,
updates hypothesis probabilities and continues until evidence favors one
explanation. It evaluates the method on solved mechanical, electrical and hydraulic
diagnostic cases.

[Zero-Shot Active Feature Acquisition](https://arxiv.org/abs/2606.18933) studies
which missing feature should be observed next to reach a classification or ranking
decision. This connects the “smallest decisive evidence” idea to an established
technical field.

**Conclusion:** “RAG that asks what it needs next” is a valuable research direction,
not a unique portfolio identity. Active acquisition can support a narrower product,
but should not be the headline.

## Research finding 2: preserving multiple realities is also established

[LLM-as-an-Investigator](https://arxiv.org/abs/2606.13220) already maintains and
tests alternative explanations during diagnosis.

[EMR-ACH](https://github.com/ApartsinProjects/EMR-ACH) applies the established
Analysis of Competing Hypotheses method to LLM-based geopolitical forecasting using
an auditable evidence matrix. Its direct GitHub footprint was small—1 star in the
2026-08-31 snapshot—but the underlying analytical method is old and well known.

[PRISM](https://www.prism4research.com/) explores pluralistic reasoning paths and
dynamic epistemic graphs for open-ended scientific work. Other evidence graphs and
contested-claim tools similarly preserve disagreement instead of collapsing it.

**Conclusion:** “AI keeps several hypotheses alive” is not enough. A surviving
concept needs a more unusual object that it produces, such as a verified
counterexample or a minimal disambiguating observation.

## Research finding 3: gap detection and decision gates are crowded broadly

[AbsenceBench](https://huggingface.co/papers/2506.11440) evaluates whether models
can identify missing content and finds important limitations. More recent
[completeness-sensitive negative-reasoning research](https://arxiv.org/abs/2608.04591)
shows that absence and partial corpus coverage remain difficult.

[Improving Requirements Completeness](https://arxiv.org/abs/2308.03784) studies
automated suggestions for missing terminology in natural-language requirements.
[RAGLint](https://github.com/Prashanth1998-18/raglint) is a small 2026 open-source
corpus-auditing project for contradictions, duplicates, stale content and metadata
completeness.

Commercial products also cover the broad readiness promise:

- [Tiebreaker AI](https://www.tiebreaker-ai.com/) shows covered, partial and missing
  audit/vendor/compliance evidence.
- [Colabra Reconcile](https://www.colabra.ai/docs/flag-and-screen/reconcile-gap-analysis/)
  links evidence gaps to document or clarification requests.
- [Assumption Mapper](https://assumption-mapper.com/) grades evidence, tracks
  contradictions and records decisions.
- Multiple new open-source “decision gate” repositories separate supported claims,
  verification, approval and action.

**Conclusion:** “knowledge gap detector” and “evidence readiness dashboard” are too
broad. The missing-information problem must be bound to a claim type that has an
objective proof obligation.

## Six concrete concepts considered

### A. EvidenceRoute — minimal next-evidence planner

#### Promise

Given a decision, identify the lowest-cost question, test, measurement or document
that is most likely to change the conclusion.

#### Example

For a production migration, the system might determine that another architecture
document adds little information, while a five-minute rollback timing test would
separate the two remaining risk hypotheses.

#### Verdict: reject as a standalone product

The need is real, and the capability should remain available to other concepts.
However, active reasoning, active feature acquisition, value-of-information methods
and investigator agents already occupy this intellectual territory. Without a very
specific domain, this is a research reproduction rather than a distinct product.

### B. SplitWorld — competing-reality workbench

#### Promise

Preserve several plausible explanations, map evidence for and against each, and ask
the question that best separates them.

#### Verdict: reject as a standalone product

Analysis of Competing Hypotheses, evidence matrices, diagnostic agents and
pluralistic reasoning systems already cover the broad job. The multi-hypothesis
representation can support CollisionWitness, but it is not enough on its own.

### C. NullProof — corpus-bounded proof of absence

#### One-line explanation

**Ordinary RAG can prove that a statement appears somewhere by retrieving one
witness. NullProof determines whether the system has searched enough to claim that
the statement appears nowhere—and refuses the negative claim when coverage is not
provable.**

#### User problem

Many consequential questions are negative, universal, numerical or superlative:

- “Does no contract permit subcontracting without approval?”
- “Do all policies require breach notification within 72 hours?”
- “Are there any exceptions to the encryption requirement?”
- “How many procedures reference the retired administrator account?”
- “Which document contains the earliest approval deadline?”

Top-k retrieval is suitable for existential questions: one valid passage can prove
that something exists. It cannot establish an absence or universal rule because the
answer makes a claim about the unread remainder of the corpus.

#### Distinct output contract

NullProof does not return a normal yes/no answer. It returns one of four bounded
verdicts:

1. **Present:** one or more cited witnesses prove existence.
2. **Counterexample found:** a cited document disproves a universal claim.
3. **Absent within the verified snapshot:** the declared corpus and parser coverage
   satisfy the claim-specific search contract, and no witness was found.
4. **Not provable:** some files, pages, modalities, languages, queries or semantic
   regions were not covered sufficiently.

Every negative verdict includes a coverage receipt:

- frozen corpus manifest and content hashes;
- successfully parsed files/pages and explicit failures;
- claim quantifier and required coverage class;
- lexical, semantic and structured query families executed;
- documents/chunks examined;
- adversarial paraphrase and exception search;
- unresolved OCR, table, image or language gaps;
- model/tool versions and deterministic rerun identifier.

This proves absence only **relative to a declared corpus snapshot and declared
coverage contract**. It never claims real-world nonexistence.

#### Why this is different from abstention and hallucination detection

An ordinary RAG system abstains when top-k retrieval finds weak evidence. That does
not explain whether the corpus lacks the answer or the retriever failed to find it.
NullProof treats negative and universal claims as different computational jobs with
different coverage requirements.

[Chunk Coverage](https://arxiv.org/abs/2607.18155),
[semantic-stratification research](https://arxiv.org/abs/2604.20763), and
[Q-CARE](https://arxiv.org/abs/2608.11238) demonstrate growing interest in
coverage-aware RAG evaluation. [Future AGI](https://github.com/future-agi/future-agi)
is a substantial general LLM evaluation platform. These are important adjacent
systems, but the search did not find a dominant end-user product whose primary
workflow is corpus-bounded negative-claim certification.

#### Why it is useful

The same proof obligation appears across contract review, compliance, requirements,
security policies, procurement evidence, audit preparation and technical
documentation. It addresses a structural RAG failure rather than a particular
industry vocabulary.

#### Why RAG is necessary

Semantic retrieval is still needed to discover varied ways a concept, exception or
permission may be expressed. But it must be combined with corpus manifests,
exhaustive coverage accounting, exact search, query expansion, structured
extraction and claim-specific stopping rules.

#### Five-minute portfolio demo

Use 40 synthetic supplier agreements. Ask:

> “No agreement permits subcontracting without written approval. Is that true?”

Normal RAG retrieves five agreements that require approval and confidently agrees.
NullProof refuses until the complete snapshot is covered, then finds one exception
on page 47 of agreement 31 and returns it as a counterexample. A second run contains
an unreadable scanned appendix; the system reports **Not provable**, even when no
textual exception is found.

#### Objective evaluation

- zero false “absent” verdicts on seeded counterexamples;
- corpus/file/page/parser coverage accuracy;
- witness and counterexample recall;
- negative/universal/count claim classification accuracy;
- query-family mutation coverage;
- certificate reproducibility;
- correct distinction between corpus absence and retrieval failure;
- latency and resource cost by assurance level.

#### Kill conditions

- semantic coverage cannot be defined without circular LLM judgment;
- the receipt creates an appearance of proof while hiding parser failures;
- exhaustive checks are too slow for even the small intended corpus;
- close competitor research reveals the same end-user workflow;
- reviewers cannot understand the bounded meaning of “absent.”

#### Round 2 assessment

**Advance to the red-team round. Current rank: 1.**

### D. CollisionWitness — counterexample generator for document rules

#### One-line explanation

**Most tools highlight sentences that sound contradictory. CollisionWitness
constructs the smallest concrete situation in which two rules both apply but demand
incompatible actions, then cites every clause used to produce that witness.**

#### User problem

Rules can look compatible when reviewed independently but collide only under a
specific combination of role, system state, timing and exception. For example:

- Policy A permits emergency production access to the on-call engineer.
- Policy B prohibits all contractor production access.
- The ownership matrix allows a contractor to be the on-call engineer.

The conflict becomes visible only in the witness:

> Severity-1 incident; primary employee unavailable; contractor is the current
> on-call engineer; production access is required.

NASA says requirements should not conflict as a set, and its engineering guidance
explicitly asks whether requirements conflict with domain constraints, system
constraints, policies or regulations.
[NASA reference](https://www.nasa.gov/reference/system-engineering-handbook-appendix/).

NIST has long worked on access-control policy composition, verification, testing and
fault detection because policy misconfiguration can create serious security
vulnerabilities. [NIST ACPT](https://www.nist.gov/identity-access-management/projects/control-policy-test-technologies-acpt-and-acrlcs).

#### Adjacent work

- [policy-contradictions-nlp](https://github.com/parkeraddison/policy-contradictions-nlp)
  finds likely contradictory sentence pairs using embeddings and NLI.
- [Prose2Policy](https://machinelearning.apple.com/research/prose2policy) converts
  natural-language access rules into executable Rego and tests them.
- [counterexample-guided specification validation](https://apartresearch.com/project/counterexampleguided-validation-repair-of-llmgenerated-safety-specifications-0s4g)
  uses formal counterexamples to repair LLM-generated safety specifications.
- SMT and policy-verification research already handles conflicts after rules have
  been formalized.

Therefore neither “contradiction detection” nor “natural language to formal policy”
is novel. The narrower wedge is an end-user workflow centered on a **minimal,
human-readable, source-cited conflict witness across heterogeneous documents**.

#### Product flow

1. Extract typed rules, conditions, exceptions, actors and actions with provenance.
2. Require human review of ambiguous or inferred predicates.
3. Translate accepted rules into a constrained intermediate representation.
4. Use SAT/SMT or bounded enumeration to find a satisfying conflict assignment.
5. Minimize the assignment so the smallest understandable scenario remains.
6. Render the witness in plain language with exact source citations.
7. Suggest candidate rule clarifications without automatically changing policy.

#### Five-minute portfolio demo

Upload an access policy, incident policy and ownership matrix. The UI shows no
obvious sentence-level contradiction. Press **Find collision witness** and receive
the four-condition scenario above, the two incompatible required actions, the solver
result and the source passages.

#### Objective evaluation

- rule/predicate/exception extraction precision and recall;
- seeded conflict detection precision and recall;
- formal witness validity;
- witness minimality;
- citation coverage;
- false collision rate;
- human agreement that the witness reflects the source text;
- repair regression tests.

#### Kill conditions

- natural-language translation errors dominate solver correctness;
- most useful policy concepts cannot be represented in the bounded schema;
- witnesses are technically satisfiable but operationally absurd;
- Prose2Policy or another direct competitor already exposes the same cited-witness
  workflow;
- the concept collapses back into generic policy linting.

#### Round 2 assessment

**Advance to the red-team round. Current rank: 2.**

### E. ShadowSOP — mine undocumented exception work

#### One-line explanation

**ShadowSOP compares what the official procedure says should happen with what
incident narratives, tickets and handoff notes show people repeatedly did when the
normal procedure failed. It turns recurring undocumented recovery work into cited
procedure-gap candidates.**

#### User problem

Organizations often document the happy path. Real exceptions are handled through
Slack messages, tickets, incident timelines and expert improvisation. The workaround
may succeed repeatedly without ever becoming part of the official procedure.

CISA's incident-response playbook explicitly asks teams after an incident to
identify insufficient processes, policies needing modification, unclear roles,
undefined authority, training gaps and planning deficiencies.
[CISA playbook](https://www.cisa.gov/sites/default/files/publications/Cybersecurity_Incident_Vulnerability_Response_Playbooks_508C.pdf).

#### Adjacent work

Process mining is an established field, and [PM4Py](https://github.com/process-intelligence-solutions/pm4py)
had 1,019 public stars in the 2026-08-31 snapshot. [ProMoAI](https://github.com/fit-process-mining/ProMoAI)
is a 61-star LLM/process-modeling project.

Recent research makes this concept less empty than it first appears:

- [Process mining between the lines](https://doi.org/10.1016/j.is.2026.102713)
  extracts object-centric event logs from unstructured text and notes that text
  contains exceptions and manual activities missing from structured data.
- [Integrating domain knowledge into process discovery](https://arxiv.org/abs/2510.07161)
  combines natural-language rules, event logs, experts and process discovery.
- Incident-knowledge tools already summarize postmortems and recurring failure
  patterns.

#### Narrow wedge that may remain

ShadowSOP is not general process discovery. Its artifact is a source-cited
**documentation debt register**:

- observed recovery action;
- incidents/tickets in which it occurred;
- official step it bypassed or extended;
- trigger condition;
- role that performed it;
- success/failure evidence;
- frequency and recency;
- proposed procedure branch;
- human owner and validation status.

It never treats “people did this” as “people should do this.” Repeated workarounds
are candidates for review, not automatic procedure updates.

#### Five-minute portfolio demo

Use one official outage runbook and 15 synthetic incident narratives. In four
incidents, engineers bypassed an unavailable identity provider using an emergency
credential stored under a different team's control. The system links those events,
shows the missing runbook branch and drafts a reviewable addition with all four
incident citations.

#### Objective evaluation

- narrative event extraction precision/recall;
- alignment accuracy between observed actions and official steps;
- seeded undocumented-exception recall;
- false procedure-gap rate;
- evidence coverage per proposed gap;
- ability to distinguish one-off improvisation from recurring behavior;
- reviewer acceptance/rejection reasons;
- change in mutation-test survival after an approved repair.

#### Kill conditions

- event extraction cannot recover reliable order or actors from narrative text;
- access to representative incident histories is unrealistic;
- the workflow is already a standard feature of process-mining incumbents;
- “recurring” behavior is mistaken for correct behavior;
- the strongest output is only a summary or cluster visualization.

#### Round 2 assessment

**Advance cautiously to the red-team round. Current rank: 3.**

### F. UndoBudget — reversibility-aware evidence gate

#### Promise

Require more evidence for irreversible, high-blast-radius actions and less evidence
for cheap, reversible experiments. Balance the value of additional information
against the cost of delay.

#### Verdict: reject as a standalone product

This is good decision engineering, but decision gates, risk-governance frameworks
and agent-safety systems already use confidence, risk, reversibility and human
approval. [Revisable by Design](https://arxiv.org/abs/2604.23283) formalizes a
reversibility taxonomy for LLM-agent actions. The concept should inform safety
boundaries inside any future product, not become this project's main identity.

## Comparative score

Scores are research judgments from 1 to 10, not objective market facts.

| Concept | Exact-job novelty | Need | Demo | Baseline reuse | MVP feasibility | Objective evaluation | Overall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **NullProof** | 8.5 | 9.0 | 9.5 | 9.5 | 7.5 | 10.0 | **9.0** |
| **CollisionWitness** | 8.0 | 9.0 | 10.0 | 8.0 | 6.5 | 9.5 | **8.5** |
| **ShadowSOP** | 7.0 | 9.0 | 9.5 | 8.5 | 7.0 | 8.5 | **8.2** |
| EvidenceRoute | 5.5 | 9.0 | 8.5 | 7.0 | 6.5 | 8.5 | 7.5 |
| UndoBudget | 5.5 | 9.0 | 8.0 | 6.5 | 7.0 | 8.5 | 7.4 |
| SplitWorld | 5.0 | 8.5 | 8.5 | 8.0 | 7.0 | 7.5 | 7.3 |

## Why NullProof currently leads

NullProof has the clearest structural reason ordinary RAG fails:

```text
Existence claim
  one valid witness can be sufficient

Absence / universal / count claim
  top-k retrieval cannot justify a statement about the unread remainder
```

That relationship gives the project:

- an immediately understandable explanation;
- a visible failure of ordinary RAG;
- deep technical work across parsing, retrieval, coverage and verification;
- strong reuse of the current provenance-aware local baseline;
- deterministic corpus manifests and failure states;
- evaluation that can punish false confidence rather than reward fluent prose;
- applicability across several document-heavy domains.

Its biggest danger is also clear: a polished “coverage receipt” could become
security theater if semantic coverage is not actually defensible. The red-team
round must attack this first.

## Red-team questions reserved for Round 3

The next round should not add more features. It should attempt to kill all three
survivors.

### NullProof

- Can a finite system ever justify semantic absence, or only parser/query coverage?
- What existing legal discovery, systematic review or compliance-search tools
  already provide recall guarantees?
- Can we define a coverage contract without asking an LLM to certify itself?
- What corpus size makes exhaustive assurance impractical?
- Would a user understand “absent within this verified snapshot” correctly?

### CollisionWitness

- Is the witness new, or simply a user-friendly front end for existing policy
  verification/model-checking tools?
- Can source prose be translated accurately enough for the solver result to matter?
- How do we prevent absurd but formally valid scenarios?
- Does Apple Prose2Policy already make this an obvious incremental extension?

### ShadowSOP

- Do Celonis, SAP Signavio, UiPath Process Mining or incident-management products
  already perform this exact documentation-gap workflow?
- Can narrative traces be trusted without structured event logs?
- Is access to real incident histories a fatal portfolio-data limitation?
- Does the system produce actionable procedure changes or merely interesting
  clusters?

## Round 2 decision

Advance **NullProof, CollisionWitness and ShadowSOP** to the red-team round.

Do not select one yet. Do not build product architecture or UI yet. Round 3 should
search for prior art under different names, inspect mature adjacent products, test
the usefulness assumptions and produce one of three honest outcomes:

1. one concept survives and earns a small validation probe;
2. all three fail and this portfolio evolution is stopped; or
3. a narrower concept emerges from a discovered limitation and is evaluated under
   the same gates rather than automatically accepted.
