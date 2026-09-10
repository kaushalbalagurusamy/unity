"""
Semantic Delta (ΔS) Engine for Project Unity.
Computes structural semantic differences between two UAST modules (S_post ⊖ S_pre).
Integrates Z3 SMT automated theorem proving for mathematical contract implication verification.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple
import z3

from .schema import (
    UnityModule,
    SymbolDeclaration,
    Contract,
    Precondition,
    Postcondition,
    ExecutionStep,
)


class DeltaSeverity(str, Enum):
    ONE_WAY_DOOR = "ONE_WAY_DOOR"          # Irreversible architectural or synchronization violation
    CONTRACT_SHIFT = "CONTRACT_SHIFT"      # Signatures, parameters, or return types altered
    BEHAVIORAL_MUTATION = "BEHAVIORAL"     # Execution logic steps modified
    STRUCTURAL_CHANGE = "STRUCTURAL"       # Symbol added or removed
    IDENTICAL = "IDENTICAL"                # No semantic change


@dataclass
class PreconditionSMTResult:
    """Outcome of SMT formal verification between two contract predicates."""
    old_expr: str
    new_expr: str
    implication_holds: bool
    counterexample: Optional[str] = None


@dataclass
class SymbolDelta:
    """Captures granular semantic diffs for a single symbol."""
    symbol_id: str
    severity: DeltaSeverity = DeltaSeverity.IDENTICAL
    is_one_way_door: bool = False
    concurrency_diff: Optional[Tuple[str, str]] = None
    purity_diff: Optional[Tuple[str, str]] = None
    contract_diff: Optional[Tuple[str, str]] = None
    precondition_diffs: List[PreconditionSMTResult] = field(default_factory=list)
    postcondition_diffs: List[Tuple[str, str]] = field(default_factory=list)
    execution_step_diffs: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)


@dataclass
class SemanticDelta:
    """Represents the complete semantic delta across all symbols in a repository module."""
    symbol_deltas: Dict[str, SymbolDelta] = field(default_factory=dict)
    added_symbols: List[str] = field(default_factory=list)
    removed_symbols: List[str] = field(default_factory=list)

    @property
    def has_one_way_doors(self) -> bool:
        """Indicates whether any critical One-Way Door architectural regressions were detected."""
        return any(d.is_one_way_door for d in self.symbol_deltas.values()) or len(self.removed_symbols) > 0

    @property
    def is_identical(self) -> bool:
        """Indicates whether both modules are semantically identical."""
        return (
            not self.added_symbols
            and not self.removed_symbols
            and all(d.severity == DeltaSeverity.IDENTICAL for d in self.symbol_deltas.values())
        )

    def summary(self) -> str:
        """Generate human-readable audit summary of semantic differences."""
        lines: List[str] = []
        lines.append("=" * 60)
        lines.append("SEMANTIC DELTA AUDIT (ΔS)")
        lines.append(f"One-Way Doors Detected: {self.has_one_way_doors}")
        lines.append("=" * 60)

        if self.added_symbols:
            lines.append(f"\n[+] Added Symbols ({len(self.added_symbols)}):")
            for s in self.added_symbols:
                lines.append(f"  + {s}")

        if self.removed_symbols:
            lines.append(f"\n[-] Removed Symbols ({len(self.removed_symbols)}) [ONE-WAY DOOR]:")
            for s in self.removed_symbols:
                lines.append(f"  - {s}")

        for sym_id, delta in self.symbol_deltas.items():
            if delta.severity == DeltaSeverity.IDENTICAL:
                continue

            door_tag = " [CRITICAL ONE-WAY DOOR]" if delta.is_one_way_door else ""
            lines.append(f"\n[*] Symbol: {sym_id} -> {delta.severity.value}{door_tag}")
            for msg in delta.messages:
                lines.append(f"    • {msg}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


class SMTContractProver:
    """
    Formal SMT Logic Engine utilizing Z3 to check logical entailment:
    P_old => P_new  (proving invariant preservation or counterexample discovery)
    """

    def parse_simple_predicate(self, expr: str, vars_map: Dict[str, z3.ArithRef]) -> Optional[z3.BoolRef]:
        """Convert simple arithmetic/logical expression into a Z3 boolean expression."""
        expr = expr.strip()

        # Handle simple comparisons: var op int
        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*(>=|<=|>|<|==|!=)\s*(-?\d+)$", expr)
        if match:
            var_name, op, val_str = match.groups()
            var = vars_map.setdefault(var_name, z3.Int(var_name))
            val = int(val_str)
            return self._build_cmp(var, op, val)

        # Handle self.balances[account_id] >= amount
        match_idx = re.match(r"^self\.balances\[account_id\]\s*(>=|<=|>|<|==|!=)\s*([a-zA-Z_][a-zA-Z0-9_]*)$", expr)
        if match_idx:
            op, var_name = match_idx.groups()
            bal_var = vars_map.setdefault("balances_acc", z3.Int("balances_acc"))
            amt_var = vars_map.setdefault(var_name, z3.Int(var_name))
            return self._build_cmp(bal_var, op, amt_var)

        return None

    @staticmethod
    def _build_cmp(left: Any, op: str, right: Any) -> Optional[z3.BoolRef]:
        cmp_map = {
            ">": lambda l, r: l > r,
            ">=": lambda l, r: l >= r,
            "<": lambda l, r: l < r,
            "<=": lambda l, r: l <= r,
            "==": lambda l, r: l == r,
            "!=": lambda l, r: l != r,
        }
        fn = cmp_map.get(op)
        return fn(left, right) if fn else None

    def verify_implication(self, old_expr: str, new_expr: str) -> PreconditionSMTResult:
        """
        Verify if old_expr => new_expr holds for all inputs using Z3 SMT solver.
        If it does not hold, extracts the concrete counterexample.
        """
        vars_map: Dict[str, z3.ArithRef] = {}
        z3_old = self.parse_simple_predicate(old_expr, vars_map)
        z3_new = self.parse_simple_predicate(new_expr, vars_map)

        if z3_old is None or z3_new is None:
            is_equal = old_expr.strip() == new_expr.strip()
            return PreconditionSMTResult(
                old_expr=old_expr,
                new_expr=new_expr,
                implication_holds=is_equal,
                counterexample=None if is_equal else "Syntax inequality (unmodeled predicate)",
            )

        solver = z3.Solver()
        solver.add(z3.Not(z3.Implies(z3_old, z3_new)))

        if solver.check() == z3.unsat:
            return PreconditionSMTResult(
                old_expr=old_expr,
                new_expr=new_expr,
                implication_holds=True,
                counterexample=None,
            )

        model = solver.model()
        cex_str = ", ".join([f"{d}={model[d]}" for d in model.decls()])
        return PreconditionSMTResult(
            old_expr=old_expr,
            new_expr=new_expr,
            implication_holds=False,
            counterexample=cex_str or "Counterexample found",
        )


class SemanticDeltaEngine:
    """
    Computes semantic delta ΔS = S_post ⊖ S_pre between two UnityModules.
    """

    def __init__(self) -> None:
        self.prover = SMTContractProver()

    def compute_delta(self, pre_module: UnityModule, post_module: UnityModule) -> SemanticDelta:
        delta = SemanticDelta()
        pre_keys = set(pre_module.symbols.keys())
        post_keys = set(post_module.symbols.keys())

        delta.added_symbols = sorted(list(post_keys - pre_keys))
        delta.removed_symbols = sorted(list(pre_keys - post_keys))

        for sym_id in sorted(list(pre_keys & post_keys)):
            sym_pre = pre_module.symbols[sym_id]
            sym_post = post_module.symbols[sym_id]
            delta.symbol_deltas[sym_id] = self._diff_symbol(sym_pre, sym_post)

        return delta

    def _diff_symbol(self, pre: SymbolDeclaration, post: SymbolDeclaration) -> SymbolDelta:
        delta = SymbolDelta(symbol_id=pre.symbol_id)
        self._diff_concurrency(pre, post, delta)
        self._diff_purity(pre, post, delta)
        self._diff_contract(pre, post, delta)
        self._diff_preconditions(pre, post, delta)
        self._diff_execution_steps(pre, post, delta)
        return delta

    def _diff_concurrency(self, pre: SymbolDeclaration, post: SymbolDeclaration, delta: SymbolDelta) -> None:
        if pre.contract.systems.concurrency != post.contract.systems.concurrency:
            delta.concurrency_diff = (pre.contract.systems.concurrency, post.contract.systems.concurrency)
            delta.is_one_way_door = True
            delta.severity = DeltaSeverity.ONE_WAY_DOOR
            delta.messages.append(
                f"CONCURRENCY MUTATION: {pre.contract.systems.concurrency} -> {post.contract.systems.concurrency}"
            )

    def _diff_purity(self, pre: SymbolDeclaration, post: SymbolDeclaration, delta: SymbolDelta) -> None:
        if pre.contract.systems.purity == post.contract.systems.purity:
            return

        delta.purity_diff = (pre.contract.systems.purity, post.contract.systems.purity)
        delta.messages.append(
            f"PURITY SHIFT: {pre.contract.systems.purity} -> {post.contract.systems.purity}"
        )
        if pre.contract.systems.purity == "pure" and "impure" in post.contract.systems.purity:
            delta.is_one_way_door = True
            delta.severity = DeltaSeverity.ONE_WAY_DOOR
        elif delta.severity != DeltaSeverity.ONE_WAY_DOOR:
            delta.severity = DeltaSeverity.CONTRACT_SHIFT

    def _diff_contract(self, pre: SymbolDeclaration, post: SymbolDeclaration, delta: SymbolDelta) -> None:
        if pre.contract.params != post.contract.params or pre.contract.returns != post.contract.returns:
            delta.contract_diff = (str(pre.contract), str(post.contract))
            delta.messages.append(
                f"SIGNATURE MUTATION: returns {pre.contract.returns} -> {post.contract.returns}"
            )
            if delta.severity != DeltaSeverity.ONE_WAY_DOOR:
                delta.severity = DeltaSeverity.CONTRACT_SHIFT

    def _diff_preconditions(self, pre: SymbolDeclaration, post: SymbolDeclaration, delta: SymbolDelta) -> None:
        pre_conds = {p.id: p.expr for p in pre.preconditions}
        post_conds = {p.id: p.expr for p in post.preconditions}

        for pid, old_expr in pre_conds.items():
            if pid not in post_conds:
                delta.is_one_way_door = True
                delta.severity = DeltaSeverity.ONE_WAY_DOOR
                delta.messages.append(f"PRECONDITION REMOVED: {pid}: {old_expr}")
            else:
                self._check_precondition_implication(pid, old_expr, post_conds[pid], delta)

        for pid, new_expr in post_conds.items():
            if pid not in pre_conds:
                delta.messages.append(f"PRECONDITION ADDED: {pid}: {new_expr}")
                if delta.severity == DeltaSeverity.IDENTICAL:
                    delta.severity = DeltaSeverity.CONTRACT_SHIFT

    def _check_precondition_implication(
        self, pid: str, old_expr: str, new_expr: str, delta: SymbolDelta
    ) -> None:
        if old_expr == new_expr:
            return

        smt_res = self.prover.verify_implication(old_expr, new_expr)
        delta.precondition_diffs.append(smt_res)
        if not smt_res.implication_holds:
            delta.is_one_way_door = True
            delta.severity = DeltaSeverity.ONE_WAY_DOOR
            delta.messages.append(
                f"SMT INVARIANT VIOLATION on {pid}: {old_expr} does NOT entail {new_expr}! "
                f"(CEX: {smt_res.counterexample})"
            )
        else:
            delta.messages.append(
                f"Precondition {pid} verified relaxed by SMT: {old_expr} => {new_expr}"
            )
            if delta.severity == DeltaSeverity.IDENTICAL:
                delta.severity = DeltaSeverity.CONTRACT_SHIFT

    def _diff_execution_steps(self, pre: SymbolDeclaration, post: SymbolDeclaration, delta: SymbolDelta) -> None:
        if len(pre.execution_logic) != len(post.execution_logic):
            delta.messages.append(
                f"Execution steps count changed: {len(pre.execution_logic)} -> {len(post.execution_logic)}"
            )
            if delta.severity == DeltaSeverity.IDENTICAL:
                delta.severity = DeltaSeverity.BEHAVIORAL_MUTATION
            return

        for s1, s2 in zip(pre.execution_logic, post.execution_logic):
            if s1 != s2:
                delta.execution_step_diffs.append(f"Step {s1.step_num}: {s1.action} -> {s2.action}")
                if delta.severity == DeltaSeverity.IDENTICAL:
                    delta.severity = DeltaSeverity.BEHAVIORAL_MUTATION
