# Unity: A Universal Semantic Intermediate Representation for Repository-Scale Code Reasoning

**A Research Proposal for Scientific Inquiry**  
**Working Group:** Project Unity  
**Target Subject Area:** AI for Code, Program Analysis, and Representation Learning (NeurIPS / ICLR / POPL)

---

## Abstract

Modern large language models and frontier reasoning systems across both open-weights and API architectures exhibit measurable performance degradation when evaluated on repository-scale, multi-file software engineering tasks compared to isolated function synthesis. This degradation stems from three structural constraints: (1) **Context degradation and attention dilution**, where self-attention mechanisms suffer from quadratic compute overhead ($O(N^2)$) and recall failures over distributed, syntax-heavy multi-file contexts; (2) **Graph retrieval latency and maintenance costs**, where Code Property Graphs (CPGs) and Graph RAG architectures introduce multi-second traversal latencies, schema drift under frequent code churn, and brittle multi-hop graph querying; and (3) **Cross-lingual representation skew**, where severe pre-training distribution imbalances cause models to underperform in systems languages (Rust, C++, Go) relative to high-resource languages (Python, TypeScript).

This proposal outlines **Unity**, an inquiry into whether multi-language source code can be deterministically lowered into a canonical, language-agnostic intermediate representation (**Unity-IR**) optimized for transformer attention. Unity-IR decouples computational semantics from lexical syntax across three orthogonal layers: static system semantics (ownership, lifetimes, mutability, concurrency locks), first-order mathematical logic (quantified predicates, linear integer arithmetic bounds, state transitions), and disambiguated structural intent. By translating code via a deterministic compiler frontend rather than a probabilistic model, Unity eliminates translation hallucination while normalizing syntactic diversity. We formulate the formal operational semantics of this representation, detail the compiler lowering calculus, and specify an empirical evaluation across SWE-bench Multilingual, CrossCodeEval, RepoEval, and CRUXEval-X. We measure task resolution rates ($\text{pass}@k$), cross-lingual variance ($\sigma^2$), structural hallucination rates (SHR), and end-to-end retrieval and inference latencies across a controlled matrix of open-weights and frontier model architectures.

---

## 1. Introduction

Evaluating language models on real-world software engineering tasks requires reasoning across large repositories comprising hundreds of modules and tens of thousands of lines of code. Tasks such as cross-file bug repair, API migration, and security patch verification require models to track data flow, type invariants, and state transitions across distant file boundaries.

Current architectures address repository-scale reasoning through two primary paradigms:

1. **Direct Context Ingestion:** Long-context models ingest multiple source files directly. However, empirical studies confirm that effective reasoning degrades as context length increases, driven by attention dilution and the "lost-in-the-middle" effect (Liu et al., 2023; Hsieh et al., 2024). Crucially, raw code contains substantial syntactic boilerplate (import declarations, language-specific formatting, repetitive structural boilerplate) that consumes token budget and disperses attention weights away from causal dependency tokens.
2. **Graph-Based Retrieval (Graph RAG & CPGs):** Systems indexing codebases into Abstract Syntax Trees (AST), Control Flow Graphs (CFG), and Program Dependence Graphs (PDG) (Yamaguchi et al., 2014) capture structural dependencies. However, they introduce practical operational bottlenecks: whole-repository graph re-indexing upon every commit is computationally expensive, query-time graph traversal adds multi-second latencies per hop, and generating accurate graph queries remains brittle.

Compounding these architectural issues is **cross-lingual disparity**. Despite massive pre-training scale, training corpora remain heavily skewed toward Python, TypeScript, and Java (Lozhkov et al., 2024). On cross-lingual benchmarks like MultiPL-E (Cassano et al., 2023) and HumanEval-X (Zheng et al., 2023), models consistently show lower pass rates in Rust, C++, and Go than in Python on identical algorithmic problems. This performance deficit is largely attributable to compiler strictness (e.g., Rust's borrow checker and lifetime bounds), pointer semantics, and tokenization fragmentation over less represented syntax.

### 1.1 Intrinsic Invariant Verification vs. Extrinsic Dynamic Monitoring

A central challenge in contemporary agentic software engineering is the reliance on **extrinsic dynamic monitoring** to compensate for untrusted model generation. Because raw code generation lacks verifiable invariant guarantees, contemporary workflows encase models in heavy scaffolding: model-generated synthetic tests, runtime sandboxing, and multi-tier agent review loops.

This operational paradigm introduces three systemic trade-offs:
1. **Specification Drift in Synthetic Test Generation:** As code generation volume increases, models tasked with generating their own test suites and mocks often produce tautological tests that validate the model's own flawed assumptions while scaling test suite maintenance overhead linearly with codebase volume.
2. **Global Invariant Preservation in Large-Scale Code Synthesis:** Restricting model edits to narrow, localized line-level diffs prevents reasoning systems from verifying global, multi-hop architectural invariants across repository boundaries.
3. **Human Review Asymmetries in Multi-File Refactoring:** While code generation occurs rapidly, verifying non-local memory safety, concurrency races, and authorization invariants across large diffs imposes substantial cognitive load on human reviewers, leading to review fatigue and latent regressions.

**Unity replaces extrinsic dynamic monitoring with intrinsic semantic verification.** When program semantics, resource lifecycles, and state transitions are deterministically lowered into a canonical invariant space (Unity-IR), contract preservation becomes verifiable via automated decision procedures (Z3 SMT solver). Reviewers and models evaluate the **canonical semantic delta** ($\Delta \mathcal{S} = \mathcal{S}_{\text{post}} \ominus \mathcal{S}_{\text{pre}}$) over formal pre/post-conditions, isolating critical regressions into a decidable verification domain.

### 1.2 Core Hypotheses

We hypothesize that an intermediate representation designed around invariant preservation, explicit systems semantics, and mathematical logic can normalize cross-lingual disparities and improve multi-file reasoning efficiency:

$$\mathcal{H}_1: \quad \sigma^2_{\text{lang}}(\text{Unity-IR}) < \sigma^2_{\text{lang}}(\text{Raw Code})$$
$$\mathcal{H}_2: \quad \text{pass}@k(\text{Unity-IR}) \ge \text{pass}@k(\text{Graph RAG}) \quad \text{where} \quad T_{\text{retrieval}}(\text{Unity-IR}) \ll T_{\text{retrieval}}(\text{Graph RAG})$$

---

## 2. Related Work

### 2.1 Code Language Models and Cross-Lingual Evaluation
Recent foundation models demonstrate high capability in single-file code synthesis and test-time reasoning. However, multilingual benchmarks such as MultiPL-E (Cassano et al., 2023), BabelCode (Orlanski et al., 2023), and HumanEval-X (Zheng et al., 2023) highlight substantial cross-language variance. Models frequently fail to satisfy static compiler constraints in low-resource and systems languages even when the high-level algorithmic plan is sound.

### 2.2 Repository-Level Reasoning and Context Architectures
SWE-bench (Jimenez et al., 2024), SWE-bench Multilingual, RepoEval (Zhang et al., 2023), and CrossCodeEval (Ding et al., 2023) evaluate models on multi-file dependencies and repository-level issue resolution. To manage repository context:
- **RepoCoder** (Zhang et al., 2023) uses an iterative retrieval-generation framework.
- **Aider** (Gauthier, 2023) utilizes Tree-sitter and PageRank to generate a compact "Repo Map" of signatures. While token-efficient, signature maps omit the internal logic and operational invariants needed for multi-hop causal reasoning.

### 2.3 Program Analysis and Graph RAG
- **Code Property Graphs (CPGs):** Yamaguchi et al. (2014) combined AST, CFG, and PDG representations in Joern for vulnerability discovery.
- **Semantic Code Intelligence Protocol (SCIP):** Sourcegraph developed SCIP to index definitions, references, and hover metadata deterministically.
- **Graph RAG Systems:** Edge et al. (2024) and related implementations extract entity graphs and query them using hybrid vector-relational databases. While effective for global architectural queries, graph serialization into prompt contexts is verbose and incurs substantial query latencies.

### 2.4 Intermediate Representations in LLM Reasoning
- **Chain-of-Code (CoC):** Li et al. (2023) demonstrated that prompting LLMs to reason via pseudocode execution improves reasoning performance on BIG-bench Hard by 12% over Chain-of-Thought.
- **Compiler IRs:** Works utilizing LLVM IR or assembly (Cummins et al., 2021) preserve operational semantics but discard semantic intent, variable names, and type abstractions, increasing difficulty for autoregressive models.
- **Generic ASTs:** Frameworks such as Semgrep lower language-specific CSTs into a unified Generic AST to perform cross-language pattern matching. Unity extends this concept from syntactic matching to invariant-preserving semantic modeling.

---

## 3. Theoretical Framework & Operational Semantics

### 3.1 Problem Formalization
Let a repository $\mathcal{R}$ consist of modules $\mathcal{R} = \{M_1, M_2, \dots, M_n\}$ implemented in languages $\mathcal{L} = \{\ell_1, \dots, \ell_k\}$. A repository-level maintenance task $\mathcal{T} = \langle \mathcal{D}, \mathcal{R}, \mathcal{K} \rangle$ requires producing a patch $\Delta \mathcal{R}$ such that:
$$\text{Verify}(\mathcal{R} \oplus \Delta \mathcal{R}, \mathcal{K}) = 1$$
where $\mathcal{D}$ is an issue specification and $\mathcal{K}$ is an automated test suite. Resolving $\mathcal{T}$ requires maintaining valid execution invariants across an inter-procedural path:
$$\mathcal{C} = \left( s_0 \xrightarrow{f_1} s_1 \xrightarrow{f_2} s_2 \dots \xrightarrow{f_m} s_m \right)$$
where each transition $s_{j-1} \xrightarrow{f_j} s_j$ must satisfy local preconditions $\mathcal{P}(f_j)$, postconditions $\mathcal{Q}(f_j)$, and global repository constraints $\mathcal{I}_{\mathcal{R}}$.

### 3.2 Abstract State Space & Operational Transitions
We formalize the execution state $\mathcal{S}$ as a 4-tuple:
$$\mathcal{S} \triangleq \langle \Sigma, \mathcal{H}, \mathcal{L}, \mathcal{P} \rangle \in \text{State}$$
Where:
* $\Sigma : \text{Var} \rightharpoonup \mathcal{V}$ is the local variable environment over domain $\mathcal{V} \triangleq \mathbb{Z} \cup \mathbb{B} \cup \text{Str} \cup \text{Loc} \cup \{ \bot \}$.
* $\mathcal{H} : \text{Loc} \rightharpoonup \mathcal{V} \times \text{Type}$ is the shared heap state mapping locations to typed memory records.
* $\mathcal{L} \subseteq \text{LockId}$ is the set of active mutual exclusion locks acquired by the thread.
* $\mathcal{P} \in \langle \mathbb{P}, \le_{\text{purity}} \rangle$ is the purity capability lattice where $\mathbb{P} \triangleq \{ \text{Pure}, \text{Impure}(\mathcal{E}) \}$.

An operational transition executes action $\alpha \in \mathcal{A}$ to produce state $\mathcal{S}'$:
$$\langle \Sigma, \mathcal{H}, \mathcal{L}, \mathcal{P} \rangle \xrightarrow{\alpha} \langle \Sigma', \mathcal{H}', \mathcal{L}', \mathcal{P}' \rangle$$

### 3.3 Contract Refinement Preorder ($\sqsubseteq$)
For two symbol declarations $\mathcal{D}_1, \mathcal{D}_2$, declaration $\mathcal{D}_2$ **refines** $\mathcal{D}_1$ ($\mathcal{D}_2 \sqsubseteq \mathcal{D}_1$) if and only if:
$$\mathcal{D}_2 \sqsubseteq \mathcal{D}_1 \iff \begin{cases}
\forall \vec{x}, & P_{\mathcal{D}_1}(\vec{x}) \implies P_{\mathcal{D}_2}(\vec{x}) & \text{(Precondition Weakening)} \\
\forall \vec{x}, \vec{y}, & Q_{\mathcal{D}_2}(\vec{x}, \vec{y}) \implies Q_{\mathcal{D}_1}(\vec{x}, \vec{y}) & \text{(Postcondition Strengthening)} \\
& \mathcal{L}_{\mathcal{D}_1} \subseteq \mathcal{L}_{\mathcal{D}_2} & \text{(Lock Subsumption)} \\
& \mathcal{P}_{\mathcal{D}_2} \le_{\text{purity}} \mathcal{P}_{\mathcal{D}_1} & \text{(Purity Non-Degradation)}
\end{cases}$$

If an edit violates this preorder ($\mathcal{D}_2 \not\sqsubseteq \mathcal{D}_1$), the transformation is classified as an architectural regression (`ONE_WAY_DOOR`).

### 3.4 Attention Dilution in Raw Syntax
In raw source representations, the tokens describing invariant $\mathcal{I}$ are interleaved with language-specific syntax $\Omega_\ell$:
$$T(M_i) = T_{\text{semantic}}(\mathcal{I}) \cup T_{\text{syntax}}(\Omega_\ell)$$

For a transformer attention head with query $q_i$ and key $k_j$, the attention weight assigned to a causal semantic token $j \in T_{\text{semantic}}$ is:
$$\alpha_{i,j} = \frac{\exp\left(q_i k_j^T / \sqrt{d_k}\right)}{\sum_{u \in T_{\text{semantic}}} \exp\left(q_i k_u^T / \sqrt{d_k}\right) + \sum_{v \in T_{\text{syntax}}} \exp\left(q_i k_v^T / \sqrt{d_k}\right)}$$

As syntactic boilerplate $T_{\text{syntax}}(\Omega_\ell)$ grows across multiple files, the denominator increases, reducing the attention mass allocated to causal dependency tokens. Unity-IR reduces $|T_{\text{syntax}}|$ while standardizing $T_{\text{semantic}}$ into dense mathematical predicates.

---

## 4. The Unity Intermediate Representation (Unity-IR)

Unity-IR decouples computational semantics into three orthogonal layers:

```
+-------------------------------------------------------------------------+
| Layer 1: Contract & Systems Semantics                                   |
| • Globally unique canonical symbol identifier (@pkg.mod.Class.func)     |
| • Purity classification: pure | impure(IO) | impure(StateMutation:tgt)  |
| • Concurrency & synchronization: exclusive_lock | atomic | csp_channel   |
| • Resource semantics: mutable_borrow | shared_borrow | owned            |
+-------------------------------------------------------------------------+
| Layer 2: Algorithmic Core (Mathematical Logic)                          |
| • Preconditions (P) and Postconditions (Q) in QF_LIA                    |
| • First-order quantifiers (∀, ∃) over input collections                 |
| • Relational transformations: Map, Filter, Fold                         |
| • State transition deltas: S_{t+1} = S_t ⊕ {k ↦ v}                      |
+-------------------------------------------------------------------------+
| Layer 3: Causal Topology & Controlled Natural Language                  |
| • Declarative intent statements and descriptive domain identifiers      |
| • Explicit @symbol causal references resolved via SCIP/LSP protocols    |
+-------------------------------------------------------------------------+
```

### 4.1 Cross-Lingual Equivalence Example

Consider a concurrent state update implemented in Python and Go:

```python
# Python
class Ledger:
    def withdraw(self, account_id: str, amount: int) -> int:
        if amount <= 0:
            raise ValueError("InvalidAmount")
        with self.mu:
            if account_id not in self.balances:
                raise KeyError("NotFound")
            current = self.balances[account_id]
            if current < amount:
                raise ValueError("InsufficientFunds")
            self.balances[account_id] = current - amount
            return self.balances[account_id]
```

```go
// Go
func (l *Ledger) Withdraw(accountID string, amount int64) (int64, error) {
    if amount <= 0 {
        return 0, ErrInvalidAmount
    }
    l.mu.Lock()
    defer l.mu.Unlock()
    current, exists := l.balances[accountID]
    if !exists {
        return 0, ErrNotFound
    }
    if current < amount {
        return 0, ErrInsufficientFunds
    }
    l.balances[accountID] = current - amount
    return l.balances[accountID], nil
}
```

Both implementations lower deterministically to the identical canonical Unity-IR representation:

```
SYMBOL: @ledger.Ledger.withdraw
CONTRACT:
  PARAMS: (account_id: Str, amount: Int64)
  RETURNS: Result<Int64, Error[NotFound | InvalidAmount | InsufficientFunds]>
  SYSTEMS: [concurrency: exclusive_lock(self.mu), purity: impure(StateMutation:self.balances)]

PRECONDITIONS:
  P1: isValidId(account_id)
  P2: amount > 0
  P3: account_id in self.balances
  P4: self.balances[account_id] >= amount

EXECUTION_LOGIC:
  1. EVALUATE: valid_amount = amount > 0
     ASSERT: valid_amount == True ELSE THROW InvalidAmount
  2. ACQUIRE: exclusive_lock(self.mu)
  3. QUERY: current = self.balances[account_id]
     ASSERT: current != None ELSE THROW NotFound
  4. EVALUATE: proposed = current - amount
     ASSERT: proposed >= 0 ELSE THROW InsufficientFunds
  5. MUTATE: self.balances[account_id] := proposed
  6. RELEASE: exclusive_lock(self.mu)
  7. RETURN: proposed

POSTCONDITIONS:
  Q1: self.balances[account_id] == current - amount
  Q2: self.balances[account_id] >= 0
  Q3: RESULT == self.balances[account_id]

CAUSAL_TOPOLOGY:
  CALLED_BY: @api.handlers.execute_withdrawal
```

### 4.2 Epistemic Distinction: Intent vs. Operational Mechanism
Unity-IR does not claim to magically infer human teleological intent ($\text{Spec}$) out of buggy source syntax ($\text{Impl}$). Deriving $\text{Spec}$ from $\text{Impl}$ alone is impossible without external specifications.

Instead, Unity provides **Differential Invariant Preservation**:
1. It canonicalizes the operational contract of the reference baseline ($\text{Impl}_{\text{pre}}$).
2. When a modification ($\text{Impl}_{\text{post}}$) is proposed, Unity verifies that existing invariants, preconditions, and synchronization boundaries are not silently violated ($\text{Impl}_{\text{post}} \sqsubseteq \text{Impl}_{\text{pre}}$).
3. Layer 3 Controlled Natural Logic retains domain-specific identifier tokens (`account_id`, `balances`, `mu`), ensuring that neural language models retain full pragmatic context for fuzzy intent-matching.

---

## 5. Controlled Empirical Protocol

### 5.1 Research Questions
- **RQ1 (Cross-Lingual Parity):** Does Unity-IR reduce performance variance ($\sigma^2_{\text{lang}}$) across programming languages compared to raw source code?
- **RQ2 (Multi-Hop Causal Reasoning):** How does Unity-IR compare to Graph RAG in issue resolution accuracy and query-time latency?
- **RQ3 (Context Compression & Attention Prefill):** Does invariant compression reduce GPU self-attention FLOPs and improve retrieval accuracy over long dependency chains?
- **RQ4 (Structural Hallucination):** Does grounding reasoning in explicit contract layers decrease the rate of invalid symbol invocations?

### 5.2 Benchmark Suites
1. **SWE-bench Multilingual:** 300 curated repository issues across 9 languages (Python, Java, Go, Rust, C++, C#, TypeScript, Ruby, PHP).
2. **CrossCodeEval:** Cross-file completion tasks evaluated across Python, Java, TypeScript, and C#.
3. **RepoEval:** Multi-file completion measuring line, function, and API dependency retrieval.
4. **CRUXEval-X:** Multilingual execution simulation measuring model state tracking.
5. **Concurrency Invariant Test Suite:** 100 multi-threaded synchronization tasks testing race and deadlock identification across multi-file boundaries.

### 5.3 Baseline Conditions
- **$C_0$ (Raw Long-Context):** Ingest raw source files directly into prompt context.
- **$C_1$ (Dense Vector RAG):** BM25 + dense embedding retrieval over file chunks.
- **$C_2$ (Aider Signature Map):** Tree-sitter PageRank signature map.
- **$C_3$ (Code Property Graph RAG):** Neo4j CPG (AST+CFG+PDG) with sub-graph serialization.
- **$C_4$ (Compiler Bytecode):** LLVM IR / WebAssembly text format.
- **$C_5$ (Unity-IR):** Proposed deterministic 3-layer representation.

### 5.4 Evaluated Model Matrix
To ensure reproducibility and eliminate commercial variance, our primary evaluation is conducted across a controlled matrix of open-weights models across parameter scales, alongside representative frontier API baselines:

| Model Tier | Architecture | Parameter Scale | Context Window | Execution Environment |
| :--- | :--- | :--- | :--- | :--- |
| **Compact Open-Weights** | Qwen 2.5 Coder | 7B / 14B | 32k tokens | Local vLLM / SGLang ($T=0$) |
| **Mid-Scale Open-Weights** | Qwen 2.5 Coder | 32B | 32k tokens | Local vLLM / SGLang ($T=0$) |
| **Frontier Open-Weights** | DeepSeek-Coder-V2 | 16B / 236B MoE | 64k tokens | Multi-GPU cluster ($T=0$) |
| **Frontier Open-Weights** | Llama 3 Code | 70B | 64k tokens | Multi-GPU cluster ($T=0$) |
| **Frontier Reference API** | Claude 3.5 Sonnet / GPT-4o | Proprietary | 128k tokens | Version-pinned API snapshots |

**Hyperparameter Control**: All evaluations enforce greedy decoding ($T=0$), fixed seed ($S=42$), standardized prompt scaffolds, and a minimum of $N=30$ runs per condition to compute 95% confidence intervals ($\mu \pm 1.96 \frac{\sigma}{\sqrt{N}}$).

### 5.5 Hardware Profiling Standards
Lowering throughput and inference latency are benchmarked on explicit, reproducible hardware:
* **Ingestion Testbed**: Multi-core x86-64 (AMD EPYC 7763, 64 cores) and Apple Silicon M-series (16-core unified memory).
* **Inference Serving**: 8x NVIDIA H100 80GB SXM5 nodes utilizing TensorRT-LLM and vLLM with RadixTree prefix caching.

---

## 6. Scope Boundaries, Assumptions & Limitations

In accordance with scholarly rigor, we explicitly document the operational limitations and boundary conditions of Project Unity:

### 6.1 Dynamic Typing & Runtime Metaprogramming
* **Limitation**: Dynamic constructs such as Python runtime `eval()`, dynamic `getattr` introspection, and monkey-patching cannot be completely resolved into closed-form static contracts.
* **Mitigation**: Such expressions fall back to `UNKNOWN_MUTATION` nodes and trigger `VerificationStatus.CONSERVATIVE_SYNTACTIC_CHECK`, requiring human review rather than autonomous approval.

### 6.2 Complex Heap Pointer Aliasing
* **Limitation**: Unbounded, cyclic pointer graphs in unmanaged languages (C/C++) exceed the expressiveness of linear contract extraction.
* **Scope Boundary**: Unity targets application-level state mutations, concurrent lock synchronization, and API contracts rather than machine-level alias analysis.

### 6.3 Strictly Monotonic One-Way Lowering
* **Design Rationale**: Unity-IR is not decompiled back into source code. Autonomous agents write native source code directly (producing standard Git diffs); Unity-IR serves strictly as an epistemic representation for comprehension and differential verification.

---

## 7. Execution Plan & Milestones

| Phase | Milestone | Deliverables |
| :--- | :--- | :--- |
| **Phase 1: Dual-Anchor Lowering** | Milestone 0 & 1 (Completed) | Tree-sitter frontend, canonical emitter, Z3 SMT delta engine, and cross-lingual equivalence test suite. |
| **Phase 2: Scalability & Caching** | Milestone 2 | Multicore batching pipeline, content-addressable storage cache, SCIP/LSP integration. |
| **Phase 3: Controlled Empirical Sweeps** | Milestone 3 | Full benchmark execution across $C_0$–$C_5$ over SWE-bench Multilingual and CrossCodeEval. |
| **Phase 4: Manuscript Preparation** | Milestone 4 | Statistical significance testing, ablation analysis, open-source artifact release. |

---

## 8. References

1. **Cassano, F., et al. (2023).** MultiPL-E: A Scalable and Polyglot Approach to Benchmarking Neural Code Generation. *IEEE TSE*, 49(7), 3675-3691.
2. **Cummins, C., et al. (2021).** Program Analysis with CompilerGym. *NeurIPS Datasets and Benchmarks*.
3. **Ding, Y., et al. (2023).** CrossCodeEval: A Diverse and Multilingual Benchmark for Cross-File Code Completion. *NeurIPS 2023*.
4. **Edge, D., et al. (2024).** From Local to Global: A Graph RAG Approach to Query-Focused Summarization. *arXiv:2404.16130*.
5. **Gauthier, P. (2023).** Aider: AI Pair Programming in Your Terminal with Tree-Sitter Repository Maps.
6. **Hsieh, C. Y., et al. (2024).** Ruler: What's the Real Effective Context Window of Your Long-Context Language Model? *arXiv:2404.06654*.
7. **Jimenez, C. E., et al. (2024).** SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*.
8. **Li, C., et al. (2023).** Chain of Code: Reasoning with a Language Model-Augmented Code Interpreter. *NeurIPS 2023*.
9. **Liu, N. F., et al. (2023).** Lost in the Middle: How Language Models Use Long Contexts. *TACL*, 12, 157-173.
10. **Lozhkov, A., et al. (2024).** StarCoder 2 and The Stack v2: The Next Generation. *arXiv:2402.19173*.
11. **Yamaguchi, F., et al. (2014).** Modeling and Discovering Vulnerabilities with Code Property Graphs. *IEEE S&P 2014*.
12. **Zhang, F., et al. (2023).** RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation. *EMNLP 2023*.
13. **Zhang, J., et al. (2023).** RepoEval: Evaluating Long-Context and Repository-Level Code Models. *arXiv:2303.12570*.
14. **Zheng, Q., et al. (2023).** CodeGeeX: A Pre-Trained Multilingual Model for Code Generation. *arXiv:2303.17568*.

---

## Appendix: Reproducibility & Toolchain Architecture

To ensure complete experimental reproducibility, the implementation utilizes deterministic, verified components:
* **Syntax Parsing**: Tree-sitter C bindings (`tree-sitter`) providing single-pass, re-entrant CST generation.
* **Formal Decision Procedures**: Z3 Automated Theorem Prover (`z3-solver`) for Quantifier-Free Linear Integer Arithmetic (QF_LIA) entailment.
* **Grammar Specification**: Canonical EBNF specification parsed via Lark (`lark`).
* **Test Automation**: Hypothesis property-based testing and pytest validation suites.
