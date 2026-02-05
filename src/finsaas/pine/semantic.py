"""Semantic analysis for Pine Script AST.

Performs type checking, scope resolution, and validation.
"""

from __future__ import annotations

from finsaas.core.errors import PineSemanticError
from finsaas.pine.ast_nodes import (
    Assignment,
    BinaryOp,
    Comparison,
    FunctionCall,
    Identifier,
    IfStatement,
    InputDecl,
    MethodCall,
    PineNode,
    Script,
    VarDecl,
)

# Known Pine Script built-in functions and namespaces
BUILTIN_FUNCTIONS = {
    "ta.sma", "ta.ema", "ta.rsi", "ta.macd", "ta.crossover", "ta.crossunder",
    "ta.highest", "ta.lowest", "ta.atr", "ta.bb", "ta.change", "ta.stdev",
    "ta.rma", "ta.tr",
    "math.abs", "math.max", "math.min", "math.round", "math.ceil",
    "math.floor", "math.sign", "math.pow", "math.sqrt", "math.log", "math.exp",
    "strategy.entry", "strategy.exit", "strategy.close", "strategy.close_all",
    "strategy.cancel", "strategy.cancel_all",
    "plot", "plotshape", "plotchar", "bgcolor", "barcolor",
    "input", "input.int", "input.float", "input.bool", "input.string", "input.source",
    "alert", "alertcondition",
    "nz", "na", "fixnan",
    "str.tostring", "str.format",
    "array.new_float", "array.push", "array.get", "array.size",
    "syminfo.tickerid", "syminfo.currency",
    "timeframe.period", "timeframe.multiplier",
}

BUILTIN_VARIABLES = {
    "open", "high", "low", "close", "volume", "time",
    "bar_index", "barstate.isconfirmed", "barstate.islast",
    "strategy.long", "strategy.short",
    "strategy.position_size", "strategy.equity",
    "na", "true", "false",
    "color.red", "color.green", "color.blue", "color.white",
    "color.black", "color.orange", "color.purple",
}


class SemanticAnalyzer:
    """Analyze Pine Script AST for semantic correctness."""

    def __init__(self) -> None:
        self._scope: dict[str, str] = {}  # name -> type
        self._errors: list[str] = []

    def analyze(self, script: Script) -> list[str]:
        """Analyze the script and return a list of warnings/errors.

        Raises PineSemanticError for critical issues.
        """
        self._scope = {}
        self._errors = []

        # Register built-in variables
        for name in BUILTIN_VARIABLES:
            self._scope[name] = "builtin"

        # Process declarations
        for decl in script.declarations:
            self._analyze_node(decl)

        # Process body
        for stmt in script.body:
            self._analyze_node(stmt)

        if self._errors:
            raise PineSemanticError(
                f"Semantic errors found:\n" + "\n".join(f"  - {e}" for e in self._errors)
            )

        return self._errors

    def _analyze_node(self, node: PineNode) -> None:
        """Recursively analyze an AST node."""
        if isinstance(node, VarDecl):
            self._scope[node.name] = "var"
            if node.value:
                self._analyze_node(node.value)

        elif isinstance(node, InputDecl):
            self._scope[node.name] = node.input_type

        elif isinstance(node, Assignment):
            if not node.is_reassignment and node.target not in self._scope:
                self._scope[node.target] = "var"
            elif node.is_reassignment and node.target not in self._scope:
                self._errors.append(
                    f"Reassignment to undeclared variable: {node.target}"
                )
            if node.value:
                self._analyze_node(node.value)

        elif isinstance(node, Identifier):
            if node.name not in self._scope and node.name not in BUILTIN_VARIABLES:
                # Could be a namespace prefix, skip
                if "." not in node.name:
                    pass  # Warn but don't error - could be defined later

        elif isinstance(node, FunctionCall):
            if node.name not in self._scope:
                # Check if it's a builtin
                if node.name not in BUILTIN_FUNCTIONS:
                    pass  # Custom functions OK
            for arg in node.args:
                self._analyze_node(arg)

        elif isinstance(node, MethodCall):
            full_name = f"{node.object_name}.{node.method}"
            for arg in node.args:
                self._analyze_node(arg)

        elif isinstance(node, BinaryOp):
            if node.left:
                self._analyze_node(node.left)
            if node.right:
                self._analyze_node(node.right)

        elif isinstance(node, Comparison):
            if node.left:
                self._analyze_node(node.left)
            if node.right:
                self._analyze_node(node.right)

        elif isinstance(node, IfStatement):
            if node.condition:
                self._analyze_node(node.condition)
            for stmt in node.then_body:
                self._analyze_node(stmt)
            for cond, body in node.elif_clauses:
                self._analyze_node(cond)
                for stmt in body:
                    self._analyze_node(stmt)
            for stmt in node.else_body:
                self._analyze_node(stmt)
