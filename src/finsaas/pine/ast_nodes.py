"""AST node definitions for Pine Script parse trees."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PineNode:
    """Base AST node."""

    line: int = 0
    col: int = 0


@dataclass
class Script(PineNode):
    """Root node - entire Pine Script."""

    version: int = 5
    indicator_or_strategy: IndicatorDecl | StrategyDecl | None = None
    declarations: list[PineNode] = field(default_factory=list)
    body: list[PineNode] = field(default_factory=list)

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}Script(v{self.version})"]
        if self.indicator_or_strategy:
            lines.append(f"{pad}  {self.indicator_or_strategy}")
        for d in self.declarations:
            lines.append(f"{pad}  {d}")
        for s in self.body:
            lines.append(f"{pad}  {s}")
        return "\n".join(lines)


@dataclass
class IndicatorDecl(PineNode):
    """indicator() declaration."""

    title: str = ""
    shorttitle: str = ""
    overlay: bool = False


@dataclass
class StrategyDecl(PineNode):
    """strategy() declaration."""

    title: str = ""
    shorttitle: str = ""
    overlay: bool = False
    initial_capital: float = 10000
    default_qty_type: str = "strategy.percent_of_equity"
    default_qty_value: float = 100
    commission_type: str = "strategy.commission.percent"
    commission_value: float = 0.1


@dataclass
class VarDecl(PineNode):
    """Variable declaration: var x = expr or x = expr."""

    name: str = ""
    type_hint: str | None = None
    value: PineNode | None = None
    is_var: bool = False  # Pine's 'var' keyword (persists across bars)
    is_input: bool = False


@dataclass
class InputDecl(PineNode):
    """input.*() declaration."""

    name: str = ""
    input_type: str = "int"  # int, float, bool, string, source
    default_value: Any = None
    title: str = ""
    min_val: Any = None
    max_val: Any = None
    step: Any = None
    options: list[Any] = field(default_factory=list)


@dataclass
class Assignment(PineNode):
    """Assignment: x = expr or x := expr."""

    target: str = ""
    value: PineNode | None = None
    is_reassignment: bool = False


@dataclass
class BinaryOp(PineNode):
    """Binary operation: left op right."""

    op: str = ""
    left: PineNode | None = None
    right: PineNode | None = None


@dataclass
class UnaryOp(PineNode):
    """Unary operation: op expr."""

    op: str = ""
    operand: PineNode | None = None


@dataclass
class Comparison(PineNode):
    """Comparison: left op right."""

    op: str = ""
    left: PineNode | None = None
    right: PineNode | None = None


@dataclass
class LogicalOp(PineNode):
    """Logical operation: and, or, not."""

    op: str = ""
    left: PineNode | None = None
    right: PineNode | None = None


@dataclass
class FunctionCall(PineNode):
    """Function call: func(args...)."""

    name: str = ""
    args: list[PineNode] = field(default_factory=list)
    kwargs: dict[str, PineNode] = field(default_factory=dict)


@dataclass
class MethodCall(PineNode):
    """Method call: obj.method(args...)."""

    object_name: str = ""
    method: str = ""
    args: list[PineNode] = field(default_factory=list)
    kwargs: dict[str, PineNode] = field(default_factory=dict)


@dataclass
class IndexAccess(PineNode):
    """Series index access: series[offset]."""

    series: PineNode | None = None
    index: PineNode | None = None


@dataclass
class IfStatement(PineNode):
    """if/else if/else statement."""

    condition: PineNode | None = None
    then_body: list[PineNode] = field(default_factory=list)
    elif_clauses: list[tuple[PineNode, list[PineNode]]] = field(default_factory=list)
    else_body: list[PineNode] = field(default_factory=list)


@dataclass
class ForLoop(PineNode):
    """for loop: for i = start to end [by step]."""

    var_name: str = ""
    start: PineNode | None = None
    end: PineNode | None = None
    step: PineNode | None = None
    body: list[PineNode] = field(default_factory=list)


@dataclass
class WhileLoop(PineNode):
    """while loop."""

    condition: PineNode | None = None
    body: list[PineNode] = field(default_factory=list)


@dataclass
class FunctionDef(PineNode):
    """Function definition."""

    name: str = ""
    params: list[str] = field(default_factory=list)
    body: list[PineNode] = field(default_factory=list)
    return_expr: PineNode | None = None


@dataclass
class TernaryExpr(PineNode):
    """Ternary expression: cond ? then : else."""

    condition: PineNode | None = None
    then_expr: PineNode | None = None
    else_expr: PineNode | None = None


@dataclass
class NumberLiteral(PineNode):
    """Numeric literal."""

    value: str = "0"
    is_float: bool = False


@dataclass
class StringLiteral(PineNode):
    """String literal."""

    value: str = ""


@dataclass
class BoolLiteral(PineNode):
    """Boolean literal."""

    value: bool = False


@dataclass
class NaLiteral(PineNode):
    """na literal."""

    pass


@dataclass
class Identifier(PineNode):
    """Variable or function reference."""

    name: str = ""


@dataclass
class ColorLiteral(PineNode):
    """Color literal: #RRGGBB or color.red etc."""

    value: str = ""


@dataclass
class PlotCall(PineNode):
    """plot() call."""

    series: PineNode | None = None
    title: str = ""
    color: PineNode | None = None
    linewidth: int = 1
