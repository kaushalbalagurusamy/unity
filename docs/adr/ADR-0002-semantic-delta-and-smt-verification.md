# ADR-0002: Canonical Semantic Delta (ΔS) Engine & Z3 SMT Contract Verification

## Status
Ratified

## Date
September 2026

## Context
Standard version control diffs (such as line-by-line `git diff`) operate purely on textual tokens. They are fundamentally blind to systems-level semantics, synchronization bounds, and state invariants:
1. **False Positives:** A developer renaming an internal variable or reformatting whitespace triggers extensive git diff changes despite zero semantic modification.
2. **False Negatives & Catastrophic Regressions:** An engineer or autonomous code synthesis agent removing a mutex lock (`with self.mu:` or `l.mu.Lock()`), relaxing concurrency from `exclusive_lock` to `lock_free`, or altering a precondition (e.g. changing `amount > 0` to `amount > 50` or `amount >= 0`) appears as a minor textual edit, yet constitutes an irreversible architectural break or security defect.
3. **Contract Weakening vs. Strengthening:** Determining whether a modified precondition preserves backward compatibility requires verifying logical entailment:
   $$P_{\text{old}} \implies P_{\text{new}}$$
   Line diffs cannot evaluate predicate logic over integer and state spaces.

## Decision
We implement a deterministic **Canonical Semantic Delta Engine** ($\Delta \mathcal{S}$) in `unity/compiler/delta.py` combined with automated theorem proving via **Z3 SMT Solver** (`z3-solver`):

1. **UAST-Level Diffing ($\mathcal{S}_{\text{post}} \ominus \mathcal{S}_{\text{pre}}$):**
   - Diffing operates strictly over the 3-Layer Universal Abstract Syntax Tree (`UnityModule`).
   - Structural additions, deletions, contract mutations, concurrency shifts, and purity transitions are isolated into structured `SymbolDelta` objects.

2. **Categorization of One-Way Doors:**
   - **Critical One-Way Doors:** Any patch that drops an exclusive lock, shifts function purity from `pure` to `impure`, deletes a declared precondition, or violates an invariant is flagged as a `ONE_WAY_DOOR`.
   - In the dual-plane Software Factory architecture, One-Way Doors halt autonomous execution and trigger mandatory Socratic deliberation.

3. **SMT Invariant Implication Verification:**
   - For all precondition and contract mutations, the engine formulates the logical validity query in Z3:
     $$\text{Valid}(P_{\text{old}} \implies P_{\text{new}}) \quad \iff \quad \text{UNSAT}(\neg (P_{\text{old}} \implies P_{\text{new}}))$$
   - If Z3 returns `UNSAT`, the contract modification is proven to be an invariant-preserving relaxation.
   - If Z3 returns `SAT`, the solver extracts the concrete counterexample (e.g., `amount = 1`), definitively proving an invariant violation and halting deployment.

## Consequences

### Positive
- Mathematical certainty of invariant preservation across polyglot implementations (Python and Go).
- Elimination of hallucinated, tautological agent unit tests in favor of SMT-grounded semantic audits.
- Direct integration with Software Factory governance (`factory audit`).

### Negative / Trade-offs
- Expressions must be parsed into first-order arithmetic predicates for SMT solving; unmodeled higher-order predicates fall back to syntax equivalence audits.
