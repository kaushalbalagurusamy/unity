# Unity: A Universal Semantic Intermediate Representation for Repository-Scale Code Reasoning

**A Research Proposal for Scientific Inquiry**  
**Working Group:** Project Unity  
**Target Publication:** NeurIPS / ICLR (AI for Code, Reasoning, and Representation Learning)

---

## Abstract

Language models trained on code exhibit substantial performance degradation when evaluated on multi-file software engineering tasks compared to isolated, single-function generation. This gap is driven by three underlying constraints: (1) **Context degradation**, where attention mechanisms suffer recall and reasoning failures over long, multi-file contexts; (2) **Graph retrieval latency and maintenance costs**, where Code Property Graphs (CPGs) and Graph RAG architectures introduce multi-second query latencies, synchronization drift against code churn, and brittle multi-hop traversal; and (3) **Cross-lingual representation skew**, where severe pre-training distribution imbalances cause models to underperform in systems languages (Rust, C++, Go) and enterprise stacks (Java, COBOL) relative to Python and JavaScript.

This proposal outlines **Unity**, an inquiry into whether multi-language source code can be deterministically lowered into a canonical, language-agnostic intermediate representation (**Unity-IR**) optimized for transformer attention. Unity-IR decouples computational semantics from lexical syntax through three layers: static system semantics (ownership, lifetimes, mutability, concurrency locks), first-order mathematical logic (quantified predicates, loop invariants, state transitions), and disambiguated structural intent. By translating code via a deterministic compiler frontend rather than a probabilistic model, Unity avoids translation hallucination while normalizing syntactic diversity. We formulate the theoretical foundations of this representation, detail the compiler lowering architecture, and specify an empirical evaluation across SWE-bench Multilingual, CrossCodeEval, RepoEval, and CRUXEval-X to measure task resolution rates (pass@$k$), cross-lingual variance ($\sigma^2$), structural hallucination rates (SHR), and end-to-end retrieval and inference latencies.

---

## 1. Introduction

Evaluating language models on real-world software engineering tasks requires reasoning across large repositories comprising hundreds of modules and tens of thousands of lines of code. Tasks such as cross-file bug repair, API migration, and security patch verification require models to track data flow, type invariants, and state transitions across distant file boundaries.

Current architectures address repository-scale reasoning through two primary methods:

1. **Direct Context Ingestion:** Long-context models (128k–1M tokens) ingest multiple source files directly. However, empirical studies show that effective reasoning degrades sharply as context grows, driven by the "lost-in-the-middle" effect (Liu et al., 2023; Hsieh et al., 2024). Crucially, raw code contains substantial syntactic boilerplate (import declarations, language-specific formatting, repetitive boilerplate) that dilutes attention weights on key causal tokens.
2. **Graph-Based Retrieval (Graph RAG & CPGs):** Systems like Joern (Yamaguchi et al., 2014), Sourcegraph SCIP, Greptile, and Microsoft GraphRAG index codebases into Abstract Syntax Tree (AST), Control Flow Graph (CFG), and Program Dependence Graph (PDG) structures. While graph representations capture structural dependencies, they introduce practical operational bottlenecks: database re-indexing upon every commit is computationally expensive, query-time graph traversal adds 2–10 seconds of latency per hop, and generating accurate graph queries (e.g. Cypher) remains brittle.

Compounding these architectural issues is **cross-lingual disparity**. Pre-training corpora such as The Stack v2 (Lozhkov et al., 2024) and StarCoder (Li et al., 2023) are predominantly composed of Python, JavaScript, and Java. On cross-lingual benchmarks like MultiPL-E (Cassano et al., 2023) and HumanEval-X (Zheng et al., 2023), models consistently score 15–35% lower in Rust, C++, and Go than in Python on identical algorithmic problems. This performance deficit is largely attributable to compiler strictness (e.g., Rust's borrow checker), pointer semantics, and tokenization fragmentation over less represented syntax.

### Core Hypothesis

We hypothesize that an intermediate representation designed around invariant preservation, explicit systems semantics, and mathematical logic can normalize cross-lingual disparities and improve multi-file reasoning efficiency:

$$\mathcal{H}_1: \quad \sigma^2_{\text{lang}}(\text{Unity-IR}) < \sigma^2_{\text{lang}}(\text{Raw Code})$$
$$\mathcal{H}_2: \quad \text{pass}@k(\text{Unity-IR}) \ge \text{pass}@k(\text{Graph RAG}) \quad \text{where} \quad T_{\text{retrieval}}(\text{Unity-IR}) \ll T_{\text{retrieval}}(\text{Graph RAG})$$

---

## 2. Related Work

### 2.1 Code Language Models and Cross-Lingual Evaluation
Recent code foundation models—including Code Llama (Rozière et al., 2023), StarCoder2 (Lozhkov et al., 2024), DeepSeek-Coder-V2 (Zhu et al., 2024), and Qwen2.5-Coder (Hui et al., 2024)—demonstrate strong capability in single-file code generation. However, multilingual benchmarks such as MultiPL-E (Cassano et al., 2023), BabelCode (Orlanski et al., 2023), and HumanEval-X (Zheng et al., 2023) highlight substantial cross-language variance. Models frequently fail to satisfy static compiler constraints in low-resource and systems languages even when the high-level algorithmic plan is sound.

### 2.2 Repository-Level Reasoning and Context Architectures
Moving beyond isolated functions, SWE-bench (Jimenez et al., 2024), SWE-bench Multilingual, RepoEval (Zhang et al., 2023), and CrossCodeEval (Ding et al., 2023) test models on multi-file dependencies and repository-level issue resolution. To manage repository context:
- **RepoCoder** (Zhang et al., 2023) uses an iterative retrieval-generation framework.
- **Aider** (Gauthier, 2023) utilizes Tree-sitter and PageRank to generate a compact "Repo Map" of function and class signatures. While token-efficient, signature maps omit the internal logic and operational invariants needed for multi-hop causal reasoning.

### 2.3 Program Analysis and Graph RAG
Deterministic program representations form the core of static analysis:
- **Code Property Graphs (CPGs):** Yamaguchi et al. (2014) combined AST, CFG, and PDG representations in Joern for vulnerability discovery.
- **Semantic Code Intelligence Protocol (SCIP):** Sourcegraph developed SCIP to index definitions, references, and hover metadata deterministically.
- **Graph RAG Systems:** Edge et al. (2024), Greptile, and related commercial implementations extract entity graphs and query them using hybrid vector-relational databases. While effective for global architectural queries, graph serialization into prompt contexts is verbose and incurs substantial query latencies.

### 2.4 Intermediate Representations in LLM Reasoning
Intermediate representations have repeatedly been shown to improve reasoning:
- **Chain-of-Code (CoC):** Li et al. (2023) demonstrated that prompting LLMs to reason via pseudocode execution and LMulation improves reasoning performance on BIG-bench Hard by 12% over Chain-of-Thought.
- **Compiler IRs:** Works utilizing LLVM IR or assembly (Cummins et al., 2021) preserve operational semantics but discard semantic intent, variable names, and type abstractions, increasing difficulty for autoregressive models.
- **Generic ASTs:** Frameworks such as Semgrep lower language-specific Tree-sitter CSTs into a unified Generic AST to perform cross-language pattern matching. Unity extends this concept from syntactic matching to invariant-preserving semantic modeling.

---

## 3. Theoretical Framework

### 3.1 Problem Formalization
Let a repository $\mathcal{R}$ consist of modules $\mathcal{R} = \{M_1, M_2, \dots, M_n\}$ implemented in languages $\mathcal{L} = \{\ell_1, \dots, \ell_k\}$. A repository-level maintenance task $\mathcal{T} = \langle \mathcal{D}, \mathcal{R}, \mathcal{K} \rangle$ requires producing a patch $\Delta \mathcal{R}$ such that:
$$\text{Verify}(\mathcal{R} \oplus \Delta \mathcal{R}, \mathcal{K}) = 1$$
where $\mathcal{D}$ is an issue specification and $\mathcal{K}$ is an automated test suite. Resolving $\mathcal{T}$ requires maintaining valid execution invariants across an inter-procedural path:
$$\mathcal{C} = \left( s_0 \xrightarrow{f_1} s_1 \xrightarrow{f_2} s_2 \dots \xrightarrow{f_m} s_m \right)$$
where each transition $s_{j-1} \xrightarrow{f_j} s_j$ must satisfy local preconditions $\mathcal{P}(f_j)$, postconditions $\mathcal{Q}(f_j)$, and global repository constraints $\mathcal{I}_{\mathcal{R}}$.

### 3.2 Attention Dilution in Raw Syntax
In raw source representations, the tokens describing invariant $\mathcal{I}$ are interleaved with language-specific syntax $\Omega_\ell$:
$$T(M_i) = T_{\text{semantic}}(\mathcal{I}) \cup T_{\text{syntax}}(\Omega_\ell)$$

For a transformer attention head with query $q_i$ and key $k_j$, the attention weight assigned to a causal semantic token $j \in T_{\text{semantic}}$ is:
$$\alpha_{i,j} = \frac{\exp\left(q_i k_j^T / \sqrt{d_k}\right)}{\sum_{u \in T_{\text{semantic}}} \exp\left(q_i k_u^T / \sqrt{d_k}\right) + \sum_{v \in T_{\text{syntax}}} \exp\left(q_i k_v^T / \sqrt{d_k}\right)}$$

As syntactic boilerplate $T_{\text{syntax}}(\Omega_\ell)$ grows across multiple files, the denominator increases, reducing the attention mass allocated to causal dependency tokens. Unity-IR reduces $|T_{\text{syntax}}|$ while standardizing $T_{\text{semantic}}$ into dense mathematical predicates.

---

## 4. The Unity Intermediate Representation (Unity-IR)

Unity-IR decouples computational semantics into three orthogonal, standardized layers:

```
+-------------------------------------------------------------------------+
| Layer 1: Contract & Systems Semantics                                   |
| • Globally unique canonical symbol identifier (@pkg.mod.Class.func)     |
| • Purity classification: pure | impure(IO) | impure(StateMutation:tgt)  |
| • Concurrency & synchronization: exclusive_lock | atomic | csp_channel   |
| • Resource semantics: mutable_borrow | shared_borrow | owned            |
+-------------------------------------------------------------------------+
| Layer 2: Algorithmic Core (Mathematical Logic)                          |
| • Preconditions (P) and Postconditions (Q)                              |
| • First-order quantifiers (∀, ∃) over input collections                 |
| • Relational transformations: Map, Filter, Fold                         |
| • State transition deltas: S_{t+1} = S_t ⊕ {k ↦ v}                      |
+-------------------------------------------------------------------------+
| Layer 3: Causal Topology & Controlled Natural Language                  |
| • Declarative EBNF intent statements                                    |
| • Explicit @symbol causal references to upstream/downstream dependencies|
+-------------------------------------------------------------------------+
```

### 4.1 Cross-Lingual Translation Example

Consider a concurrent state update implemented in Rust and Go.

#### Source Implementations

```rust
// Rust
pub async fn update_balance(id: &str, delta: i64, vault: &Arc<Mutex<Vault>>) -> Result<i64, Error> {
    let mut guard = vault.lock().await;
    let current = guard.get(id).copied().ok_or(Error::NotFound)?;
    if current + delta < 0 { return Err(Error::InsufficientFunds); }
    guard.set(id, current + delta);
    Ok(current + delta)
}
```

```go
// Go
func UpdateBalance(ctx context.Context, id string, delta int64, vault *Vault) (int64, error) {
    vault.mu.Lock()
    defer vault.mu.Unlock()
    current, exists := vault.Balances[id]
    if !exists { return 0, ErrNotFound }
    if current + delta < 0 { return 0, ErrInsufficientFunds }
    vault.Balances[id] = current + delta
    return current + delta, nil
}
```

#### Canonical Unity-IR Representation

Both implementations lower deterministically to the identical representation:

```
SYMBOL: @vault.ledger.update_balance
CONTRACT:
  PARAMS: (id: Str, delta: Int64, vault: Ref<Vault>)
  RETURNS: Result<Int64, Error[NotFound | InsufficientFunds]>
  SYSTEMS: [concurrency: exclusive_lock(vault.mu), purity: impure(StateMutation:vault.balances)]

PRECONDITIONS:
  P1: isValidId(id)
  P2: isAlive(vault)

EXECUTION_LOGIC:
  1. ACQUIRE: exclusive_lock(vault.mu)
  2. QUERY: current = vault.balances[id]
     ASSERT: current != None ELSE THROW NotFound
  3. EVALUATE: proposed = current + delta
     ASSERT: proposed >= 0 ELSE THROW InsufficientFunds
  4. MUTATE: vault.balances[id] := proposed
  5. RELEASE: exclusive_lock(vault.mu)

POSTCONDITIONS:
  Q1: vault.balances[id] == current + delta
  Q2: RESULT == vault.balances[id]
```

### 4.2 Deterministic Lowering Pipeline

To eliminate hallucination risks during intermediate representation construction, Unity does not use an LLM for translation. The frontend uses deterministic static analysis:

```
Source Files (Python, Rust, Go, Java, C++)
  │
  ▼  Tree-sitter Parsers
Concrete Syntax Trees (CST)
  │
  ▼  Normalization Pass
Generic AST (Canonical control structures & types)
  │
  ▼  Analysis Engine (CFG/DFG & Abstract Interpretation)
Invariants, Lifetimes, Mutability, & Concurrency Scopes
  │
  ▼  Emitter
Canonical Unity-IR Documents (Cached per AST subtree hash)
```

---

## 5. Experimental Design

### 5.1 Research Questions
- **RQ1 (Cross-Lingual Parity):** Does Unity-IR reduce performance variance across languages compared to raw code?
- **RQ2 (Multi-Hop Causal Reasoning):** How does Unity-IR compare to Graph RAG in issue resolution accuracy and query latency?
- **RQ3 (Context Compression & Recall):** Does mathematical invariant compression reduce token consumption and improve recall over long dependency chains?
- **RQ4 (Structural Hallucination):** Does grounding reasoning in explicit contract layers decrease the rate of invalid symbol calls?

### 5.2 Benchmark Suites
1. **SWE-bench Multilingual:** 300 curated repository issues across 9 programming languages (Python, Java, Go, Rust, C++, C#, TypeScript, Ruby, PHP).
2. **SWE-bench Java:** 91 multi-file enterprise issue-patch verification pairs.
3. **CrossCodeEval:** Cross-file completion tasks evaluated across Python, Java, TypeScript, and C#.
4. **RepoEval:** Multi-file completion measuring line, function, and API dependency retrieval.
5. **CRUXEval-X:** Multilingual execution simulation measuring model state tracking.
6. **Concurrency Invariant Test Suite:** 100 multi-threaded synchronization tasks testing race and deadlock identification across 5–15 file boundaries.

### 5.3 Baseline Conditions
- **$C_0$ (Raw Long-Context):** Ingest raw files directly into the context window.
- **$C_1$ (Dense Vector RAG):** BM25 + dense vector embeddings (`text-embedding-3-large`).
- **$C_2$ (Aider Repo Map):** Tree-sitter PageRank signature map.
- **$C_3$ (Code Graph RAG):** Neo4j CPG (AST+CFG+PDG) with LLM-generated node summaries.
- **$C_4$ (Compiler Bytecode):** LLVM IR / Wasm text format.
- **$C_5$ (Unity-IR):** Proposed deterministic 3-layer representation.

### 5.4 Evaluated Models
- **Proprietary:** Claude 3.5 Sonnet, GPT-4o, Gemini 2.0 Flash.
- **Open-Weights:** DeepSeek-Coder-V2 (236B MoE), Qwen2.5-Coder (32B), Code Llama (70B).

### 5.5 Evaluation Metrics
- **Task Accuracy (pass@$k$):** Verified against Docker test suites.
- **Cross-Lingual Disparity ($\sigma^2_{\text{lang}}$):**
  $$\sigma^2_{\text{lang}} = \frac{1}{|L|} \sum_{\ell \in L} (\text{pass}@1(\ell) - \mu)^2$$
- **Structural Hallucination Rate (SHR):** Fraction of referenced symbols not present in repository symbol tables.
- **Token Efficiency Ratio (TER):** Token reduction factor relative to raw source code.
- **Latency Profile:** Indexing time ($T_{\text{index}}$), retrieval time ($T_{\text{retrieval}}$), and inference time ($T_{\text{inference}}$).

---

## 6. Execution Plan & Milestones

| Phase | Duration | Key Deliverables |
| :--- | :--- | :--- |
| **Phase 1: Compiler Frontend** | Months 1–2 | Tree-sitter lowering pipelines for Python, Go, Rust, Java, and C++. |
| **Phase 2: Invariant Synthesis** | Months 3–4 | CFG/DFG analysis passes, lifetime/concurrency inference, Unity-IR emitter. |
| **Phase 3: Empirical Sweeps** | Months 5–6 | Full evaluation across $C_0$–$C_5$ on SWE-bench Multilingual and CrossCodeEval. |
| **Phase 4: Analysis & Writing** | Months 7–8 | Statistical significance verification, manuscript preparation, artifact release. |

---

## 7. References

1. **Ahia, O., et al. (2023).** Do Language Models Dream of Clean Code? On the Tokenization and Cross-Lingual Transfer in Code LLMs. *ACL 2023*.
2. **Cassano, F., et al. (2023).** MultiPL-E: A Scalable and Polyglot Approach to Benchmarking Neural Code Generation. *IEEE TSE*, 49(7), 3675-3691.
3. **Cummins, C., et al. (2021).** Program Analysis with CompilerGym. *NeurIPS Datasets and Benchmarks*.
4. **Ding, Y., et al. (2023).** CrossCodeEval: A Diverse and Multilingual Benchmark for Cross-File Code Completion. *NeurIPS 2023*.
5. **Edge, D., et al. (2024).** From Local to Global: A Graph RAG Approach to Query-Focused Summarization. *arXiv:2404.16130*.
6. **Gauthier, P. (2023).** Aider: AI Pair Programming in Your Terminal with Tree-Sitter Repository Maps.
7. **Hsieh, C. Y., et al. (2024).** Ruler: What's the Real Effective Context Window of Your Long-Context Language Model? *arXiv:2404.06654*.
8. **Hui, B., et al. (2024).** Qwen2.5-Coder: Open Technical Report. *arXiv:2409.12186*.
9. **Jimenez, C. E., et al. (2024).** SWE-bench: Can Language Models Resolve Real-World GitHub Issues? *ICLR 2024*.
10. **Lattner, C., & Adve, V. (2004).** LLVM: A Compilation Framework for Lifelong Program Analysis & Transformation. *CGO 2004*.
11. **Li, C., et al. (2023).** Chain of Code: Reasoning with a Language Model-Augmented Code Interpreter. *NeurIPS 2023*.
12. **Liu, N. F., et al. (2023).** Lost in the Middle: How Language Models Use Long Contexts. *TACL*, 12, 157-173.
13. **Lozhkov, A., et al. (2024).** StarCoder 2 and The Stack v2: The Next Generation. *arXiv:2402.19173*.
14. **Luo, Z., et al. (2024).** RepoAgent: An LLM-Powered Agent Framework for Repository-Level Documentation and Comprehension. *arXiv:2402.16667*.
15. **Orlanski, G., et al. (2023).** Measuring Cross-Language Code Generation on BabelCode. *ICLR 2023*.
16. **Rozière, B., et al. (2023).** Code Llama: Open Foundation Models for Code. *arXiv:2308.12950*.
17. **Yamaguchi, F., et al. (2014).** Modeling and Discovering Vulnerabilities with Code Property Graphs. *IEEE S&P 2014*.
18. **Zhang, F., et al. (2023).** RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation. *EMNLP 2023*.
19. **Zhang, J., et al. (2023).** RepoEval: Evaluating Long-Context and Repository-Level Code Models. *arXiv:2303.12570*.
20. **Zheng, Q., et al. (2023).** CodeGeeX: A Pre-Trained Multilingual Model for Code Generation. *arXiv:2303.17568*.
21. **Zhu, Q., et al. (2024).** DeepSeek-Coder-V2: Breaking the Barrier of Closed-Source Models in Code Intelligence. *arXiv:2406.11931*.
