# S_RAG portfolio evolution: concept discovery round 1

Date: 2026-08-31

> **Status: superseded as a recommendation.** This file preserves the first
> hypothesis and research trail. Deeper competitor research found that established
> requirements tools already provide traceability-based change-impact analysis, so
> RippleRAG should not be selected in this broad form. Use
> [`02-deep-concept-comparison.md`](./02-deep-concept-comparison.md) for the current
> shortlist and decision gate.

## Objective

Turn the working local RAG baseline into a portfolio project whose value is easy
to explain, technically defensible and meaningfully different from a standard
document chatbot.

This is an initial landscape scan, not proof that no comparable system exists.
Any final originality claim must be narrowed and validated again before the
project is presented publicly.

## What the current baseline gives us

The repository already has reusable interfaces for parsing, chunking, embedding,
retrieval and generation. It also preserves document, section and page provenance,
returns clickable citations and exposes stage-level performance measurements.

That makes it a good base for a new capability built around evidence. The project
does not need a cosmetic model, vector database or UI replacement.

## Landscape findings

Several directions that sound advanced are now common enough that they are not a
strong differentiator by themselves:

- **Agentic, graph and multimodal RAG:** current open-source systems already combine
  hybrid retrieval, knowledge graphs, agent navigation, multimodal parsing and
  cited answers. Examples include [RAGraph](https://github.com/ADVASYS/ragraph),
  [Knowhere](https://github.com/Ontos-AI/knowhere) and
  [SAG](https://github.com/Zleap-AI/SAG).
- **Record a workflow and generate instructions:**
  [Scribe](https://scribe.com/capture), [Guidde](https://help.guidde.com/en/collections/3533773-getting-started),
  [Tango](https://www.tango.ai/product/guide), and
  [Whatfix](https://support.whatfix.com/studio/docs/what-are-quick-capture-flows)
  already capture work and turn it into guides or in-app assistance.
- **Persistent screen memory:** [screenpipe](https://github.com/screenpipe/screenpipe)
  records screen and audio locally and exposes searchable memory to agents.
- **AI interviews for tacit knowledge:** [Tacivo](https://tacivo.com/),
  [KnowCore](https://www.knowcore.ai/), [KNOA](https://www.getknoa.com/) and
  [Voxcept](https://www.voxist.com/en/voxcept) already interview experts, ingest
  documents and produce structured, source-linked organizational knowledge.
- **Temporal and contradiction-aware RAG:** this is an important technical problem,
  but active research and open-source work already target temporal validity,
  supersession and conflicting evidence. Examples include
  [ConflictRAG](https://arxiv.org/abs/2605.17301),
  [ChronoRAG](https://github.com/SSKG2602/chronorag-acv) and
  [persistent-knowledge-layer](https://github.com/mcekikj/persistent-knowledge-layer/).
- **Multimodal investigation timelines:** tools such as
  [Google Pinpoint](https://journaliststudio.google.com/pinpoint/about/en-GB_uk/),
  [Incident Lens](https://github.com/rukaiya2000/incident-lens) and
  [Loom](https://github.com/jrwinget/loom) already organize mixed evidence and
  source-linked timelines.

The lesson is not to avoid these technologies. It is to use them as supporting
parts of a product with a sharper job than “search my knowledge.”

## Shortlist

Scores are an early product judgment from 1 (weak) to 10 (strong), based on the
current scan and the existing laptop-friendly baseline.

| Direction | Differentiation | Usefulness | Demo clarity | Baseline reuse | MVP feasibility | Overall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **RippleRAG: evidence-cited change impact engine** | 9 | 9 | 9 | 9 | 7 | **8.6** |
| Evidence Journey: reconstruct a defensible case from mixed media | 6 | 9 | 9 | 8 | 6 | 7.6 |
| Procedural Twin: learn a process from demonstrations and coach it live | 5 | 8 | 9 | 6 | 5 | 6.6 |
| Expert Handover: interview experts and preserve tacit knowledge | 4 | 9 | 8 | 8 | 7 | 7.2 |

## Recommendation: RippleRAG

### One-line explanation

**Most RAG systems tell you what the documents say. RippleRAG shows what else must
change when one rule, requirement or decision changes—and proves every impact with
source evidence.**

### Specific first user

A technical or operations lead responsible for a connected set of architecture
documents, policies, runbooks and standard operating procedures.

### Problem

Knowledge is spread across documents that refer to the same systems, roles,
requirements and procedures. When one rule changes, ordinary semantic search can
find similar passages but cannot reliably show the full downstream blast radius:

- which documents or steps are now stale;
- which statements contradict the proposed change;
- which systems, roles or controls may be affected;
- which questions cannot be resolved from the available evidence; and
- what must be reviewed before the change is accepted.

Recent work confirms the direction is technically meaningful. Research on
[counterfactual RAG](https://proceedings.iclr.cc/paper_files/paper/2026/hash/1c078897dc08d46091d0d361d9955c6b-Abstract-Conference.html)
is pushing retrieval beyond correlation, while an applied
[documentation impact-analysis example](https://www.scaleragency.io/works/ai-supported-impact-analysis-and-documentation-intelligence)
uses a connected knowledge graph to ask which processes and documents are affected
by a regulatory change. These are adjacent evidence, not proof of an identical
product.

### Different ingestion experience

The user does not only upload source documents. They create two evidence states:

1. **Current world:** existing policies, requirements, diagrams, runbooks and SOPs.
2. **Proposed world:** a revised document, pasted clause, structured change card or
   natural-language proposal such as “reduce log retention from 30 days to 7 days.”

The system converts both states into inspectable claims and dependencies, then
compares them. The “upload” becomes a proposed intervention against a grounded
model of the current world.

### Experience

1. Ingest the current corpus using the existing pipeline.
2. Extract atomic claims, entities, obligations, steps and cross-references with
   provenance back to the original chunks.
3. Build an inspectable dependency graph without discarding the vector index.
4. Accept a proposed change as text or a revised file.
5. Detect the direct diff, then traverse evidence-backed dependencies.
6. Present an interactive ripple map grouped into direct, downstream, conflicting
   and uncertain impacts.
7. Let the user open every impact at the exact source passage.
8. Generate a review checklist, affected-document list and unresolved questions.

### Supporting AI technologies

- structured LLM extraction into typed claims and relations;
- knowledge graphs for dependency traversal;
- temporal/version modeling for before-versus-after state;
- natural-language inference for contradiction and entailment checks;
- agentic retrieval for multi-hop evidence gathering;
- RAG for source-grounded explanations;
- uncertainty calibration and human approval for inferred relationships.

The graph, agent and contradiction detector are supporting technologies. The
product is the change-impact workflow.

## First demonstrable scenario

Use a small synthetic but realistic technical-operations corpus containing:

- an architecture overview;
- an access-control policy;
- a data-retention policy;
- an incident-response runbook;
- a deployment SOP; and
- a service ownership matrix.

Proposed change: **“Production audit-log retention changes from 30 days to 7 days.”**

Expected output:

- the changed source clause;
- affected monitoring, investigation and compliance steps;
- documents that still state 30 days;
- owners who must review the change;
- unresolved questions where no evidence connects a dependency; and
- a cited before/after impact brief.

This scenario is easy to understand in a short demo and can be evaluated against a
hand-authored ground-truth impact graph.

## Evaluation bar

The project should be judged on measurable behavior, not only the quality of its
generated prose:

- direct-impact precision and recall;
- downstream-impact precision and recall by graph distance;
- contradiction detection precision and recall;
- citation/provenance coverage;
- unsupported-impact rate;
- uncertainty calibration;
- latency and local resource use; and
- change-review time saved in a small user study.

## Decision gate before implementation

Before architecture work begins, confirm or reject these three assumptions:

1. Technical/operations change review is the best first domain.
2. The core promise should be impact discovery, not automated approval or execution.
3. The first version should remain local, inspectable and human-gated.

If accepted, the next artifact will be a product brief with personas, user journey,
scope, explicit non-goals, success metrics and an MVP architecture that preserves
the working baseline.
