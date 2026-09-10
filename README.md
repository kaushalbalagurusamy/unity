# Unity

**A Universal Semantic Intermediate Representation for Repository-Scale Code Reasoning**

[![CI](https://github.com/kaushalbalagurusamy/unity/actions/workflows/ci.yml/badge.svg)](https://github.com/kaushalbalagurusamy/unity/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[**Research Proposal**](RESEARCH_PROPOSAL.md) | [**Master Roadmap**](ROADMAP.md) | [**Design Specification**](#representation-design) | [**Toolchain & Dependencies**](#toolchain--core-dependencies) | [**Evaluation Protocol**](#evaluation-protocol) | [**BibTeX**](#citation)

---

## About

Despite substantial advances in test-time compute and extended context windows in frontier models (e.g. Claude Fable 5.1, GPT-6 Astra, Gemini 3.8 Flash, Grok 4), language models continue to struggle with repository-scale, multi-file code reasoning. Existing approaches suffer from fundamental structural trade-offs:

1. **Direct Long-Context Ingestion:** Ingesting raw source files across 1M+ token contexts leads to attention dilution ("lost-in-the-middle") and token inefficiency caused by lexical boilerplate, syntax fragmentation, and compiler-specific mechanics.
2. **Graph RAG / Code Property Graphs:** Constructing and querying AST/CFG/PDG graph databases (e.g. via Neo4j or vector stores) introduces high indexing overhead, query-time latency (2–10s per hop), schema drift across rapid commits, and brittle graph-query generation.

Furthermore, pre-training distributions remain heavily biased toward Python and TypeScript. Frontier models that achieve state-of-the-art results on Python benchmarks exhibit steep drops in reliability when reasoning over systems-level languages (Rust, C++, Go) or enterprise stacks (Java, COBOL), failing to satisfy strict lifetime, memory-ownership, and concurrency invariants.

**Unity** investigates whether source code across disparate languages can be deterministically lowered into a canonical, language-agnostic intermediate representation (**Unity-IR**). Unity-IR combines static system semantics (ownership, lifetimes, mutability, concurrency locks), first-order mathematical logic (predicates, invariants, relational transformations), and disambiguated structural English. By evaluating models directly on this normalized representation, Unity aims to:

- Eliminate cross-lingual reasoning disparities caused by surface syntax and pre-training distribution skew.
- Compress repository context into dense semantic invariants, reducing total token consumption.
- Enable sub-second cross-file dependency resolution without external graph database queries.

---

## The Core Paradigm: Parity Over Panopticon Telemetry

The dominant engineering pattern in 2025–2026 attempts to mitigate LLM unreliability through extrinsic surveillance: wrapping models in extensive synthetic test generators, runtime eBPF sandboxes, and multi-tier agent review guardrails. 

This approach introduces severe systemic costs:
- **Tautological Test Debt:** LLM-generated test harnesses scale proportionally with code generation, creating brittle mock pipelines and linear maintenance debt.
- **Cognitive Throttling:** Forcing models into localized micro-edits prevents high-order reasoning across repository-scale causal chains.
- **Reviewer Asymmetry:** Code generation takes seconds, but verifying non-local concurrency, memory, and authorization invariants causes human review fatigue, allowing critical vulnerabilities to slip into production.

**Unity replaces extrinsic surveillance with intrinsic semantic parity.** By deterministically lowering code into explicit state invariants, ownership lifecycles, and mathematical relations, correctness becomes a structural property of the representation. Reviewers and models audit the canonical semantic delta (\Delta S) rather than hundreds of lines of syntactic boilerplate.

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
| **Language Parity** | Skewed to Python/TS | Syntax-only signatures | Language-specific AST/CFG | Skewed by base LLM | Normalized across paradigms |
| **Context Density** | Low (boilerplate-heavy) | High (signatures only) | Low (large graph serialization) | Medium (chunks + docstrings) | High (compressed invariants) |
| **Multi-Hop Traversal** | Attention-dependent | Manual navigation | Precise query traversal | Multi-step LLM extraction | Self-contained links |
| **Query Latency** | Baseline file read | <50ms | 100ms–2s | 2s–10s | <100ms deterministic |
| **Index Maintenance** | None | Incremental re-parse | High (graph DB re-indexing) | High (re-summarization) | Local AST cache |

---

## Evaluation Protocol

We evaluate the representation across three benchmark tiers using frontier 2026 models across closed and open architectures:
- **Frontier Closed-Weights:** Claude Fable 5.1, GPT-6 Astra, Gemini 3.8 Flash, Grok 4.
- **Frontier Open-Weights:** DeepSeek-Coder-V3 / DeepSeek-R1, Qwen3-Coder (32B/70B), Llama 4 Code.

### Benchmark Suites

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

## Toolchain & Core Dependencies

Unity rejects probabilistic translation models in favor of deterministic compiler passes, formal grammar engines, and SMT solvers:

| Package / Tool | Purpose | Role in Project Unity |
| :--- | :--- | :--- |
| **`tree-sitter`**<br>`tree-sitter-python`<br>`tree-sitter-go` | Concrete Syntax Tree (CST) Frontends | High-speed, incremental AST parsing for Python and Go, extracting control structures without executing bytecode. |
| **`lark`** | Formal EBNF Grammar Engine | Parses and validates `grammar/unity_ir.ebnf`, ensuring emitted `.uir` files strictly adhere to the 3-Layer schema. |
| **`deal`** | Design-by-Contract (DbC) | Canonical Python contract definitions (`@deal.pre`, `@deal.ensure`, `@deal.pure`) used for reference anchors and AST extraction. |
| **`z3-solver`** | Microsoft Z3 SMT Prover | Validates that extracted pre/post-conditions preserve algebraic invariants across cross-lingual lowerings. |
| **`networkx`** | Causal Topology & DAGs | Analyzes hyperlinked inter-file symbol dependency graphs and computes topological sort order. |
| **`hypothesis`** | Invariant Property Fuzzer | Executes property-based fuzz testing against compiler lowering outputs to detect invariant drift. |
| **`pytest`** | Deterministic Test Suite | Drives compiler regression tests and AST parity verification. |

### Environment Setup

```bash
# Set up isolated virtual environment with Python 3.12+
uv venv --python 3.12 .venv
source .venv/bin/activate

# Install compiler dependencies
uv pip install -e .
```

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
@article{unity2026,
  title   = {Unity: A Universal Semantic Intermediate Representation for Repository-Scale Code Reasoning},
  author  = {Project Unity Research Group},
  journal = {arXiv preprint},
  year    = {2026}
}
```
