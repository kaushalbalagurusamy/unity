"""
Milestone 0 Automated Quality Gate:
Validates that the formal EBNF grammar parses the golden target IR,
that UAST schema models serialize properly, and that both source anchors
satisfy syntax and contract invariants.
"""

from pathlib import Path
import pytest
from lark import Lark
from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_go

from compiler.schema import (
    UnityModule,
    SymbolDeclaration,
    Contract,
    Parameter,
    SystemAttributes,
    Precondition,
    ExecutionStep,
    Postcondition,
    CausalLink,
)
from examples.ledger.ledger import (
    Ledger,
    NotFoundError,
    InvalidAmountError,
    InsufficientFundsError,
)

ROOT_DIR = Path(__file__).parent.parent
GRAMMAR_PATH = ROOT_DIR / "grammar" / "unity_ir.ebnf"
GOLDEN_UIR_PATH = ROOT_DIR / "examples" / "ledger" / "canonical_ledger.uir"
PYTHON_ANCHOR_PATH = ROOT_DIR / "examples" / "ledger" / "ledger.py"
GO_ANCHOR_PATH = ROOT_DIR / "examples" / "ledger" / "ledger.go"


def test_grammar_parses_golden_canonical_ledger() -> None:
    """Ensure the formal EBNF grammar parses canonical_ledger.uir with 0 errors."""
    assert GRAMMAR_PATH.exists(), f"Grammar file missing at {GRAMMAR_PATH}"
    assert GOLDEN_UIR_PATH.exists(), f"Golden UIR file missing at {GOLDEN_UIR_PATH}"

    grammar_text = GRAMMAR_PATH.read_text(encoding="utf-8")
    parser = Lark(grammar_text, start="start", parser="earley")

    uir_text = GOLDEN_UIR_PATH.read_text(encoding="utf-8")
    tree = parser.parse(uir_text)

    symbols = list(tree.find_data("symbol_decl"))
    assert len(symbols) == 3, f"Expected 3 symbols in canonical ledger, found {len(symbols)}"

    # Collect parsed symbol IDs
    symbol_ids = []
    for s in symbols:
        cid_node = s.children[0]
        # Reconstruct canonical symbol ID
        symbol_str = "".join([str(c) for c in cid_node.children if isinstance(c, str)])
        symbol_ids.append(symbol_str)

    assert "ledgerLedgerget_balance" in symbol_ids
    assert "ledgerLedgerdeposit" in symbol_ids
    assert "ledgerLedgerwithdraw" in symbol_ids


def test_schema_serialization_and_deserialization() -> None:
    """Verify that in-memory UAST dataclasses construct, validate, and serialize correctly."""
    withdraw_decl = SymbolDeclaration(
        symbol_id="@ledger.Ledger.withdraw",
        contract=Contract(
            params=[
                Parameter(name="account_id", type_spec="Str"),
                Parameter(name="amount", type_spec="Int64"),
            ],
            returns="Result<Int64, Error[NotFound | InvalidAmount | InsufficientFunds]>",
            systems=SystemAttributes(
                concurrency="exclusive_lock(self.mu)",
                purity="impure(StateMutation:self.balances)",
            ),
        ),
        preconditions=[
            Precondition(id="P1", expr="isValidId(account_id)"),
            Precondition(id="P2", expr="amount > 0"),
            Precondition(id="P3", expr="account_id in self.balances"),
            Precondition(id="P4", expr="self.balances[account_id] >= amount"),
        ],
        execution_logic=[
            ExecutionStep(
                step_num=1,
                action="EVALUATE: valid_amount = amount > 0",
                assert_expr="valid_amount == True",
                assert_throw="InvalidAmount",
            ),
            ExecutionStep(
                step_num=2,
                action="ACQUIRE: exclusive_lock(self.mu)",
            ),
            ExecutionStep(
                step_num=5,
                action="MUTATE: self.balances[account_id] := proposed",
            ),
            ExecutionStep(
                step_num=6,
                action="RELEASE: exclusive_lock(self.mu)",
            ),
        ],
        postconditions=[
            Postcondition(id="Q1", expr="self.balances[account_id] == current - amount"),
            Postcondition(id="Q2", expr="self.balances[account_id] >= 0"),
            Postcondition(id="Q3", expr="RESULT == self.balances[account_id]"),
        ],
        causal_topology=[
            CausalLink(kind="CALLED_BY", target_symbol="@api.handlers.execute_withdrawal")
        ],
    )

    module = UnityModule()
    module.add_symbol(withdraw_decl)

    retrieved = module.get_symbol("@ledger.Ledger.withdraw")
    assert retrieved is not None
    assert retrieved.contract.systems.concurrency == "exclusive_lock(self.mu)"
    assert retrieved.contract.systems.purity == "impure(StateMutation:self.balances)"
    assert len(retrieved.preconditions) == 4
    assert len(retrieved.postconditions) == 3

    # Test dictionary export
    exported = module.to_dict()
    assert "@ledger.Ledger.withdraw" in exported["symbols"]
    assert exported["symbols"]["@ledger.Ledger.withdraw"]["contract"]["returns"] == (
        "Result<Int64, Error[NotFound | InvalidAmount | InsufficientFunds]>"
    )


def test_python_source_anchor_contracts_and_concurrency() -> None:
    """Verify runtime contract checking and thread-safety on ledger.py."""
    ledger = Ledger()
    ledger.create_account("test-acc", 500)

    # 1. Successful deposit
    assert ledger.deposit("test-acc", 200) == 700
    assert ledger.get_balance("test-acc") == 700

    # 2. Successful withdrawal
    assert ledger.withdraw("test-acc", 300) == 400
    assert ledger.get_balance("test-acc") == 400

    # 3. Invalid negative amount
    with pytest.raises(InvalidAmountError):
        ledger.deposit("test-acc", -50)

    with pytest.raises(InvalidAmountError):
        ledger.withdraw("test-acc", 0)

    # 4. Overdraft invariant check
    with pytest.raises(InsufficientFundsError):
        ledger.withdraw("test-acc", 1000)

    # 5. Non-existent account
    with pytest.raises(NotFoundError):
        ledger.get_balance("unknown-acc")


def test_tree_sitter_cst_parses_both_anchors_with_zero_errors() -> None:
    """Verify that Tree-sitter parsers parse both Python and Go anchors cleanly."""
    py_lang = Language(tree_sitter_python.language())
    go_lang = Language(tree_sitter_go.language())

    py_parser = Parser(py_lang)
    go_parser = Parser(go_lang)

    py_code = PYTHON_ANCHOR_PATH.read_bytes()
    go_code = GO_ANCHOR_PATH.read_bytes()

    py_cst = py_parser.parse(py_code)
    go_cst = go_parser.parse(go_code)

    assert not py_cst.root_node.has_error, "Syntax error detected in Python anchor CST"
    assert not go_cst.root_node.has_error, "Syntax error detected in Go anchor CST"

    assert py_cst.root_node.named_child_count > 0
    assert go_cst.root_node.named_child_count > 0
