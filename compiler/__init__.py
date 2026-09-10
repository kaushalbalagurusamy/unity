"""
Unity Compiler Package: Lowers polyglot source code into canonical Unity-IR.
"""

from pathlib import Path
from typing import Optional, Union

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
from .parser import UnifiedParser, ParsedSource, SourceLanguage
from .extractor import (
    SemanticExtractor,
    PythonExtractor,
    GoExtractor,
    CausalGraphResolver,
    LexicalCausalResolver,
)
from .emitter import CanonicalEmitter
from .delta import (
    SemanticDeltaEngine,
    SemanticDelta,
    SymbolDelta,
    DeltaSeverity,
    VerificationStatus,
    PreconditionSMTResult,
    SMTContractProver,
)


def extract_uast(
    path: Union[str, Path],
    causal_resolver: Optional[CausalGraphResolver] = None,
) -> UnityModule:
    """Extract in-memory 3-Layer UAST (UnityModule) from source file."""
    extractor = SemanticExtractor(causal_resolver=causal_resolver)
    return extractor.extract_from_file(str(path))


def compile_source(
    path: Union[str, Path],
    validate: bool = True,
    causal_resolver: Optional[CausalGraphResolver] = None,
) -> str:
    """Compile source file directly into validated canonical Unity-IR string."""
    module = extract_uast(path, causal_resolver=causal_resolver)
    emitter = CanonicalEmitter()
    return emitter.emit_module(module, validate=validate)


def compute_semantic_delta(
    pre_path: Union[str, Path],
    post_path: Union[str, Path],
    causal_resolver: Optional[CausalGraphResolver] = None,
) -> SemanticDelta:
    """Compute structural semantic delta (ΔS) between two source files."""
    pre_mod = extract_uast(pre_path, causal_resolver=causal_resolver)
    post_mod = extract_uast(post_path, causal_resolver=causal_resolver)
    engine = SemanticDeltaEngine()
    return engine.compute_delta(pre_mod, post_mod)


__all__ = [
    "UnityModule",
    "SymbolDeclaration",
    "Contract",
    "Parameter",
    "SystemAttributes",
    "Precondition",
    "ExecutionStep",
    "Postcondition",
    "CausalLink",
    "UnifiedParser",
    "ParsedSource",
    "SourceLanguage",
    "SemanticExtractor",
    "PythonExtractor",
    "GoExtractor",
    "CausalGraphResolver",
    "LexicalCausalResolver",
    "CanonicalEmitter",
    "SemanticDeltaEngine",
    "SemanticDelta",
    "SymbolDelta",
    "DeltaSeverity",
    "VerificationStatus",
    "PreconditionSMTResult",
    "SMTContractProver",
    "extract_uast",
    "compile_source",
    "compute_semantic_delta",
]
