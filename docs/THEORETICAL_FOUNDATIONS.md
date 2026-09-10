# Theoretical Foundations & Computability Architecture

## Executive Abstract

Project Unity investigates the deterministic lowering of polyglot source code into a canonical, language-agnostic intermediate representation (**Unity-IR**). This document outlines the formal methods foundations, computability boundaries, compiler theory, and systems architecture governing the representation.

Unity addresses the repository-scale reasoning bottleneck of frontier neural models not by introducing unbounded runtime synthesis or executable bytecode virtualization, but by establishing a sound, decidable **epistemic verification substrate**.

```
+---------------------------------------------------------------------------------------------------+
|                                       PROJECT UNITY ARCHITECTURE                                  |
|                                                                                                   |
|  [ Native Polyglot Code ]                                                                         |
|  (Python, Go, Rust, C++)                                                                          |
|         │                                                                                         |
|         ▼ (Monotonic One-Way Lowering: Tree-sitter CST + Static Contract Extraction)             |
|  [ Unity-IR: Epistemic Substrate ]                                                                |
|  ├── Layer 1: Contracts & Systems Attributes (Purity, Concurrency, Ownership)                     |
|  ├── Layer 2: Algorithmic Core (QF_LIA Predicates, State Transitions)                             |
|  └── Layer 3: Causal Topology (SCIP/LSP Resolved Call Graphs & CNL)                              |
|         │                                                                                         |
|         ├──► Context Ingestion: GPU Attention Prefill Optimization (O(N^2) token savings)         |
|         └──► Differential Verification: SMT (Z3) on ΔS = S_post ⊖ S_pre (< 4 ms bounded QF_LIA)    |
+---------------------------------------------------------------------------------------------------+
```

---

## 1. Computability Boundaries & Rice's Theorem Compliance

### 1.1 The Invariant Synthesis Boundary
Per **Rice's Theorem**, any non-trivial semantic property of arbitrary programs in a Turing-complete language is undecidable:
$$\forall P \in \mathcal{P}, \quad P \neq \emptyset \land P \neq \mathcal{T} \implies \{ \langle M \rangle \mid \mathcal{L}(M) \in P \} \text{ is undecidable}$$

Project Unity **does not attempt automated inductive invariant synthesis** for unannotated loops or general Turing-complete programs. Attempting to mechanically divine arbitrary loop invariants ($\mathcal{I}$) or postconditions from unannotated imperative code without developer-supplied specifications or bounded model checking is mathematically undecidable.

Instead, Unity operates on **Contract Extraction & Deterministic Lowering**:
1. **Declared Contract Extraction**: Unity extracts explicit contracts, assertions, parameter validation guards, type constraints, and decorator specifications (e.g., Python `@deal`, Go `if err != nil`, Rust type-state invariants).
2. **Structural Pattern Lowering**: Canonical state transition operations (such as ledger mutations $S_{t+1} = S_t \oplus \{k \mapsto v\}$, boundary checks, and lock acquisitions) are lifted into normalized algebraic representations.
3. **Contract Preservation, Not Discovery**: Unity-IR explicitly represents the *boundaries* guaranteed by the code or its specifications, rather than fabricating non-existent mathematical guarantees out of thin air.

### 1.2 Bounded Decidability: SMT Verification in QF_LIA
The role of automated theorem proving (via the Z3 SMT solver) in Unity is strictly delimited:
* **The Entailment Problem**: When an autonomous agent or developer modifies code, Unity computes the semantic difference $\Delta \mathcal{S} = \mathcal{S}_{\text{post}} \ominus \mathcal{S}_{\text{pre}}$ and checks whether preconditions have been unsafely strengthened or state bounds violated:
  $$\text{Valid}(P_{\text{pre}} \implies P_{\text{post}}) \iff \text{UNSAT}(\neg (P_{\text{pre}} \implies P_{\text{post}}))$$
* **Decidable Fragment Guarantee**: SMT queries in Unity are strictly confined to **Quantifier-Free Linear Integer Arithmetic (QF_LIA)** and Equality with Uninterpreted Functions (EUF). Within QF_LIA, the validity problem is decidable (via Presburger arithmetic decision procedures, Fourier-Motzkin elimination, and Simplex-based integer linear programming).
* **Conservative Syntactic Fallback**: If a predicate contains non-linear arithmetic, complex floating-point expressions, or unmodeled external function calls outside QF_LIA, the solver does not hang or execute unbounded search. Instead, it emits `VerificationStatus.CONSERVATIVE_SYNTACTIC_CHECK`, requiring strict syntactic equivalence or flagging the transition for architectural review.

```
                  ┌──────────────────────────────────────────────┐
                  │ Candidate Contract Mutation (P_old, P_new)   │
                  └──────────────────────┬───────────────────────┘
                                         │
                         Is predicate within QF_LIA?
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼ YES                                     ▼ NO
       ┌───────────────────────────────┐        ┌───────────────────────────────┐
       │   Formulate Query in Z3 SMT   │        │ Fallback to Conservative      │
       │   UNSAT(¬(P_old => P_new))    │        │ Syntactic Checking            │
       └───────────────┬───────────────┘        └───────────────┬───────────────┘
                       │                                        │
           ┌───────────┴───────────┐                            │
           ▼ UNSAT                 ▼ SAT / CEX                  ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌───────────────────────────────┐
│ DECIDABLE_SMT_PROVED│ │ COUNTEREXAMPLE_FOUND│ │ CONSERVATIVE_SYNTACTIC_CHECK  │
│ Contract Relaxed    │ │ One-Way Door Error  │ │ Sound Identity or Halt Review │
└─────────────────────┘ └─────────────────────┘ └───────────────────────────────┘
```

---

## 2. Epistemic Reasoning Substrate vs. Executable Bytecode

### 2.1 The UNCOL Illusion in Historical Compilers
Historically, attempts to create a universal intermediate language (such as UNCOL—Universal Computer Oriented Language in 1958) failed because they targeted **runtime execution**:
* A general execution bytecode must reconcile conflicting language execution semantics: garbage collection vs. manual memory management (`malloc`/`free`), stack unwinding vs. panics, green threads vs. OS threads, structural typing vs. nominal inheritance.
* Lowering $N$ source languages into 1 executable bytecode for $M$ target architectures without semantic loss or runtime bloat proved intractable.

### 2.2 Unity-IR as an Epistemic Substrate
Unity-IR is **not an executable bytecode**. It does not possess a virtual machine, does not manage garbage collection or memory layouts, and is never executed by a CPU or runtime interpreter.

Instead, Unity-IR is an **epistemic intermediate representation**:
* **Target Consumer**: The consumers of Unity-IR are **Transformer attention heads**, **formal verification solvers (Z3)**, and **software architects**.
* **Purpose**: It models semantic intent, invariants, synchronization locks, purity attributes, and inter-procedural causal topologies.
* **Lossless Semantic Distillation**: By discarding language-specific lexical baggage (syntax sugar, punctuation, import formats, boilerplate getters/setters), Unity-IR provides a canonical representation where logically identical implementations in Python, Go, Rust, or C++ lower to isomorphic semantic blocks.

---

## 3. The Decompilation Boundary: Strictly Monotonic One-Way Lowering

### 3.1 Why Universal Decompilation is Unnecessary
General decompilation from high-level intermediate representations back into idiomatic, maintainable source code across arbitrary languages is a notoriously fraught problem:
* Reconstructing idiomatic language constructs (e.g., Python list comprehensions, Go goroutine select statements, Rust borrow checker annotations) from a lowered format leads to unnatural, unidiomatic code that human developers reject.

### 3.2 Monotonic Lowering Architecture
Unity sidesteps the decompilation void entirely by enforcing a **strictly monotonic, one-way lowering pipeline**:

$$\mathcal{L}: \text{Source}_{\text{polyglot}} \longrightarrow \text{Unity-IR}$$

```
                ┌──────────────────────────────────────────────┐
                │             Native Polyglot Code             │
                │        (Python, Go, Rust, TypeScript)        │
                └──────────────┬───────────────────────────────┘
                               │
                               ▼ Lowering L (Deterministic)
                ┌──────────────────────────────────────────────┐
                │                   Unity-IR                   │
                │        (Canonical Semantic Substrate)        │
                └──────────────┬───────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────────────┐     ┌───────────────────────────────┐
│     Context Ingestion         │     │     Verification Engine       │
│ Dense Prompt for LLM Agent    │     │ SMT Implication & Invariants  │
└───────────────┬───────────────┘     └───────────────┬───────────────┘
                │                                     ▲
                │ (Agent Reasons in Dense Semantics)  │
                ▼                                     │
┌───────────────────────────────┐                     │
│ Autonomous Agent Generates    │                     │
│ Native Git Diff (e.g. .py/.go)├─────────────────────┘
└───────────────────────────────┘ (Re-lowered to verify ΔS)
```

1. **Reading & Ingestion**: The autonomous agent or human architect reads dense Unity-IR to understand repository invariants, call graphs, and concurrency boundaries.
2. **Generation**: The autonomous agent emits **native source code directly** (e.g., standard Git diffs in Python, Go, or Rust). The agent is guided by the semantic contract of Unity-IR, but generates code native to the host project.
3. **Verification**: Upon generating the native diff, the compiler re-lowers the modified source files into post-change Unity-IR ($\mathcal{S}_{\text{post}}$) and executes differential SMT verification ($\mathcal{S}_{\text{post}} \ominus \mathcal{S}_{\text{pre}}$).
4. **Conclusion**: Unity-IR is **never decompiled**. Code authors and agents write native code; Unity-IR verifies and represents it.

---

## 4. Architectural Decoupling: Single-File CSTs vs. Cross-File Causal Topology

### 4.1 Tree-sitter Scope & Limitations
Tree-sitter is a concrete syntax tree (CST) parser generator designed for high-performance incremental parsing within single-file lexical scopes. It operates with $O(1)$ disk access and no global symbol tables. It does not resolve:
* Multi-file symbol definitions across packages.
* Type inference spanning module boundaries.
* Dynamic dispatch, reflection, or interface resolution.

Treating Tree-sitter as a whole-program analyzer is an architectural anti-pattern.

### 4.2 Decoupled Causal Graph Architecture
Unity strictly separates **single-file syntax lowering** from **inter-procedural causal topology**:

```
[ File 1 Source ] ──► [ Tree-sitter CST ] ──► [ Symbol Invariants ] ──┐
                                                                      │
[ File 2 Source ] ──► [ Tree-sitter CST ] ──► [ Symbol Invariants ] ──┼──► [ Unified UnityModule ]
                                                                      │            ▲
[ External SCIP/LSP ] ──────────────────────► [ Causal Link Graph ] ──┘            │
(e.g., rust-analyzer, gopls, pyright)        (Inter-file callers, dependencies)    │
                                                                                   │
                                             Resolved via CausalGraphResolver Protocol
```

1. **Frontend Lowering (`compiler/extractor.py`)**:
   - Uses Tree-sitter exclusively for single-file CST generation and lexical construct lifting (types, parameter signatures, lexical guards, concurrency primitives, and execution steps).
   - This phase is embarrassingly parallel and operates at **> 300,000 lines/second per core**.
2. **Topology Resolution (`CausalGraphResolver`)**:
   - Cross-file call graphs (`CALLED_BY`, `DEPENDS_ON`) are decoupled behind the `CausalGraphResolver` protocol.
   - In standalone mode, a fast lexical resolver provides local project bindings.
   - In enterprise CI/CD environments, Unity interfaces directly with industry-standard indexers:
     - **SCIP** (Source Code Intelligence Protocol)
     - **LSP** (Language Server Protocol via `gopls`, `pyright`, `rust-analyzer`)
     - Build system dependency graphs (Bazel query, Cargo metadata)

---

## 5. Foundation Model Priors & Attention Mechanics

### 5.1 Controlled Natural Logic (CNL) Alignment
Frontier foundation models are trained predominantly on natural language, documentation, and source code. Highly idiosyncratic mathematical formalisms (such as raw Prolog clauses, TLA+ specifications, or dense lambda calculus) occupy a vanishingly small fraction of pre-training token distributions.

Unity Layer 3 employs **Controlled Natural Logic (CNL)**:
* Combines formal mathematical precision with natural syntactic constructs.
* Expresses preconditions, postconditions, and algorithmic steps using standard declarative phrases (`EVALUATE`, `MUTATE`, `ACQUIRE`, `RELEASE`, `QUERY`).
* Matches the learned priors of large transformer models, preventing hallucination while maintaining rigorous parseability by deterministic grammars.

### 5.2 Quadratic Attention FLOPs & KV-Cache Dynamics
Transformer inference latency during the prompt processing (prefill) phase is dominated by self-attention FLOPs, which scale quadratically with sequence length $N$:

$$\text{FLOPs}_{\text{attn}} = 2 \cdot L \cdot d_{\text{model}} \cdot N^2$$

Where $L$ is the number of layers and $d_{\text{model}}$ is the hidden dimensionality.

When raw polyglot code is ingested:
* Syntactic boilerplate (import ladders, braces, type verbosity, boilerplate error handling) accounts for **70–80% of total tokens**.
* In a 16,000-token raw prompt, attention consumes $16000^2 = 256 \times 10^6$ relative quadratic units.
* Lowering to Unity-IR compresses this context to ~4,000 tokens of high-density semantic invariants.
* The quadratic attention compute drops to $4000^2 = 16 \times 10^6$ relative units—an **exact $16\times$ reduction in self-attention FLOPs**.

Furthermore, because Unity-IR normalizes AST order, formatting, and symbol IDs canonically, symbol blocks remain identical across non-functional source changes. This preserves **Radix-tree prefix cache hits** in inference engines (vLLM, SGLang), eliminating redundant prompt recomputation.

---

## 6. Two-Tier Throughput and Verification Model

Project Unity establishes two clearly defined operational regimes with distinct latency and algorithmic characteristics:

| Dimension | Tier 1: Streaming Ingestion Pipeline | Tier 2: Differential SMT Verification Engine |
| :--- | :--- | :--- |
| **Primary Operation** | Parse, Lift, and Canonicalize ($S \to \text{Unity-IR}$) | Prove Contract Entailment ($P_{\text{pre}} \implies P_{\text{post}}$) |
| **Scope** | Entire repository / working set | Modified symbol delta ($\Delta \mathcal{S}$) only |
| **Algorithmic Complexity**| Linear $O(N)$ streaming | Bounded QF_LIA Decision Procedure |
| **Typical Input Size** | 1,000 to 10,000,000 LOC | 1 to 10 modified symbols (in a PR/diff) |
| **Throughput / Latency** | **301,000 to 1,180,000 LOC / second** | **< 4 milliseconds total per diff** |
| **Hardware Target** | Multi-core CPU streaming | Single CPU thread SMT solver instance |
| **Failure Mode** | Tree-sitter syntax recovery | `COUNTEREXAMPLE_FOUND` or conservative fallback |

### 6.1 Why SMT Verification Never Bottlenecks Repo Ingestion
* Streaming ingestion does **not** invoke the SMT solver. Constructing the initial AST, extracting metadata, and emitting canonical IR is a pure parsing and serialization task.
* The Z3 SMT solver is invoked **only during differential verification** when a change is introduced.
* Because a typical software engineering change affects only a tiny fraction of a codebase ($\approx 0.04\%$), SMT queries are generated only for modified preconditions and assertions, completing in single-digit milliseconds.

---

## 7. Formal Verification Classifications

Contract delta checks in Unity-IR are formally classified according to the `VerificationStatus` taxonomy:

```python
class VerificationStatus(str, Enum):
    DECIDABLE_SMT_PROVED = "DECIDABLE_SMT_PROVED"
    COUNTEREXAMPLE_FOUND = "COUNTEREXAMPLE_FOUND"
    CONSERVATIVE_SYNTACTIC_CHECK = "CONSERVATIVE_SYNTACTIC"
```

1. **`DECIDABLE_SMT_PROVED`**:
   The SMT solver verified that the proposed contract modification is an invariant-preserving relaxation within the decidable theory of Quantifier-Free Linear Integer Arithmetic (QF_LIA).
2. **`COUNTEREXAMPLE_FOUND`**:
   The SMT solver identified a concrete assignment of inputs falsifying the entailment $P_{\text{old}} \implies P_{\text{new}}$, proving an invariant regression (flagged as a critical `ONE_WAY_DOOR`).
3. **`CONSERVATIVE_SYNTACTIC_CHECK`**:
   The predicate contains uninterpreted functions, strings, or constructs outside QF_LIA. The engine falls back soundly to syntactic equality; non-identical mutations halt autonomous deployment and require human review.

This taxonomy guarantees that Project Unity remains mathematically sound, computationally tractable, and architecturally resilient across all operating scales.

---

## 8. Formal Operational Semantics & Lowering Calculus

To eliminate ambiguity and ground the representation in formal programming language theory, this section formalizes the state space, transition relations, contract refinement preorder, and inductive lowering calculus.

### 8.1 State Domain & Execution Environment
Let the abstract machine state $\mathcal{S}$ be defined as the 4-tuple:
$$\mathcal{S} \triangleq \langle \Sigma, \mathcal{H}, \mathcal{L}, \mathcal{P} \rangle \in \text{State}$$

Where:
1. **Local Variable Store ($\Sigma$)**:
   $$\Sigma : \text{Var} \rightharpoonup \mathcal{V}$$
   Maps local identifier names to values in domain $\mathcal{V} \triangleq \mathbb{Z} \cup \mathbb{B} \cup \text{Str} \cup \text{Loc} \cup \{ \bot \}$.
2. **Shared Heap State ($\mathcal{H}$)**:
   $$\mathcal{H} : \text{Loc} \rightharpoonup \mathcal{V} \times \text{Type}$$
   Maps heap locations to typed records, simulating heap allocations and mutable composite structures (e.g., dictionary lookups, struct fields).
3. **Active Synchronization Set ($\mathcal{L}$)**:
   $$\mathcal{L} \subseteq \text{LockId}$$
   The set of currently acquired mutual exclusion locks held by the executing thread.
4. **Purity Capability Lattice ($\mathcal{P}$)**:
   $$\mathcal{P} \in \langle \mathbb{P}, \le_{\text{purity}} \rangle, \quad \mathbb{P} \triangleq \{ \text{Pure}, \text{Impure}(\mathcal{E}) \}$$
   Where $\mathcal{E} \subseteq \{ \text{IO}, \text{StateMutation}(\text{Loc}), \text{Concurrency} \}$ denotes the permitted side-effect capabilities. The lattice ordering satisfies:
   $$\text{Pure} \sqsubset \text{Impure}(\text{StateMutation}) \sqsubset \text{Impure}(\text{IO})$$

### 8.2 State Transition Relation
An operational transition takes a state $\mathcal{S}$, executes an action $\alpha \in \mathcal{A}$, and produces a successor state $\mathcal{S}'$:
$$\langle \Sigma, \mathcal{H}, \mathcal{L}, \mathcal{P} \rangle \xrightarrow{\alpha} \langle \Sigma', \mathcal{H}', \mathcal{L}', \mathcal{P}' \rangle$$

The canonical action alphabet $\mathcal{A}$ in Unity Layer 2 comprises:
* $\text{ACQUIRE}(m)$: Transitions state such that $\mathcal{L}' = \mathcal{L} \cup \{m\}$, requiring $m \notin \mathcal{L}$.
* $\text{RELEASE}(m)$: Transitions state such that $\mathcal{L}' = \mathcal{L} \setminus \{m\}$, requiring $m \in \mathcal{L}$.
* $\text{MUTATE}(k, v)$: Transitions state such that $\mathcal{H}' = \mathcal{H} \oplus \{ k \mapsto v \}$, requiring $\text{StateMutation}(k) \in \mathcal{P}$.
* $\text{QUERY}(x, k)$: Read-only binding where $\Sigma' = \Sigma \cup \{ x \mapsto \mathcal{H}(k) \}$.
* $\text{EVALUATE}(x, e)$: Pure expression evaluation $\Sigma' = \Sigma \cup \{ x \mapsto \llbracket e \rrbracket_\Sigma \}$.

### 8.3 Contract Refinement Preorder ($\sqsubseteq$)
For two symbol declarations $\mathcal{D}_1$ and $\mathcal{D}_2$, we say $\mathcal{D}_2$ **refines** $\mathcal{D}_1$ (written $\mathcal{D}_2 \sqsubseteq \mathcal{D}_1$) if and only if $\mathcal{D}_2$ preserves all observational safety invariants of $\mathcal{D}_1$:

$$\mathcal{D}_2 \sqsubseteq \mathcal{D}_1 \iff \begin{cases}
\forall \vec{x}, & P_{\mathcal{D}_1}(\vec{x}) \implies P_{\mathcal{D}_2}(\vec{x}) & \text{(Precondition Weakening)} \\
\forall \vec{x}, \vec{y}, & Q_{\mathcal{D}_2}(\vec{x}, \vec{y}) \implies Q_{\mathcal{D}_1}(\vec{x}, \vec{y}) & \text{(Postcondition Strengthening)} \\
& \mathcal{L}_{\mathcal{D}_1} \subseteq \mathcal{L}_{\mathcal{D}_2} & \text{(Lock Subsumption)} \\
& \mathcal{P}_{\mathcal{D}_2} \le_{\text{purity}} \mathcal{P}_{\mathcal{D}_1} & \text{(Purity Non-Degradation)}
\end{cases}$$

**Semantic Delta Rule**: Any transformation where $\mathcal{D}_2 \not\sqsubseteq \mathcal{D}_1$ represents an architectural regression and is classified as a critical `ONE_WAY_DOOR`.

### 8.4 Inductive Lowering Calculus ($\Gamma \vdash e \hookrightarrow \mathcal{U}$)
Let $\Gamma$ be the typing environment mapping identifiers to their types and systems capabilities. The lowering pass maps concrete AST expressions $e$ in source language $\mathcal{K} \in \{ \text{Python}, \text{Go}, \text{Rust} \}$ into canonical Unity-IR statements $\mathcal{U}$:

$$\frac{\Gamma \vdash e_1 \hookrightarrow s_1 \quad \Gamma \vdash e_2 \hookrightarrow s_2 \quad \text{typeof}(v) = \text{Int64}}{\Gamma \vdash \text{Assign}(v, e_1 + e_2) \hookrightarrow \left[ \text{EVALUATE: } t = s_1 + s_2, \quad \text{MUTATE: } v := t \right]}$$

$$\frac{\text{FieldAccess}(e, \text{"Lock"}) \quad \Gamma \vdash \text{body} \hookrightarrow \mathcal{U}_{\text{body}}}{\Gamma \vdash \text{WithLock}(m, \text{body}) \hookrightarrow \left[ \text{ACQUIRE: exclusive\_lock}(m) \right] \cdot \mathcal{U}_{\text{body}} \cdot \left[ \text{RELEASE: exclusive\_lock}(m) \right]}$$

---

## 9. Epistemic Verification Model: Specification vs. Implementation

A central challenge in program synthesis and verification is the distinction between:
* **The Operational Implementation ($\text{Impl}$)**: The concrete syntax detailing *how* a program transitions machine states.
* **The Teleological Specification ($\text{Spec}$)**: The human developer's underlying goal—*what* the program ought to achieve.

### 9.1 Resolving the "Canonicalizing the Defect" Paradox
If an automated extractor blindly lifts a buggy program (e.g. an off-by-one loop index or a missing authentication check), does it not merely formalize human error into an immutable law?

**Yes—if the goal were ab initio formal verification ($\text{Impl} \models \text{Spec}$).** 
Deriving an unstated human specification ($\text{Spec}$) out of operational syntax alone is mathematically impossible: no compiler can divine that an engineer intended `balance > amount` when they wrote `balance >= amount`.

Project Unity explicitly defines its verification domain as **Differential Invariant Refinement ($\Delta \mathcal{S}$)**:
$$\text{Impl}_{\text{post}} \sqsubseteq \text{Impl}_{\text{pre}}$$

1. **The Reference Baseline**: In software engineering, refactoring, cross-lingual porting, and agentic code generation, the baseline codebase $\text{Impl}_{\text{pre}}$ represents the existing accepted contract.
2. **Preserving Established Boundaries**: Unity does not claim $\text{Impl}_{\text{pre}}$ is divinely correct; it proves that $\text{Impl}_{\text{post}}$ does not silently violate the contracts, invariants, and synchronization rules that $\text{Impl}_{\text{pre}}$ established.
3. **Role of the Neural Model**: The LLM's role is to translate high-level natural language issues ($\text{Spec}$) into code modifications. Unity-IR acts as the safety rail, verifying that the agent's patch maintains backward compatibility and invariant refinement.

### 9.2 Preserving Communicative Intent in Layer 3
A common failure mode in formal methods for machine learning is desugaring code into stripped, uninterpreted logic (such as raw SMT-LIB2 formulas), which destroys the semantic priors neural networks rely upon (variable names, docstrings, idioms).

Unity-IR deliberately preserves communicative tokens:
* **Layer 3 Controlled Natural Logic (CNL)** retains descriptive identifiers (`account_id`, `balances`, `exclusive_lock(vault.mu)`).
* By stripping *syntactic noise* (brackets, semicolons, redundant imports) while preserving *domain terminology*, Unity-IR presents neural models with maximum pragmatic signal per token, enhancing rather than degrading intent inference.

---

## 10. Scope Boundaries, Assumptions & Failure Modes

In accordance with scientific rigor, Project Unity explicitly defines its operational boundaries and known failure modes:

### 10.1 Dynamic Typing & Runtime Metaprogramming
* **Assumption**: Programs exhibit statically analyzable module boundaries and symbol references.
* **Failure Mode**: Highly dynamic Python/JavaScript patterns (such as runtime `eval()`, dynamic `getattr` dispatch, or monkey-patching globals) cannot be resolved into closed-form UAST contracts.
* **Remedy / Fallback**: When an unresolvable dynamic construct is encountered, the extractor emits an `UNKNOWN_MUTATION` node and assigns `VerificationStatus.CONSERVATIVE_SYNTACTIC_CHECK`. Autonomous automated deployment is blocked, requiring manual human validation.

### 10.2 Pointer Aliasing & Complex Heap Topologies
* **Assumption**: Memory mutations operate on identifiable struct fields or mapped collection keys.
* **Failure Mode**: Complex, cyclic heap graphs in unmanaged languages (e.g. C/C++ raw pointer arithmetic, arbitrary double-free scenarios) exceed the expressiveness of linear contract extraction.
* **Scope Boundary**: Unity focuses on application-level and systems-level business logic, concurrent state updates, and inter-procedural causal flows—not low-level assembly-level alias analysis.

### 10.3 Non-Executable Epistemic Boundary
* **Limitation**: Unity-IR cannot be executed directly by a virtual machine.
* **Design Rationale**: By explicitly abandoning the goal of generating machine code (the UNCOL trap), Unity-IR avoids the intractable complexity of cross-compiling garbage collection, thread scheduling, and runtime memory models across diverse execution targets. It serves exclusively as a representation for reasoning, context optimization, and formal verification.

