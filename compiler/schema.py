"""
Formal Typed Data Schema for Unity Intermediate Representation (Unity-IR).
Defines the in-memory Universal Abstract Syntax Tree (UAST) across all 3 layers.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class Parameter:
    """Represents a typed function parameter in Layer 1."""
    name: str
    type_spec: str


@dataclass(frozen=True)
class SystemAttributes:
    """Represents systems-level semantics in Layer 1."""
    concurrency: str  # e.g. exclusive_lock(self.mu), lock_free, atomic
    purity: str       # e.g. pure, impure(IO), impure(StateMutation:target)
    resource: Optional[str] = None  # e.g. owned, mutable_borrow(T), shared_borrow(T)


@dataclass(frozen=True)
class Contract:
    """Represents the complete Layer 1 systems contract for a symbol."""
    params: List[Parameter]
    returns: str
    systems: SystemAttributes


@dataclass(frozen=True)
class Precondition:
    """Represents a first-order logic precondition in Layer 2."""
    id: str   # e.g. P1, P2
    expr: str


@dataclass(frozen=True)
class ExecutionStep:
    """Represents an execution logic or state transition step in Layer 2."""
    step_num: int
    action: str
    assert_expr: Optional[str] = None
    assert_throw: Optional[str] = None


@dataclass(frozen=True)
class Postcondition:
    """Represents a first-order logic postcondition in Layer 2."""
    id: str   # e.g. Q1, Q2
    expr: str


@dataclass(frozen=True)
class CausalLink:
    """Represents a causal dependency edge in Layer 3."""
    kind: str           # CALLS or CALLED_BY
    target_symbol: str  # e.g. @api.handlers.execute_withdrawal


@dataclass
class SymbolDeclaration:
    """Represents a full 3-Layer Unity-IR symbol declaration."""
    symbol_id: str
    contract: Contract
    preconditions: List[Precondition] = field(default_factory=list)
    execution_logic: List[ExecutionStep] = field(default_factory=list)
    postconditions: List[Postcondition] = field(default_factory=list)
    causal_topology: List[CausalLink] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize symbol declaration to dictionary format."""
        return {
            "symbol_id": self.symbol_id,
            "contract": {
                "params": [{"name": p.name, "type_spec": p.type_spec} for p in self.contract.params],
                "returns": self.contract.returns,
                "systems": {
                    "concurrency": self.contract.systems.concurrency,
                    "purity": self.contract.systems.purity,
                    "resource": self.contract.systems.resource,
                },
            },
            "preconditions": [{"id": p.id, "expr": p.expr} for p in self.preconditions],
            "execution_logic": [
                {
                    "step_num": s.step_num,
                    "action": s.action,
                    "assert_expr": s.assert_expr,
                    "assert_throw": s.assert_throw,
                }
                for s in self.execution_logic
            ],
            "postconditions": [{"id": q.id, "expr": q.expr} for q in self.postconditions],
            "causal_topology": [
                {"kind": c.kind, "target_symbol": c.target_symbol} for c in self.causal_topology
            ],
        }


@dataclass
class UnityModule:
    """Represents a collection of symbols comprising a compiled repository module."""
    symbols: Dict[str, SymbolDeclaration] = field(default_factory=dict)

    def get_symbol(self, symbol_id: str) -> Optional[SymbolDeclaration]:
        return self.symbols.get(symbol_id)

    def add_symbol(self, decl: SymbolDeclaration) -> None:
        self.symbols[decl.symbol_id] = decl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbols": {k: v.to_dict() for k, v in self.symbols.items()}
        }
