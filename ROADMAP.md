# Project Unity & Software Factory: Master Architecture & Implementation Roadmap

**An Autonomous Engineering Substrate for Invariant-Preserving, Repository-Scale Code Intelligence**  
**Executive Authority:** Project Unity & Software Factory Core Engineering  
**Target Publication Venue:** ICSE / OOPSLA / NeurIPS (AI for Systems Reasoning & Formal Verification)  
**Status:** Ratified Master Implementation Blueprint  
**Date:** September 2026  

---

## 1. System Architecture: The Unified Dual-Plane Engine

The **Software Factory** and **Project Unity** operate as an integrated, dual-plane autonomous engineering system. They reject both ungrounded generative "vibe-coding" and brittle, multi-agent bureaucratic scaffolding in favor of **Intrinsic Semantic Parity** and **Epistemic Zero Trust**.

```
                       ┌─────────────────────────────────────────────────────────┐
                       │               THE SOFTWARE FACTORY ENGINE               │
                       │              (Orchestration & Governance)               │
                       └─────────────────────────────────────────────────────────┘
                                                    │
             ┌──────────────────────────────────────┴──────────────────────────────────────┐
             ▼                                                                             ▼
┌────────────────────────────────────────┐                                   ┌────────────────────────────────────────┐
│     COGNITIVE & REASONING PLANE        │                                   │       EXECUTION & SUBSTRATE PLANE      │
│             (Unity-IR)                 │                                   │          (Concrete Syntaxes)           │
├────────────────────────────────────────┤                                   ├────────────────────────────────────────┤
│ • Canonical Symbol Table (@symbol)     │                                   │ • Polyglot Repositories (Python, Go)   │
│ • Systems Contracts (Purity, Locks)    │                                   │ • Concrete ASTs (Tree-sitter Parsers)  │
│ • State Invariants (Pre/Post, ∀, ∃)    │                                   │ • Deterministic Compilers & Linters    │
│ • Causal Dependency Topology           │                                   │ • Property-Based Invariant Fuzzers     │
│ • Socratic One-Way Door Deliberation   │                                   │ • Language Toolchains (cargo, go, uv)  │
└────────────────────────────────────────┘                                   └────────────────────────────────────────┘
                    ▲                                                                     │
                    │               DETERMINISTIC COMPILER LOWERING (Unity)               │
                    └─────────────────────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
                               ┌────────────────────────────────────────┐
                               │       EPISTEMIC ZERO-TRUST GATE        │
                               ├────────────────────────────────────────┤
                               │ • Canonical Semantic Delta (ΔS) Audit  │
                               │ • Cryptographically Locked Baselines   │
                               │ • Isolated Adversarial Invariant Fuzz  │
                               └────────────────────────────────────────┘
```

### Component Decomposition & Inter-Repository Contracts
1. **`unity` (The Semantic Context & Invariant Engine):**
   - Deterministically lowers heterogeneous source files (Python, Go, Rust) into a canonical 3-Layer Intermediate Representation (**Unity-IR**).
   - Extracts static system invariants: symbol ownership, thread synchronization (locks, channels), and mutation purity.
   - Computes the **Canonical Semantic Delta** ($\Delta \mathcal{S} = \mathcal{S}_{\text{post}} \ominus \mathcal{S}_{\text{pre}}$) across commits.
   - Exposes a typed Python library API and deterministic CLI (`unity compile`, `unity diff`, `unity verify`).
2. **`software-factory` (The Orchestrator & Governance Engine):**
   - Ingests user specifications, user issues, and repository state.
   - Audits architectural risk (**One-Way Doors vs. Two-Way Doors**) backed by Unity contract analysis.
   - Conducts Socratic architectural debates and ratifies formal Architecture Decision Records (ADRs).
   - Drives single-agent code synthesis using deep test-time compute (extended Chain-of-Thought).
   - Enforces the **Epistemic Zero-Trust Verification Gate** before committing changes to production.

---

## 2. Ratified Architectural Foundations

### Decision 1: Intrinsic Semantic Parity Over Panopticon Telemetry
We reject the dominant 2024–2025 industry pattern of wrapping LLMs in bloated extrinsic surveillance cages (synthetic LLM unit tests, eBPF sandboxes, multi-tier agent review boards). As proven by 2025–2026 meta-studies, this induces **tautological test debt** and **reward-hacking** (Berkeley *EvilGenie* 2026, *ImpossibleBench* 2025). Correctness must be established structurally as algebraic invariants over formal preconditions ($P$), postconditions ($Q$), purity, and concurrency bounds.

### Decision 2: Compute-Normalized Single-Agent Synthesis (No Swarm Bureaucracy)
In accordance with recent compute-normalized multi-agent evaluations (*The Illusion of Multi-Agent Advantage*, arXiv:2604.02460; *MASEval* 2026), we reject multi-agent developer/reviewer swarms for sequential code writing, which inflate token costs by up to 220x and degrade sequential reasoning by up to 70%.
- **Core Loop:** A single high-capability model utilizing extended test-time compute, directly equipped with deterministic tools.
- **Multi-Agent Isolation:** Multi-agent mechanisms are deployed **only** for isolated, adversarial red-team verifiers with zero access to the generator's internal rationale.

### Decision 3: Deterministic Compiler Lowering (Zero LLM Translation)
At no point is an LLM used to translate source code into Unity-IR. Lowering is strictly deterministic:
$$\text{Source Code} \xrightarrow{\text{Tree-sitter CST}} \text{Generic AST (UAST)} \xrightarrow{\text{Static Analysis (CFG/DFG)}} \text{Canonical Unity-IR}$$
This mathematically guarantees that intermediate representation generation is 100% immune to hallucination.

### Decision 4: Dual-Anchor Empirical Wedge (Python + Go)
To conclusively prove cross-lingual invariance without unbounded scope, the initial compiler proofs will target:
- **Python:** Dynamically typed, ubiquitous, reference-based, GIL-constrained.
- **Go:** Statically typed, explicit error models, native CSP concurrency (`sync.Mutex`, channels).
A concurrent state machine (e.g., financial ledger) implemented in both languages must lower to an identical, canonical Unity-IR representation.

### Decision 5: Epistemic Zero-Trust Verification
- Existing test suites and invariant contracts are cryptographically hashed; any agent-authored patch that weakens, skips, or deletes an assertion without a ratified ADR is automatically rejected.
- Agents implementing code cannot author the test criteria verifying their own implementation.

---

## 3. Phased Master Implementation Roadmap

```
Milestone 0: Specification, EBNF Grammar & Golden Ground Truth (TDD Foundation)
├── Formalize unity/grammar/unity_ir.ebnf (Layers 1, 2, 3)
├── Implement typed AST & contract data schemas (Pydantic / Dataclasses)
└── Author dual-anchor reference pair: examples/ledger/ (Python, Go, and canonical_ledger.uir)

Milestone 1: Unity Compiler Frontend & Lowering Engine
├── Build Tree-sitter AST walkers for Python & Go (compiler/parser.py)
├── Implement UAST normalization and invariant extraction (compiler/extractor.py)
├── Implement canonical Unity-IR text emitter (compiler/emitter.py)
│   └── Verification Gate: 100% byte-for-byte or AST match on canonical_ledger.uir
└── Implement the Semantic Delta Engine (compiler/delta.py -> ΔS)

Milestone 2: Software Factory Orchestrator & Epistemic Zero-Trust Substrate
├── Scaffold bare-metal CLI runner: factory/cli.py (Direct official model SDKs)
├── Build Semantic One-Way Door Guard (factory/governance.py via Unity contracts)
├── Implement Epistemic Zero-Trust Gate (factory/zero_trust.py)
│   ├── Cryptographic test baseline hashing
│   └── Property-based invariant fuzz harness generator
└── Implement factory audit --pr <ref> (Terminal projection of ΔS)

Milestone 3: End-to-End Brownfield Demonstration & Empirical Sweeps
├── Construct multi-file concurrency defect suite (Python & Go)
├── Execute comparative benchmarks across Conditions C0–C5
│   └── Measure: pass@k on SWE-bench Pro, SHR, σ²_lang, TER, Latency
└── Conduct human-in-the-loop double-blind review study (ΔS vs raw diff)

Milestone 4: Academic Publication & Open-Source Release
├── Finalize LaTeX manuscript for top-tier conference (ICSE / NeurIPS / OOPSLA)
├── Release reproducible Dockerized benchmarking evaluation harness
└── Open-source packages on PyPI and GitHub
```

---

### Milestone 0: Formal Specification, EBNF Grammar & Golden Ground Truth
*Objective: Establish the immutable mathematical and grammatical contract before writing compiler code.*

1. **Formal EBNF Grammar (`unity/grammar/unity_ir.ebnf`):**
   - Define exact syntax for:
     - **Layer 1:** Canonical symbol headers (`SYMBOL: @pkg.module.Class.method`), purity tags (`pure`, `impure(IO)`, `impure(StateMutation:target)`), and synchronization scopes (`exclusive_lock(m)`, `atomic`, `csp_channel`).
     - **Layer 2:** Contract clauses (`PRECONDITIONS: P1..Pn`, `EXECUTION_LOGIC: 1..N`, `POSTCONDITIONS: Q1..Qn`).
     - **Layer 3:** Declarative intent statements and hyperlinked upstream/downstream symbol references.
2. **Typed Schema Definitions (`unity/compiler/schema.py`):**
   - High-performance, immutable Python dataclasses modeling the 3-Layer UAST.
3. **Golden Ground-Truth Reference Anchor (`unity/examples/ledger/`):**
   - `ledger.py`: Multi-threaded bank account ledger using `threading.Lock` and balance invariants.
   - `ledger.go`: Struct-based ledger using `sync.Mutex` with identical balance invariants.
   - `canonical_ledger.uir`: The handwritten, gold-standard Unity-IR document.
   - *Automated Test:* `tests/test_golden_anchor.py` asserting that both files lower to this exact canonical structure.

---

### Milestone 1: Unity Compiler Frontend & Lowering Engine
*Objective: Deliver a high-performance, deterministic Tree-sitter lowering pipeline.*

1. **Parser Frontend (`unity/compiler/parser.py`):**
   - Integrate `tree_sitter` bindings for `tree_sitter_python` and `tree_sitter_go`.
   - Implement CST traversal into canonical control nodes (function declarations, calls, assignments, conditionals, loop structures).
2. **Invariant & Systems Extractor (`unity/compiler/extractor.py`):**
   - **Purity Detection:** Identify state mutations (writes to `self.*`, package globals, or referenced structs) vs. pure functional transformations vs. I/O operations.
   - **Concurrency Scope Analysis:** Extract lock acquisition/release boundaries (`with self.lock:`, `mu.Lock()`, `defer mu.Unlock()`).
   - **Pre/Post Condition Synthesis:** Extract parameter type bounds, `assert` statements, guard-clause exceptions, and return invariants.
3. **Canonical Emitter (`unity/compiler/emitter.py`):**
   - Serialize extracted UAST into formatted, validated Unity-IR conforming strictly to `unity_ir.ebnf`.
   - **Milestone 1 Gate:** Both `ledger.py` and `ledger.go` must compile to `canonical_ledger.uir` with 100% structural parity.
4. **The Semantic Delta Engine (`unity/compiler/delta.py`):**
   - Given two versions of a codebase (or a git commit/diff), compute:
     $$\Delta \mathcal{S} = \mathcal{S}_{\text{post}} \ominus \mathcal{S}_{\text{pre}}$$
   - Detect purity shifts (e.g., pure function becoming impure), synchronization changes (e.g., lock removal), and precondition/postcondition mutations.

---

### Milestone 2: Software Factory Orchestrator & Epistemic Zero-Trust Substrate
*Objective: Build the bare-metal autonomous execution and governance engine.*

1. **Bare-Metal CLI Runner (`software-factory/factory/cli.py`):**
   - CLI commands:
     - `factory run --spec <spec.md> --repo <target_repo>`
     - `factory audit --pr <git-ref> --repo <target_repo>`
     - `factory verify --repo <target_repo>`
   - Direct integration with official model SDKs (Google GenAI SDK, Anthropic SDK, OpenAI SDK); zero heavy framework overhead.
2. **Invariant-Backed Governance (`software-factory/factory/governance.py`):**
   - Integrate `unity` to detect One-Way Doors based on **structural contract violations**:
     - Concurrency model mutations.
     - Storage and database schema shifts.
     - Public API signature alterations.
   - Two-Way Doors execute autonomously; One-Way Doors trigger mandatory Socratic ADR generation via `skills/architectural-debate-and-decision-records`.
3. **Epistemic Zero-Trust Verification Gate (`software-factory/factory/zero_trust.py`):**
   - **Baseline Hash Guard:** Hashes all existing unit test files and specification files prior to execution; rejects patches that weaken assertions.
   - **Property-Based Invariant Fuzzer:** Generates hypothesis/fuzz test cases derived directly from Unity-IR Layer 2 pre/post conditions.
   - **Isolated Red-Team Verifier:** An isolated agent instance charged solely with finding edge cases that violate Layer 1/2 invariants.
4. **Terminal Semantic Reviewer (`factory audit`):**
   - Displays the colorized $\Delta \mathcal{S}$ in the console, enabling human reviewers to audit complex multi-file patches in seconds.

---

### Milestone 3: End-to-End Brownfield Demonstration & Empirical Sweeps
*Objective: Prove the superior efficacy and token density of the Dual-Plane system under rigorous experimental conditions.*

1. **Polyglot Concurrency Challenge:**
   - Author a realistic multi-file financial exchange simulation containing a subtle, distributed race condition across 5+ files (implemented in Python and Go).
   - Task the Software Factory with ingesting the issue, localizing the race condition via Unity-IR, and issuing an invariant-preserving patch.
2. **Empirical Benchmarking Sweeps:**
   - Evaluate across 6 controlled conditions ($C_0$: Raw Context, $C_1$: BM25 Vector RAG, $C_2$: Repo Maps, $C_3$: Graph RAG, $C_4$: Bytecode, $C_5$: Unity-IR).
   - Evaluate on frontier 2026 models: Claude Fable 5.1, GPT-6 Astra, Gemini 3.8 Flash, DeepSeek-Coder-V3.
   - Measure:
     - **Task Resolution Rate (pass@$k$)** on SWE-bench Pro.
     - **Cross-Lingual Disparity ($\sigma^2_{\text{lang}}$)**.
     - **Structural Hallucination Rate (SHR)**.
     - **Token Efficiency Ratio (TER)**.
     - **Query & Indexing Latency**.
3. **Human Review Comprehension Study:**
   - Double-blind experiment measuring human reviewer defect detection and time-to-review when presented with raw git diffs vs. $\Delta \mathcal{S}$.

---

### Milestone 4: Scientific Manuscript & Open Release
*Objective: Publish results in top-tier peer-reviewed venues and release production-grade open-source tooling.*

1. **LaTeX Manuscript Authoring:**
   - Grounded in theoretical derivations from `RESEARCH_MANIFESTO.md` and empirical sweep data from Milestone 3.
   - Target conference: NeurIPS / ICSE / OOPSLA.
2. **Artifact Packaging & Open Source:**
   - Package `unity-ir` compiler on PyPI.
   - Package `software-factory` orchestration CLI on PyPI / GitHub Releases.
   - Provide reproducible Docker containers for all benchmark sweeps.

---

## 4. Definition of Done & Quality Gates

| Milestone | Gate Criteria | Verification Command |
| :--- | :--- | :--- |
| **Milestone 0** | Valid EBNF grammar; valid typed schema; complete Python/Go golden test pair. | `pytest tests/test_schema.py` |
| **Milestone 1** | Python and Go golden files lower to identical `canonical_ledger.uir`; $\Delta \mathcal{S}$ correctly detects lock removal. | `pytest tests/test_compiler.py` |
| **Milestone 2** | `factory run` executes Two-Way doors autonomously, halts on One-Way doors for ADR debate; Zero-Trust gate blocks test tampering. | `pytest tests/test_factory_governance.py` |
| **Milestone 3** | Polyglot concurrency challenge resolved 100% green; $\ge 40\%$ token reduction verified; latency $<100\text{ms}$. | `python benchmarks/run_sweeps.py` |
| **Milestone 4** | Complete LaTeX manuscript compiled; all Docker benchmarks reproducible. | `make paper && make docker-eval` |
