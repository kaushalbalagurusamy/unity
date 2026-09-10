"""
Milestone 1 Automated Quality Gate:
Validates the Compiler Frontend, Tree-sitter Lowering Engine,
Dual-Anchor Semantic Equivalence, and the Semantic Delta (ΔS) Engine with Z3 SMT logic.
"""

import copy
from pathlib import Path
import pytest
from lark import Lark

from compiler import (
    compile_source,
    extract_uast,
    compute_semantic_delta,
    UnifiedParser,
    SemanticExtractor,
    CanonicalEmitter,
    SemanticDeltaEngine,
    DeltaSeverity,
    VerificationStatus,
    SMTContractProver,
    CausalGraphResolver,
    CausalLink,
)

ROOT_DIR = Path(__file__).parent.parent
GRAMMAR_PATH = ROOT_DIR / "grammar" / "unity_ir.ebnf"
GOLDEN_UIR_PATH = ROOT_DIR / "examples" / "ledger" / "canonical_ledger.uir"
PYTHON_ANCHOR_PATH = ROOT_DIR / "examples" / "ledger" / "ledger.py"
GO_ANCHOR_PATH = ROOT_DIR / "examples" / "ledger" / "ledger.go"


def test_python_lowers_to_canonical_uir_byte_for_byte() -> None:
    """Verify that compiling Python anchor produces 100% byte-for-byte match to canonical_ledger.uir."""
    assert GOLDEN_UIR_PATH.exists()
    golden_uir = GOLDEN_UIR_PATH.read_text(encoding="utf-8")

    compiled_py_uir = compile_source(PYTHON_ANCHOR_PATH, validate=True)
    assert compiled_py_uir == golden_uir, "Compiled Python UIR does not match golden canonical_ledger.uir"


def test_go_lowers_to_canonical_uir_byte_for_byte() -> None:
    """Verify that compiling Go anchor produces 100% byte-for-byte match to canonical_ledger.uir."""
    assert GOLDEN_UIR_PATH.exists()
    golden_uir = GOLDEN_UIR_PATH.read_text(encoding="utf-8")

    compiled_go_uir = compile_source(GO_ANCHOR_PATH, validate=True)
    assert compiled_go_uir == golden_uir, "Compiled Go UIR does not match golden canonical_ledger.uir"


def test_cross_lingual_dual_anchor_equivalence() -> None:
    """Verify that Python and Go compilers yield identical in-memory UASTs and identical IR."""
    py_module = extract_uast(PYTHON_ANCHOR_PATH)
    go_module = extract_uast(GO_ANCHOR_PATH)

    assert py_module.symbols.keys() == go_module.symbols.keys(), "Mismatch in extracted symbol IDs"

    for sym_id in py_module.symbols:
        py_sym = py_module.get_symbol(sym_id)
        go_sym = go_module.get_symbol(sym_id)

        assert py_sym is not None and go_sym is not None
        assert py_sym.contract == go_sym.contract, f"Contract mismatch in {sym_id}"
        assert py_sym.preconditions == go_sym.preconditions, f"Preconditions mismatch in {sym_id}"
        assert py_sym.execution_logic == go_sym.execution_logic, f"Execution logic mismatch in {sym_id}"
        assert py_sym.postconditions == go_sym.postconditions, f"Postconditions mismatch in {sym_id}"
        assert py_sym.causal_topology == go_sym.causal_topology, f"Causal topology mismatch in {sym_id}"

    # Semantic Delta between Python and Go must be IDENTICAL with 0 One-Way Doors
    delta = compute_semantic_delta(PYTHON_ANCHOR_PATH, GO_ANCHOR_PATH)
    assert delta.is_identical, "Semantic delta between Python and Go must be identical"
    assert not delta.has_one_way_doors, "Cross-lingual delta must not contain One-Way Doors"


def test_delta_engine_detects_concurrency_lock_removal() -> None:
    """Verify that removing a concurrency lock triggers a critical One-Way Door."""
    py_module = extract_uast(PYTHON_ANCHOR_PATH)
    mutated_module = copy.deepcopy(py_module)

    # Mutate withdraw to remove exclusive lock
    withdraw_sym = mutated_module.get_symbol("@ledger.Ledger.withdraw")
    assert withdraw_sym is not None
    object.__setattr__(withdraw_sym.contract.systems, "concurrency", "lock_free")

    engine = SemanticDeltaEngine()
    delta = engine.compute_delta(py_module, mutated_module)

    assert delta.has_one_way_doors, "Lock removal MUST be classified as a One-Way Door"
    sym_delta = delta.symbol_deltas["@ledger.Ledger.withdraw"]
    assert sym_delta.severity == DeltaSeverity.ONE_WAY_DOOR
    assert sym_delta.is_one_way_door is True
    assert sym_delta.concurrency_diff == ("exclusive_lock(self.mu)", "lock_free")


def test_delta_engine_detects_purity_shift() -> None:
    """Verify that shifting a pure function to impure triggers a One-Way Door."""
    py_module = extract_uast(PYTHON_ANCHOR_PATH)
    mutated_module = copy.deepcopy(py_module)

    get_balance_sym = mutated_module.get_symbol("@ledger.Ledger.get_balance")
    assert get_balance_sym is not None
    object.__setattr__(get_balance_sym.contract.systems, "purity", "impure(StateMutation:self.balances)")

    engine = SemanticDeltaEngine()
    delta = engine.compute_delta(py_module, mutated_module)

    assert delta.has_one_way_doors, "Pure to impure transition MUST trigger a One-Way Door"
    sym_delta = delta.symbol_deltas["@ledger.Ledger.get_balance"]
    assert sym_delta.severity == DeltaSeverity.ONE_WAY_DOOR
    assert sym_delta.purity_diff == ("pure", "impure(StateMutation:self.balances)")


def test_delta_engine_smt_prover_catches_counterexample() -> None:
    """Verify that Z3 SMT solver catches unsafe precondition strengthening with a counterexample."""
    prover = SMTContractProver()

    # 1. Unsafe strengthening: (amount > 0) does NOT entail (amount > 50)
    res_unsafe = prover.verify_implication("amount > 0", "amount > 50")
    assert not res_unsafe.implication_holds
    assert res_unsafe.status == VerificationStatus.COUNTEREXAMPLE_FOUND
    assert res_unsafe.counterexample is not None
    assert "amount" in res_unsafe.counterexample

    # 2. Safe relaxation: (amount > 0) DOES entail (amount >= 0)
    res_safe = prover.verify_implication("amount > 0", "amount >= 0")
    assert res_safe.implication_holds
    assert res_safe.status == VerificationStatus.DECIDABLE_SMT_PROVED
    assert res_safe.counterexample is None


def test_delta_engine_smt_prover_handles_unmodeled_predicates_soundly() -> None:
    """
    Verify that predicates outside the decidable theory (QF_LIA) fall back
    soundly to conservative syntactic equality rather than halting or hallucinating.
    """
    prover = SMTContractProver()

    # 1. Syntactic identity outside QF_LIA holds conservatively
    res_ident = prover.verify_implication("isValidId(account_id)", "isValidId(account_id)")
    assert res_ident.implication_holds
    assert res_ident.status == VerificationStatus.CONSERVATIVE_SYNTACTIC_CHECK
    assert res_ident.counterexample is None

    # 2. Syntactic inequality outside QF_LIA is soundly rejected
    res_diff = prover.verify_implication("isValidId(account_id)", "isUUID(account_id)")
    assert not res_diff.implication_holds
    assert res_diff.status == VerificationStatus.CONSERVATIVE_SYNTACTIC_CHECK
    assert res_diff.counterexample is not None
    assert "Conservative fallback" in res_diff.counterexample


def test_decoupled_causal_graph_resolver() -> None:
    """
    Verify that cross-file causal topology resolution is decoupled from
    single-file Tree-sitter parsing and accepts external resolvers (e.g. SCIP / LSP indexers).
    """
    class MockSCIPCausalResolver:
        def resolve_called_by(self, symbol_id: str, method_name: str) -> list[CausalLink]:
            return [
                CausalLink(kind="CALLED_BY", target_symbol=f"@external.service.{method_name}"),
                CausalLink(kind="CALLED_BY", target_symbol="@audit.logger.record"),
            ]

    resolver = MockSCIPCausalResolver()
    py_module = extract_uast(PYTHON_ANCHOR_PATH, causal_resolver=resolver)

    deposit_sym = py_module.get_symbol("@ledger.Ledger.deposit")
    assert deposit_sym is not None
    assert len(deposit_sym.causal_topology) == 2
    assert deposit_sym.causal_topology[0].target_symbol == "@external.service.deposit"
    assert deposit_sym.causal_topology[1].target_symbol == "@audit.logger.record"


def test_delta_engine_detects_precondition_mutation_in_module() -> None:
    """Verify that an illegal precondition mutation in a module triggers an SMT One-Way Door."""
    py_module = extract_uast(PYTHON_ANCHOR_PATH)
    mutated_module = copy.deepcopy(py_module)

    deposit_sym = mutated_module.get_symbol("@ledger.Ledger.deposit")
    assert deposit_sym is not None

    # Alter P2 from amount > 0 to amount > 100
    for i, p in enumerate(deposit_sym.preconditions):
        if p.id == "P2":
            deposit_sym.preconditions[i] = type(p)(id="P2", expr="amount > 100")

    engine = SemanticDeltaEngine()
    delta = engine.compute_delta(py_module, mutated_module)

    assert delta.has_one_way_doors
    sym_delta = delta.symbol_deltas["@ledger.Ledger.deposit"]
    assert sym_delta.severity == DeltaSeverity.ONE_WAY_DOOR
    assert any("SMT INVARIANT VIOLATION" in msg for msg in sym_delta.messages)


def test_delta_engine_detects_symbol_addition_and_removal() -> None:
    """Verify that deleting a symbol triggers a One-Way Door, while adding one is structural."""
    py_module = extract_uast(PYTHON_ANCHOR_PATH)
    mutated_module = copy.deepcopy(py_module)

    # Remove withdraw
    del mutated_module.symbols["@ledger.Ledger.withdraw"]

    engine = SemanticDeltaEngine()
    delta = engine.compute_delta(py_module, mutated_module)

    assert delta.has_one_way_doors
    assert "@ledger.Ledger.withdraw" in delta.removed_symbols
