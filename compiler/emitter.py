"""
Canonical Unity-IR Serializer and Emitter.
Serializes in-memory UAST (UnityModule) into formal .uir text adhering to grammar/unity_ir.ebnf.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from lark import Lark

from .schema import (
    UnityModule,
    SymbolDeclaration,
    Contract,
    ExecutionStep,
)


class CanonicalEmitter:
    """
    Serializes UnityModule or SymbolDeclaration dataclasses into canonical .uir text.
    Validates output against the formal EBNF grammar using Lark.
    """

    def __init__(self, grammar_path: Optional[Path] = None) -> None:
        if grammar_path is None:
            grammar_path = Path(__file__).parent.parent / "grammar" / "unity_ir.ebnf"
        self.grammar_path = grammar_path
        self._lark_parser: Optional[Lark] = None

    def _get_lark(self) -> Lark:
        if self._lark_parser is None:
            if not self.grammar_path.exists():
                raise FileNotFoundError(f"Unity-IR EBNF grammar not found at {self.grammar_path}")
            grammar_text = self.grammar_path.read_text(encoding="utf-8")
            self._lark_parser = Lark(grammar_text, start="start", parser="earley")
        return self._lark_parser

    def emit_symbol(self, symbol: SymbolDeclaration) -> str:
        """Serialize a single SymbolDeclaration into canonical text."""
        lines: List[str] = []

        # Header
        lines.append(f"SYMBOL: {symbol.symbol_id}")

        # Contract Block
        lines.append("CONTRACT:")
        params_str = ", ".join([f"{p.name}: {p.type_spec}" for p in symbol.contract.params])
        lines.append(f"  PARAMS: ({params_str})")
        lines.append(f"  RETURNS: {symbol.contract.returns}")
        sys = symbol.contract.systems
        sys_attrs = [f"concurrency: {sys.concurrency}", f"purity: {sys.purity}"]
        if sys.resource:
            sys_attrs.append(f"resource: {sys.resource}")
        lines.append(f"  SYSTEMS: [{', '.join(sys_attrs)}]")

        # Preconditions Block
        if symbol.preconditions:
            lines.append("")
            lines.append("PRECONDITIONS:")
            for p in symbol.preconditions:
                lines.append(f"  {p.id}: {p.expr}")

        # Execution Logic Block
        if symbol.execution_logic:
            lines.append("")
            lines.append("EXECUTION_LOGIC:")
            for step in symbol.execution_logic:
                lines.append(f"  {step.step_num}. {step.action}")
                if step.assert_expr and step.assert_throw:
                    lines.append(f"     ASSERT: {step.assert_expr} ELSE THROW {step.assert_throw}")

        # Postconditions Block
        if symbol.postconditions:
            lines.append("")
            lines.append("POSTCONDITIONS:")
            for q in symbol.postconditions:
                lines.append(f"  {q.id}: {q.expr}")

        # Causal Topology Block
        if symbol.causal_topology:
            lines.append("")
            lines.append("CAUSAL_TOPOLOGY:")
            for link in symbol.causal_topology:
                lines.append(f"  {link.kind}: {link.target_symbol}")

        return "\n".join(lines)

    def emit_module(self, module: UnityModule, validate: bool = True) -> str:
        """
        Serialize an entire UnityModule into canonical .uir text.
        Optionally validates the text against Lark grammar.
        """
        blocks = [self.emit_symbol(sym) for sym in module.symbols.values()]
        text = "\n\n\n".join(blocks) + "\n"

        if validate:
            self.validate_uir(text)

        return text

    def validate_uir(self, uir_text: str) -> bool:
        """Validate UIR text against the formal EBNF grammar."""
        lark = self._get_lark()
        try:
            lark.parse(uir_text)
            return True
        except Exception as e:
            raise ValueError(f"Emitted Unity-IR failed EBNF grammar validation:\n{e}")
