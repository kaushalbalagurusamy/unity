# Unity

**A Universal Semantic Intermediate Representation for Repository-Scale Code Reasoning**

[**Research Proposal**](RESEARCH_PROPOSAL.md) | [**Design Specification**](#representation-design) | [**Evaluation Protocol**](#evaluation-protocol) | [**BibTeX**](#citation)

---

## About

Large language models (LLMs) struggle to reason over large, multi-file codebases. Existing strategies typically fall into one of two paradigms, both of which have severe trade-offs:

1. **Long-Context Ingestion:** Feeding raw source files directly into large context windows leads to attention dilution ("lost-in-the-middle") and token inefficiency caused by lexical boilerplate and syntax fragmentation.
2. **Graph RAG / Code Property Graphs:** Constructing and querying AST/CFG/PDG graph databases (e.g. via Neo4j or vector stores) introduces high indexing overhead, query-time latency (2–10s per hop), schema drift across commits, and brittle graph-query generation.

Furthermore, pre-training data distributions heavily favor Python and JavaScript, resulting in marked performance drops when reasoning about systems-level languages (Rust, C++, Go) or legacy stacks (COBOL, Fortran).

**Unity** investigates whether source code across disparate languages can be deterministically lowered into a canonical, language-agnostic intermediate representation (**Unity-IR**). Unity-IR combines static system semantics (ownership, lifetimes, mutability, concurrency locks), first-order logic (predicates, invariants, relational transformations), and disambiguated structural English. By evaluating models directly on this normalized representation, Unity aims to:

- Eliminate cross-lingual reasoning disparities caused by surface syntax and pre-training distribution skew.
- Compress repository context into dense semantic invariants, reducing total token consumption.
- Enable sub-second cross-file dependency resolution without external graph database queries.

---

## Representation Design

Unity-IR decouples computational semantics from language-specific syntax via a three-layer schema:

```
+-------------------------------------------------------------------------+
| Layer 1: Contract & Systems Semantics (Deterministic Static Analysis)   |
| • Canonical Symbol IDs (@pkg.module.Class.method)                       |
| • Purity: pure | impure(IO) | impure(StateMutation:target)              |
| • Concurrency: exclusive_lock(m) | lock_free | atomic | csp_channel     |
| • Resource Bounds: mutable_borrow(&mut T) | shared_borrow(&T) | owned   |
+-------------------------------------------------------------------------+
| Layer 2: Algorithmic Core (Mathematical Logic & Relations)              |
| • Preconditions (P) and Postconditions (Q)                              |
| • Universal (∀) and Existential (∃) Quantifiers over Collections        |
| • Relational Transformations (Map, Filter, Fold)                        |
| • State Transition Deltas: S_{t+1} = S_t ⊕ {k ↦ v}                      |
+-------------------------------------------------------------------------+
| Layer 3: Causal Topology & Controlled Natural Language                  |
| • Standardized EBNF Intent Statements                                   |
| • Explicit Hyperlinked Dependencies to Inter-File Symbols               |
+-------------------------------------------------------------------------+
```

### Deterministic Lowering Pipeline

To prevent translation-phase hallucinations, Unity rejects probabilistic LLM-based translation. Instead, lowering is performed by a deterministic compiler pass:

```
Source Code (Python / Rust / Go / C++ / Java)
  │
  ▼  Tree-sitter AST
Generic Abstract Syntax Tree (Normalized AST)
  │
  ▼  Static Program Analysis (CFG / DFG / Abstract Interpretation)
Type & Invariant Extraction
  │
  ▼  Deterministic Emitter
Unity-IR (Contracts + Logic + Invariants)
```

---

## Comparison with Existing Approaches

| Dimension | Raw Source Code | AST Repo Maps (e.g. Aider) | Code Property Graphs (Joern / Memgraph) | Graph RAG (Greptile / MS GraphRAG) | Unity-IR |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Language Parity** | Skewed to Python/JS | Syntax-only signatures | Language-specific AST/CFG | Skewed by base LLM | Normalized across paradigms |
| **Context Density** | Low (boilerplate-heavy) | High (signatures only) | Low (large graph serialization) | Medium (chunks + docstrings) | High (compressed invariants) |
| **Multi-Hop Traversal** | Attention-dependent | Manual navigation | Precise query traversal | Multi-step LLM extraction | Self-contained links |
| **Query Latency** | Baseline file read | <50ms | 100ms–2s | 2s–10s | <100ms deterministic |
| **Index Maintenance** | None | Incremental re-parse | High (graph DB re-indexing) | High (re-summarization) | Local AST cache |

---

## Evaluation Protocol

We evaluate the representation across three benchmark tiers using frontier closed-weights and open-weights models (Claude 3.5 Sonnet, GPT-4o, DeepSeek-Coder-V2, Qwen 2.5 Coder):

1. **Repository-Level Issue Resolution:**
   - **SWE-bench Multilingual:** 300 real-world GitHub issues across 9 programming languages.
   - **SWE-bench Java:** 91 enterprise-level patch-and-verify tasks.
2. **Cross-File Context & Dependency Resolution:**
   - **CrossCodeEval:** Multi-file dependency completion in Python, Java, TypeScript, and C#.
   - **RepoEval:** Cross-file line, API, and function completion.
3. **Execution Simulation & Invariants:**
   - **CRUXEval-X:** Cross-lingual input/output state simulation.
   - **Concurrency Invariant Suite:** 100 multi-threaded synchronization tasks testing race and deadlock detection across 5–15 file boundaries.

### Primary Metrics

- **Task Accuracy:** pass@1 and pass@5 on full Docker test harnesses.
- **Cross-Lingual Disparity ($\sigma^2_{	ext{lang}}$):** Variance of accuracy scores across evaluated programming languages.
- **Structural Hallucination Rate (SHR):** Proportion of invented or invalid symbol references in model-generated reasoning traces.
- **Token Efficiency Ratio (TER):** Input token reduction of Unity-IR relative to raw source code.
- **Latency Profile:** End-to-end indexing, retrieval, and inference times.

For complete theoretical derivations, formal specifications, and experimental setups, see [**RESEARCH_PROPOSAL.md**](RESEARCH_PROPOSAL.md).

---

## Project Structure

```
unity/
├── README.md              # Project overview and specifications
├── RESEARCH_PROPOSAL.md   # Formal scientific research proposal
├── grammar/               # Unity-IR EBNF grammar specifications (planned)
├── compiler/              # Tree-sitter lowering frontends (planned)
│   ├── python/
│   ├── rust/
│   ├── go/
│   └── cpp/
├── analysis/              # CFG/DFG and invariant extraction passes (planned)
└── benchmarks/            # Evaluation harnesses and dataset runners (planned)
```

---

## Citation

```bibtex
@article{unity2025,
  title   = {Unity: A Universal Semantic Intermediate Representation for Repository-Scale Code Reasoning},
  author  = {Project Unity Research Group},
  journal = {arXiv preprint},
  year    = {2025}
}
```
