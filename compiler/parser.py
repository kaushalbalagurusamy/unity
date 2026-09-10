"""
Tree-sitter Concrete Syntax Tree (CST) Traversal Engine for Project Unity.
Provides unified parsing and node inspection across Python and Go source files.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
import tree_sitter
from tree_sitter import Language, Node, Parser, Tree
import tree_sitter_python
import tree_sitter_go


class SourceLanguage(str, Enum):
    PYTHON = "python"
    GO = "go"


@dataclass(frozen=True)
class ParsedSource:
    """Encapsulates a parsed source file and its Tree-sitter CST."""
    language: SourceLanguage
    source_bytes: bytes
    tree: Tree
    filepath: Optional[Path] = None

    @property
    def root_node(self) -> Node:
        return self.tree.root_node

    def get_text(self, node: Node) -> str:
        """Extract decoded utf-8 text for any CST node."""
        return self.source_bytes[node.start_byte : node.end_byte].decode("utf-8")


class UnifiedParser:
    """
    Thread-safe parser wrapper that compiles Python and Go code into Tree-sitter CSTs.
    """

    def __init__(self) -> None:
        self._py_language = Language(tree_sitter_python.language())
        self._go_language = Language(tree_sitter_go.language())

        self._py_parser = Parser(self._py_language)
        self._go_parser = Parser(self._go_language)

    def parse_file(self, filepath: Union[str, Path]) -> ParsedSource:
        """Parse source code from a file, automatically detecting language from extension."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Source file does not exist: {path}")

        source_bytes = path.read_bytes()
        ext = path.suffix.lower()

        if ext == ".py":
            lang = SourceLanguage.PYTHON
            tree = self._py_parser.parse(source_bytes)
        elif ext == ".go":
            lang = SourceLanguage.GO
            tree = self._go_parser.parse(source_bytes)
        else:
            raise ValueError(f"Unsupported file extension: {ext} (expected .py or .go)")

        if tree.root_node.has_error:
            raise SyntaxError(f"Syntax error encountered while parsing {path}")

        return ParsedSource(
            language=lang,
            source_bytes=source_bytes,
            tree=tree,
            filepath=path,
        )

    def parse_string(self, code: str, language: SourceLanguage) -> ParsedSource:
        """Parse source code from an in-memory string."""
        source_bytes = code.encode("utf-8")
        if language == SourceLanguage.PYTHON:
            tree = self._py_parser.parse(source_bytes)
        elif language == SourceLanguage.GO:
            tree = self._go_parser.parse(source_bytes)
        else:
            raise ValueError(f"Unsupported language: {language}")

        if tree.root_node.has_error:
            raise SyntaxError("Syntax error encountered while parsing code snippet")

        return ParsedSource(
            language=language,
            source_bytes=source_bytes,
            tree=tree,
        )

    # -------------------------------------------------------------------------
    # CST Query & Traversal Utilities (CS61B Tree Traversal)
    # -------------------------------------------------------------------------

    @staticmethod
    def find_children_by_type(node: Node, type_name: str) -> List[Node]:
        """Find all immediate child nodes matching a specific type."""
        return [child for child in node.children if child.type == type_name]

    @staticmethod
    def find_all_descendants_by_type(node: Node, type_name: str) -> List[Node]:
        """Find all recursive descendant nodes matching a specific type (DFS traversal)."""
        results: List[Node] = []

        def _dfs(current: Node) -> None:
            if current.type == type_name:
                results.append(current)
            for child in current.children:
                _dfs(child)

        _dfs(node)
        return results

    @staticmethod
    def find_child_by_field(node: Node, field_name: str) -> Optional[Node]:
        """Retrieve a specific named field child from a CST node."""
        return node.child_by_field_name(field_name)
