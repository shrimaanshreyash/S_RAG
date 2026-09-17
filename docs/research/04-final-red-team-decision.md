# S_RAG portfolio evolution: final red-team decision

Date: 2026-08-31

## Decision

**No-go. Do not build NullProof, CollisionWitness or ShadowSOP as the new identity
of this portfolio project.**

All three address real problems, and all three could produce technically strong
demos. That is not the bar set for this project. The required bar was a rare,
immediately distinct and strongly defensible product—not another useful assembly
of ideas that already exist in research, patents or mature adjacent products.

Round 3 deliberately searched under competing terminology, in older fields and in
new 2026 work. It found prior art close enough to defeat the central originality
claim of every candidate. Narrowing the wording again would preserve a feature,
not rescue a distinct product.

This is a product decision, not a claim that the underlying problems are solved.
It is also not a legal patentability opinion. The patent results below are
exploratory evidence that the intellectual territory is occupied.

## Final scorecard

Scores are research judgments from 1 to 10. “Defensible distinction” is scored
against the unusually high standard chosen for this portfolio, not against normal
commercial viability.

| Candidate | Problem need | Technical depth | Demo strength | Defensible distinction after red-team | Data/MVP realism | Verdict |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| NullProof | 9 | 9 | 9 | 3 | 7 | **No-go as headline** |
| CollisionWitness | 9 | 10 | 10 | 2 | 6 | **No-go** |
| ShadowSOP | 9 | 8 | 9 | 2 | 4 | **No-go** |

## 1. NullProof failed the originality and proof tests

### What survived

The underlying failure is real: a retrieved witness can establish existence, but
top-k silence cannot establish absence. A responsible system should distinguish
“not found in what was searched” from “does not exist.” This remains useful.

### What killed it

The proposed signature was:

1. recognize a negative or universal claim;
2. demand stronger corpus coverage than ordinary top-k RAG;
3. record what was and was not searched;
4. attach a machine-checkable receipt; and
5. refuse the claim when coverage is insufficient.

That combination is no longer an unoccupied product insight:

- August 2026 [completeness-sensitive negative-reasoning
  research](https://arxiv.org/abs/2608.04591) explicitly varies query-relative
  coverage and uses structured certificate elicitation to expose
  evidence-coverage errors.
- The July 2026 [Certified Document QA
  dataset](https://huggingface.co/datasets/SovNodeAI/certified-document-qa/blob/main/README.md)
  publishes absence items with machine-checkable certificates, source-corpus
  records, content hashes and verification sweeps. Its own correction log also
  demonstrates how easily a certificate can overstate what it proves.
- The independently described [Negative-Claim Exhaustion
  Check](https://abstractopedia.org/mechanisms/negative_claim_exhaustion_check/)
  makes negative-claim strength depend on search coverage and requires an
  exhaustion record of searched and unsearched regions.
- Legal discovery already treats completeness as an evaluated quantity. The
  [Relativity Active Learning guide](https://help.relativity.com/PDFDownloads/Server2024_PDF/Relativity%20-%20Assisted%20Review%20Active%20Learning%20Guide.pdf)
  documents project validation, elusion testing and recall estimation.
- Data-management research has formalized query completeness for decades. Work on
  [complete answers from incomplete databases](https://www.vldb.org/conf/1996/P402.PDF)
  and later [query-completeness statements](https://www.vldb.org/pvldb/vol4/p749-razniewski.pdf)
  shows that a negative answer becomes defensible only when relevant completeness
  assumptions are known.
- Contract-review products and patents already occupy the simpler “missing clause”
  interpretation. Examples include
  [OneClause](https://www.oneclause.io/),
  [ContractKen](https://www.contractken.com/review), and the older
  [clause-presence/absence patent US20210201013A1](https://patents.google.com/patent/US20210201013A1/en).

### The technical limit

For a frozen byte corpus, a deterministic scan can prove that an exact normalized
string is absent. For structured data with declared completeness rules, formal
query-completeness reasoning may justify a bounded negative result. For unrestricted
natural language, however, no finite list of embeddings, paraphrases or LLM-created
queries proves that every semantically equivalent expression was covered.

Therefore a receipt can prove parser execution, file/page coverage, exact searches
and the protocol followed. It cannot prove semantic exhaustion unless the claim is
first reduced to a closed, formally specified representation. Calling that result
“proof of absence” would create exactly the false confidence this project is meant
to prevent.

### Verdict

NullProof could be renamed “coverage-aware negative-claim verification” and built
honestly. That would be a useful RAG evaluation/application project, but the exact
distinction we hoped to claim is now visible in public 2026 work. **It does not meet
this portfolio's originality bar.**

## 2. CollisionWitness failed on direct prior art

### What killed it

CollisionWitness proposed translating natural-language rules into a bounded formal
model, detecting conflicting obligations, generating a minimal scenario in which
they collide, and translating that scenario back into cited prose.

This is not merely adjacent to older work. A 2013 paper on
[conflict analysis of controlled natural-language normative
texts](https://doi.org/10.1016/j.jlap.2013.03.002) describes automatic translation
to a formal language, conflict analysis, counterexample generation and conversion
of the counterexample back into controlled natural language for the user.

The surrounding territory is also mature:

- [US8327414B2](https://patents.google.com/patent/US8327414) covers semantic policy
  conflict detection and resolution, with priority dating to 2007.
- [EP1559070A2](https://patents.google.com/patent/EP1559070A2/en) covers expanding
  rule sets and detecting authorization/obligation conflicts.
- [US20200204453A1](https://patents.google.com/patent/US20200204453A1/en) covers
  counterexample generation for network-intent equivalence failures.
- [Cedar validation](https://docs.cedarpolicy.com/policies/validation.html),
  [Amazon Verified Permissions testing](https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/authorization-testing.html)
  and [Open Policy Agent testing](https://www.openpolicyagent.org/docs/policy-testing)
  demonstrate mature formal-policy validation and executable test workflows.
- Natural-language requirements inconsistency detection is an established research
  area, and IBM's current requirements tooling already combines traceability,
  change governance and AI-assisted quality analysis.

Source citations, modern LLM extraction and a polished witness UI could improve the
experience. They do not change the intellectual center of the product.

### Verdict

**No-go.** Keep counterexample generation as a possible verification technique in
a future domain-specific product, never as this project's novelty claim.

## 3. ShadowSOP failed on incumbent convergence and data realism

### What killed it

ShadowSOP proposed aligning official procedures with incident/ticket narratives,
finding recurring undocumented exception work and producing a cited documentation-
debt register.

The boundary between process mining and unstructured operational text has already
been crossed:

- [SAP Signavio Process Intelligence](https://help.sap.com/docs/SIGNAVIO_PROCESS_INTELLIGENCE/bf423b5f04964e4a90c5142ef9a87682/9ff14ea5d2c444e78d09a4c8568f5f22.html?locale=en-US)
  compares actual event-log paths with planned models and identifies variants and
  nonconformance.
- Its current [AI-assisted Context
  Analyzer](https://help.sap.com/docs/signavio-process-intelligence/onboarding-and-data-integration-guide/ai-assisted-context-analyzer?locale=en-US&state=PRODUCTION&version=SHIP)
  connects support tickets, chats, emails, audit notes and other free text to
  process events to reveal exceptions and operational drivers.
- [Process mining between the
  lines](https://doi.org/10.1016/j.is.2026.102713) extracts process events,
  exceptions and manual activities from unstructured text.
- [incident.io post-mortems](https://docs.incident.io/post-incident/postmortems-overview)
  are AI-native, incorporate incident context and turn incidents into follow-up
  learning; its [suggested follow-ups](https://docs.incident.io/ai/follow-ups)
  extract missing actions from incident conversations.

The exact “documentation debt register” view is still a useful feature. It is a
thin product boundary between existing process-conformance analysis, text-to-event
matching and incident learning.

The portfolio MVP also has a credibility problem: realistic incident histories are
sensitive and organization-specific. A synthetic dataset can verify extraction and
alignment mechanics, but cannot demonstrate that recurring workarounds are safe,
representative or worth formalizing. The strongest value claim would remain
mock-validated.

### Verdict

**No-go.** The need is strong, but incumbent convergence and unavailable real data
make it a weak choice for this portfolio.

## Why no narrower survivor is being forced through

A final-round failure should not trigger another renaming exercise. The following
would all be accurate but insufficient:

- “NullProof, but only for bounded natural-language corpora”;
- “CollisionWitness, but with better citations and minimality”;
- “ShadowSOP, but presented as documentation debt.”

Each formulation describes an implementation emphasis inside an established field.
None produces the hard evidence needed to tell a reviewer, “this is a genuinely
different product job.”

Combining the three would make the system larger, not more original. It would also
weaken the five-minute explanation and make evaluation less honest.

## Final disposition of this workspace

1. Preserve the existing local, inspectable RAG baseline as a completed project.
2. Do not implement any Round 1, Round 2 or Round 3 concept in this workspace.
3. Keep the research documents as evidence of disciplined product discovery and a
   deliberate no-go decision.
4. Do not market this repository as NullProof, CollisionWitness, ShadowSOP or
   “Reverse RAG.”
5. If portfolio exploration resumes, begin with a painful real-world workflow and
   a user/action/data advantage. Allow RAG to enter later as infrastructure; do not
   start from “what uncommon feature can be added to RAG?”

## What this round proved

The research did not fail. It prevented several weeks of building a polished demo
whose differentiation would collapse under one informed question. The strongest
portfolio story currently available is honest:

> I built and verified a local RAG system, then ran a multi-round prior-art and
> feasibility review before expanding it. The proposed directions addressed real
> needs, but direct research, patent and incumbent evidence showed that none met my
> originality bar, so I stopped instead of manufacturing a novelty claim.

That is the final decision for this concept-search cycle.
