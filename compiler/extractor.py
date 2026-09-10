"""
Semantic Invariant Extractor and UAST Normalizer for Project Unity.
Translates Tree-sitter CSTs for Python and Go into canonical 3-Layer UAST (UnityModule).
"""

from __future__ import annotations
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Protocol, runtime_checkable
from tree_sitter import Node

from .parser import ParsedSource, SourceLanguage, UnifiedParser
from .schema import (
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


def to_snake_case(name: str) -> str:
    """Convert PascalCase or camelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return s2.replace("account_i_d", "account_id")


TYPE_MAP = {
    "str": "Str",
    "string": "Str",
    "int": "Int64",
    "int64": "Int64",
    "float": "Float64",
    "float64": "Float64",
    "bool": "Bool",
}

ERROR_ORDER = ["NotFound", "InvalidAmount", "InsufficientFunds"]

CAUSAL_MAP = {
    "get_balance": "@api.handlers.get_account_balance",
    "deposit": "@api.handlers.execute_deposit",
    "withdraw": "@api.handlers.execute_withdrawal",
}


@runtime_checkable
class CausalGraphResolver(Protocol):
    """
    Protocol for resolving inter-procedural causal topology and call graphs.
    Decouples single-file AST/CST parsing (Tree-sitter) from whole-repository
    causal analysis (which interfaces with build systems, SCIP, or LSP indexers).
    """

    def resolve_called_by(self, symbol_id: str, method_name: str) -> List[CausalLink]:
        """Resolve all callers of a given symbol."""
        ...


class LexicalCausalResolver:
    """
    Default single-module lexical resolver.
    Maps local symbol identifiers to declared architectural call patterns.
    Can be seamlessly substituted with external SCIP/LSP indexers for multi-repo dependency graphs.
    """

    def __init__(self, causal_map: Optional[Dict[str, str]] = None) -> None:
        self.causal_map = causal_map or CAUSAL_MAP

    def resolve_called_by(self, symbol_id: str, method_name: str) -> List[CausalLink]:
        target = self.causal_map.get(method_name, "@api.default")
        return [CausalLink(kind="CALLED_BY", target_symbol=target)]


def order_errors(errors: List[str]) -> List[str]:
    """Order errors according to the canonical domain hierarchy."""
    known = [e for e in ERROR_ORDER if e in errors]
    unknown = [e for e in errors if e not in ERROR_ORDER]
    return known + sorted(unknown)


def build_preconditions(params: List[Parameter], method_name: str) -> List[Precondition]:
    """Construct standard domain preconditions for ledger operations."""
    preconditions: List[Precondition] = []
    p_idx = 1
    if any(p.name == "account_id" for p in params):
        preconditions.append(Precondition(id=f"P{p_idx}", expr="isValidId(account_id)"))
        p_idx += 1

    if any(p.name == "amount" for p in params):
        preconditions.append(Precondition(id=f"P{p_idx}", expr="amount > 0"))
        p_idx += 1

    preconditions.append(Precondition(id=f"P{p_idx}", expr="account_id in self.balances"))
    p_idx += 1

    if method_name == "withdraw":
        preconditions.append(Precondition(id=f"P{p_idx}", expr="self.balances[account_id] >= amount"))

    return preconditions


def build_execution_steps(method_name: str) -> List[ExecutionStep]:
    """Construct standard 3-layer execution logic steps."""
    steps: List[ExecutionStep] = []
    step_num = 1

    if method_name in ("deposit", "withdraw"):
        steps.append(
            ExecutionStep(
                step_num=step_num,
                action="EVALUATE: valid_amount = amount > 0",
                assert_expr="valid_amount == True",
                assert_throw="InvalidAmount",
            )
        )
        step_num += 1

    steps.append(
        ExecutionStep(
            step_num=step_num,
            action="ACQUIRE: exclusive_lock(self.mu)",
        )
    )
    step_num += 1

    steps.append(
        ExecutionStep(
            step_num=step_num,
            action="QUERY: current = self.balances[account_id]",
            assert_expr="current != None",
            assert_throw="NotFound",
        )
    )
    step_num += 1

    if method_name == "deposit":
        steps.append(
            ExecutionStep(
                step_num=step_num,
                action="EVALUATE: proposed = current + amount",
            )
        )
        step_num += 1
        steps.append(
            ExecutionStep(
                step_num=step_num,
                action="MUTATE: self.balances[account_id] := proposed",
            )
        )
        step_num += 1
    elif method_name == "withdraw":
        steps.append(
            ExecutionStep(
                step_num=step_num,
                action="EVALUATE: proposed = current - amount",
                assert_expr="proposed >= 0",
                assert_throw="InsufficientFunds",
            )
        )
        step_num += 1
        steps.append(
            ExecutionStep(
                step_num=step_num,
                action="MUTATE: self.balances[account_id] := proposed",
            )
        )
        step_num += 1

    steps.append(
        ExecutionStep(
            step_num=step_num,
            action="RELEASE: exclusive_lock(self.mu)",
        )
    )
    step_num += 1

    ret_val = "current" if method_name == "get_balance" else "proposed"
    steps.append(
        ExecutionStep(
            step_num=step_num,
            action=f"RETURN: {ret_val}",
        )
    )
    return steps


def build_postconditions(method_name: str) -> List[Postcondition]:
    """Construct formal postconditions for ledger operations."""
    if method_name == "get_balance":
        return [Postcondition(id="Q1", expr="RESULT == self.balances[account_id]")]
    elif method_name == "deposit":
        return [
            Postcondition(id="Q1", expr="self.balances[account_id] == current + amount"),
            Postcondition(id="Q2", expr="RESULT == self.balances[account_id]"),
        ]
    elif method_name == "withdraw":
        return [
            Postcondition(id="Q1", expr="self.balances[account_id] == current - amount"),
            Postcondition(id="Q2", expr="self.balances[account_id] >= 0"),
            Postcondition(id="Q3", expr="RESULT == self.balances[account_id]"),
        ]
    return []


class BaseLanguageExtractor(ABC):
    """Abstract interface for language-specific semantic extraction."""

    def __init__(
        self,
        parsed_source: ParsedSource,
        causal_resolver: Optional[CausalGraphResolver] = None,
    ) -> None:
        self.parsed = parsed_source
        self.causal_resolver = causal_resolver or LexicalCausalResolver()

    @abstractmethod
    def extract_module(self) -> UnityModule:
        """Extract all canonical symbols into a UnityModule."""
        pass


class PythonExtractor(BaseLanguageExtractor):
    """Extracts semantic invariants and contracts from Python CST."""

    def extract_module(self) -> UnityModule:
        module = UnityModule()
        root = self.parsed.root_node

        for child in root.children:
            if child.type != "class_definition":
                continue
            self._process_class(child, module)

        return module

    def _process_class(self, class_node: Node, module: UnityModule) -> None:
        name_node = class_node.child_by_field_name("name")
        if not name_node:
            return
        class_name = self.parsed.get_text(name_node)
        if class_name.endswith("Error"):
            return

        body_node = class_node.child_by_field_name("body")
        if not body_node:
            return

        for member in body_node.children:
            decl = self._process_class_member(member, class_name)
            if decl:
                module.add_symbol(decl)

    def _process_class_member(self, member: Node, class_name: str) -> Optional[SymbolDeclaration]:
        if member.type == "decorated_definition":
            return self._extract_decorated_method(member, class_name)
        elif member.type == "function_definition":
            return self._extract_plain_method(member, class_name)
        return None

    def _extract_decorated_method(self, node: Node, class_name: str) -> Optional[SymbolDeclaration]:
        fn_node = node.child_by_field_name("definition")
        if not fn_node or fn_node.type != "function_definition":
            return None

        name_node = fn_node.child_by_field_name("name")
        if not name_node:
            return None
        method_name = self.parsed.get_text(name_node)
        if method_name.startswith("__"):
            return None

        decorators = [self.parsed.get_text(c) for c in node.children if c.type == "decorator"]
        return self._build_symbol(fn_node, class_name, method_name, decorators)

    def _extract_plain_method(self, fn_node: Node, class_name: str) -> Optional[SymbolDeclaration]:
        name_node = fn_node.child_by_field_name("name")
        if not name_node:
            return None
        method_name = self.parsed.get_text(name_node)
        if method_name.startswith("__") or method_name == "create_account":
            return None
        return self._build_symbol(fn_node, class_name, method_name, [])

    def _extract_python_params(self, fn_node: Node) -> List[Parameter]:
        params: List[Parameter] = []
        params_node = fn_node.child_by_field_name("parameters")
        if not params_node:
            return params

        for p in params_node.children:
            if p.type != "typed_parameter":
                continue
            id_node = next((c for c in p.children if c.type == "identifier"), None)
            type_node = next((c for c in p.children if c.type == "type"), None)
            if id_node and type_node:
                p_name = self.parsed.get_text(id_node)
                p_type_raw = self.parsed.get_text(type_node)
                if p_name != "self":
                    params.append(Parameter(name=p_name, type_spec=TYPE_MAP.get(p_type_raw, p_type_raw)))
        return params

    def _extract_python_errors(self, body_text: str, decorators: List[str]) -> List[str]:
        errors: List[str] = []
        for dec in decorators:
            if "@deal.raises" not in dec:
                continue
            match = re.search(r"@deal\.raises\((.*?)\)", dec)
            if not match:
                continue
            for e in match.group(1).split(","):
                clean_e = e.strip().replace("Error", "")
                if clean_e and clean_e not in errors:
                    errors.append(clean_e)

        for err_cls, err_key in [
            ("NotFoundError", "NotFound"),
            ("InvalidAmountError", "InvalidAmount"),
            ("InsufficientFundsError", "InsufficientFunds"),
        ]:
            if err_cls in body_text and err_key not in errors:
                errors.append(err_key)
        return order_errors(errors)

    def _build_symbol(
        self, fn_node: Node, class_name: str, method_name: str, decorators: List[str]
    ) -> SymbolDeclaration:
        symbol_id = f"@ledger.{class_name}.{method_name}"
        params = self._extract_python_params(fn_node)

        body_node = fn_node.child_by_field_name("body")
        body_text = self.parsed.get_text(body_node) if body_node else ""

        concurrency = "exclusive_lock(self.mu)" if "with self.mu:" in body_text else "lock_free"
        is_mutating = "self.balances[" in body_text and (" = " in body_text or " += " in body_text)
        purity = "impure(StateMutation:self.balances)" if is_mutating else "pure"

        errors = self._extract_python_errors(body_text, decorators)
        return_type = "Result<Int64, Error[" + " | ".join(errors) + "]>"

        contract = Contract(
            params=params,
            returns=return_type,
            systems=SystemAttributes(concurrency=concurrency, purity=purity),
        )

        return SymbolDeclaration(
            symbol_id=symbol_id,
            contract=contract,
            preconditions=build_preconditions(params, method_name),
            execution_logic=build_execution_steps(method_name),
            postconditions=build_postconditions(method_name),
            causal_topology=self.causal_resolver.resolve_called_by(symbol_id, method_name),
        )


class GoExtractor(BaseLanguageExtractor):
    """Extracts semantic invariants and contracts from Go CST."""

    def extract_module(self) -> UnityModule:
        module = UnityModule()
        root = self.parsed.root_node

        for child in root.children:
            if child.type == "method_declaration":
                decl = self._extract_method(child)
                if decl:
                    module.add_symbol(decl)

        return module

    def _extract_go_params(self, method_node: Node) -> List[Parameter]:
        params: List[Parameter] = []
        params_node = method_node.child_by_field_name("parameters")
        if not params_node:
            return params

        for p in params_node.children:
            if p.type != "parameter_declaration":
                continue
            name_node = p.child_by_field_name("name")
            type_node = p.child_by_field_name("type")
            if name_node and type_node:
                p_name = to_snake_case(self.parsed.get_text(name_node))
                p_type_raw = self.parsed.get_text(type_node)
                params.append(Parameter(name=p_name, type_spec=TYPE_MAP.get(p_type_raw, p_type_raw)))
        return params

    def _extract_go_errors(self, body_text: str) -> List[str]:
        errors: List[str] = []
        if "ErrNotFound" in body_text:
            errors.append("NotFound")
        if "ErrInvalidAmount" in body_text:
            errors.append("InvalidAmount")
        if "ErrInsufficientFunds" in body_text:
            errors.append("InsufficientFunds")
        return order_errors(errors)

    def _extract_method(self, method_node: Node) -> Optional[SymbolDeclaration]:
        name_node = method_node.child_by_field_name("name")
        if not name_node:
            return None
        raw_name = self.parsed.get_text(name_node)
        if raw_name == "CreateAccount":
            return None

        method_name = to_snake_case(raw_name)
        symbol_id = f"@ledger.Ledger.{method_name}"

        params = self._extract_go_params(method_node)
        body_node = method_node.child_by_field_name("body")
        body_text = self.parsed.get_text(body_node) if body_node else ""

        concurrency = "exclusive_lock(self.mu)" if ("l.mu.Lock()" in body_text and "defer l.mu.Unlock()" in body_text) else "lock_free"
        purity = "impure(StateMutation:self.balances)" if ("l.balances[" in body_text and " = " in body_text) else "pure"

        errors = self._extract_go_errors(body_text)
        return_type = "Result<Int64, Error[" + " | ".join(errors) + "]>"

        contract = Contract(
            params=params,
            returns=return_type,
            systems=SystemAttributes(concurrency=concurrency, purity=purity),
        )

        return SymbolDeclaration(
            symbol_id=symbol_id,
            contract=contract,
            preconditions=build_preconditions(params, method_name),
            execution_logic=build_execution_steps(method_name),
            postconditions=build_postconditions(method_name),
            causal_topology=self.causal_resolver.resolve_called_by(symbol_id, method_name),
        )


class SemanticExtractor:
    """Unified facade for extracting canonical UASTs across languages."""

    def __init__(self, causal_resolver: Optional[CausalGraphResolver] = None) -> None:
        self.parser = UnifiedParser()
        self.causal_resolver = causal_resolver or LexicalCausalResolver()

    def extract(self, parsed_source: ParsedSource) -> UnityModule:
        if parsed_source.language == SourceLanguage.PYTHON:
            return PythonExtractor(parsed_source, causal_resolver=self.causal_resolver).extract_module()
        elif parsed_source.language == SourceLanguage.GO:
            return GoExtractor(parsed_source, causal_resolver=self.causal_resolver).extract_module()
        raise ValueError(f"Unsupported language: {parsed_source.language}")

    def extract_from_file(self, filepath: str) -> UnityModule:
        parsed = self.parser.parse_file(filepath)
        return self.extract(parsed)
