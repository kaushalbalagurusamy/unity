# ADR-0001: Python and Go Dual-Anchor Wedge for Tree-Sitter UAST Lowering

* **Status:** Accepted
* **Date:** 2026-09-09
* **Authors:** Kaushal Balagurusamy & Project Unity Working Group
* **Deciders:** Project Unity & Software Factory Core Engineering

---

## 1. Context and Problem Statement
Language models exhibit steep cross-lingual performance variance ($\sigma^2_{\text{lang}}$) between dynamic languages (Python) and systems languages (Go, Rust). To prove that Unity-IR can normalize code across paradigms, we need an initial proof-of-concept wedge that demonstrates that identical computational semantics in two fundamentally different languages lower to the exact same canonical representation.

## 2. Decision Drivers
* **Cross-Lingual Parity:** Prove structural and invariant identity between dynamic duck-typed code (Python) and statically typed concurrent code (Go).
* **Deterministic Lowering:** Reject probabilistic LLM-based translation in favor of deterministic Tree-sitter static analysis.
* **Scope Discipline:** Avoid tackling 10 languages at once; establish a rock-solid dual anchor before expanding to Rust and C++.
* **Concurrency Representation:** Prove that Python's `threading.Lock` and Go's `sync.Mutex` lower to the exact same `exclusive_lock` scope invariant.

## 3. Considered Options
* **Option 1: Python Only** (Lowest barrier, but proves nothing about cross-lingual normalization).
* **Option 2: All 5 Major Languages Simultaneously (Python, Go, Rust, C++, Java)** (Excessive scope; slow feedback loop).
* **Option 3: Python + Go Dual-Anchor Wedge** (Ideal balance of paradigm contrast and scoping).

---

## 4. Decision Outcome
**Chosen Option:** **Option 3**, because Python and Go represent opposing poles of the language design spectrum:
* Python: Dynamic typing, reference-counted GC, GIL, context managers (`with lock:`).
* Go: Static typing, CSP concurrency (`sync.Mutex`, goroutines, channels), explicit multiple return error tuples.

Proving that a concurrent bank ledger in Python and Go compiles to an identical, byte-for-byte or structurally identical `canonical_ledger.uir` conclusively establishes the core hypothesis of Project Unity ($\mathcal{H}_1$).

### Positive Consequences
* **Immediate Testability:** Milestone 0 creates `ledger.py` and `ledger.go` alongside `canonical_ledger.uir`, providing an instant deterministic quality gate for the compiler in Milestone 1.
* **Clear Design-by-Contract Mapping:** Python's `@deal` decorators map directly to Go's explicit guard clauses and return error patterns.

### Negative Consequences & Mitigations
* **Typing Gap in Python:** Untyped Python cannot specify 64-bit integer bounds.
  * *Mitigation:* Require modern PEP 484 type annotations on Python source anchors.

---

## 5. Pros and Cons of the Options

### Option 1: Python Only
* Good: Fast to build frontend.
* Bad: Does not validate cross-lingual invariant equivalence; fails the primary research goal.

### Option 2: 5 Languages at Once
* Good: Maximum theoretical breadth.
* Bad: Premature optimization; slows down compiler iteration; high maintenance overhead.

### Option 3: Python + Go Dual Anchor
* Good: Sufficient paradigm diversity (dynamic vs. static, exceptions vs. error values) to prove the thesis; tight, test-driven feedback loop.
* Bad: Defers Rust borrow-checker semantics to Milestone 2.
