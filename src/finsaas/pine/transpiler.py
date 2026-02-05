"""Pine Script AST to Python Strategy transpiler.

Converts a Pine Script AST into a Python Strategy subclass
that can be used with the FinSaaS backtest engine.
"""

from __future__ import annotations

from finsaas.pine.ast_nodes import (
    Assignment,
    BinaryOp,
    BoolLiteral,
    Comparison,
    ForLoop,
    FunctionCall,
    Identifier,
    IfStatement,
    IndexAccess,
    InputDecl,
    LogicalOp,
    MethodCall,
    NaLiteral,
    NumberLiteral,
    PineNode,
    PlotCall,
    Script,
    StrategyDecl,
    StringLiteral,
    TernaryExpr,
    UnaryOp,
    VarDecl,
)


class PineTranspiler:
    """Transpile Pine Script AST to Python Strategy code."""

    def __init__(self) -> None:
        self._indent = 0
        self._var_inits: list[str] = []
        self._on_bar_lines: list[str] = []
        self._params: list[InputDecl] = []
        self._strategy_name = "PineStrategy"
        self._class_params: list[str] = []

    def transpile(self, script: Script) -> str:
        """Transpile a Script AST to Python source code."""
        self._var_inits = []
        self._on_bar_lines = []
        self._params = []
        self._class_params = []

        # Extract strategy name
        if isinstance(script.indicator_or_strategy, StrategyDecl):
            title = script.indicator_or_strategy.title
            if title:
                self._strategy_name = self._to_class_name(title)

        # Collect inputs/parameters
        for decl in script.declarations:
            if isinstance(decl, InputDecl):
                self._params.append(decl)
                self._class_params.append(self._transpile_input_param(decl))
            elif isinstance(decl, VarDecl):
                if decl.is_var:
                    self._var_inits.append(self._transpile_var_init(decl))
                else:
                    self._on_bar_lines.append(self._transpile_node(decl))

        # Process body
        for stmt in script.body:
            line = self._transpile_node(stmt)
            if line:
                self._on_bar_lines.append(line)

        return self._generate_python()

    def _generate_python(self) -> str:
        """Generate the complete Python module."""
        lines: list[str] = []
        lines.append('"""Auto-generated from Pine Script."""')
        lines.append("")
        lines.append("from decimal import Decimal")
        lines.append("")
        lines.append("from finsaas.core.types import Side")
        lines.append("from finsaas.strategy.base import Strategy")
        lines.append("from finsaas.strategy.parameters import IntParam, FloatParam, BoolParam")
        lines.append("")
        lines.append("")
        lines.append(f"class {self._strategy_name}(Strategy):")

        # Class-level parameters
        if self._class_params:
            for param in self._class_params:
                lines.append(f"    {param}")
            lines.append("")

        # on_init
        lines.append("    def on_init(self):")
        if self._var_inits:
            for init in self._var_inits:
                lines.append(f"        {init}")
        else:
            lines.append("        pass")
        lines.append("")

        # on_bar
        lines.append("    def on_bar(self, ctx):")
        if self._on_bar_lines:
            for line in self._on_bar_lines:
                for sub_line in line.split("\n"):
                    lines.append(f"        {sub_line}")
        else:
            lines.append("        pass")

        lines.append("")
        return "\n".join(lines)

    def _transpile_node(self, node: PineNode) -> str:
        """Transpile a single AST node to Python code."""
        if isinstance(node, VarDecl):
            value = self._transpile_node(node.value) if node.value else "None"
            return f"{node.name} = {value}"

        if isinstance(node, Assignment):
            value = self._transpile_node(node.value) if node.value else "None"
            return f"{node.target} = {value}"

        if isinstance(node, MethodCall):
            return self._transpile_method_call(node)

        if isinstance(node, FunctionCall):
            return self._transpile_function_call(node)

        if isinstance(node, IfStatement):
            return self._transpile_if(node)

        if isinstance(node, ForLoop):
            return self._transpile_for(node)

        if isinstance(node, BinaryOp):
            left = self._transpile_node(node.left) if node.left else "0"
            right = self._transpile_node(node.right) if node.right else "0"
            return f"({left} {node.op} {right})"

        if isinstance(node, UnaryOp):
            operand = self._transpile_node(node.operand) if node.operand else "0"
            if node.op == "not":
                return f"(not {operand})"
            return f"({node.op}{operand})"

        if isinstance(node, Comparison):
            left = self._transpile_node(node.left) if node.left else "0"
            right = self._transpile_node(node.right) if node.right else "0"
            return f"({left} {node.op} {right})"

        if isinstance(node, LogicalOp):
            left = self._transpile_node(node.left) if node.left else "False"
            right = self._transpile_node(node.right) if node.right else "False"
            return f"({left} {node.op} {right})"

        if isinstance(node, TernaryExpr):
            cond = self._transpile_node(node.condition) if node.condition else "False"
            then = self._transpile_node(node.then_expr) if node.then_expr else "None"
            else_ = self._transpile_node(node.else_expr) if node.else_expr else "None"
            return f"({then} if {cond} else {else_})"

        if isinstance(node, IndexAccess):
            series = self._transpile_node(node.series) if node.series else "None"
            index = self._transpile_node(node.index) if node.index else "0"
            return f"{series}[{index}]"

        if isinstance(node, NumberLiteral):
            return f"Decimal('{node.value}')"

        if isinstance(node, StringLiteral):
            return f'"{node.value}"'

        if isinstance(node, BoolLiteral):
            return "True" if node.value else "False"

        if isinstance(node, NaLiteral):
            return "None"

        if isinstance(node, Identifier):
            return self._map_identifier(node.name)

        return str(node)

    def _transpile_method_call(self, node: MethodCall) -> str:
        """Transpile a method/namespace call."""
        obj = node.object_name
        method = node.method
        args = [self._transpile_node(a) for a in node.args]
        args_str = ", ".join(args)

        # Map Pine Script namespaces to Python
        if obj == "ta":
            return f"self.ta.{method}({args_str})"
        elif obj == "strategy":
            # Handle constants like strategy.long, strategy.short
            if method == "long" and not args:
                return "Side.LONG"
            elif method == "short" and not args:
                return "Side.SHORT"
            return self._transpile_strategy_call(method, args, node)
        elif obj == "math":
            return f"self.math.{method}({args_str})"
        elif obj == "input":
            return f"input_{method}({args_str})"
        else:
            # Might be a variable's method
            mapped_obj = self._map_identifier(obj)
            if args:
                return f"{mapped_obj}.{method}({args_str})"
            return f"{mapped_obj}.{method}"

    def _transpile_strategy_call(
        self, method: str, args: list[str], node: MethodCall
    ) -> str:
        """Map strategy.* calls to Python."""
        if method == "entry":
            # strategy.entry(id, direction, qty, ...)
            tag = args[0] if args else '"default"'
            direction = args[1] if len(args) > 1 else "Side.LONG"
            # Map strategy.long/strategy.short
            direction = direction.replace("strategy.long", "Side.LONG")
            direction = direction.replace("strategy.short", "Side.SHORT")
            extra = ""
            if len(args) > 2:
                extra = f", qty={args[2]}"
            return f"self.entry({tag}, {direction}{extra})"
        elif method == "exit":
            tag = args[0] if args else '"default"'
            from_entry = args[1] if len(args) > 1 else tag
            return f"self.exit({tag}, from_entry={from_entry})"
        elif method == "close":
            tag = args[0] if args else '"default"'
            return f"self.close_position({tag})"
        elif method == "close_all":
            return "self.close_all()"
        return f"# strategy.{method}({', '.join(args)})"

    def _transpile_function_call(self, node: FunctionCall) -> str:
        """Transpile a function call."""
        args = [self._transpile_node(a) for a in node.args]
        args_str = ", ".join(args)

        # Map known functions
        func = node.name
        if func == "nz":
            return f"nz({args_str})"
        elif func == "na":
            return f"na({args_str})"
        elif func == "plot":
            return f"# plot({args_str})"
        elif func == "plotshape":
            return f"# plotshape({args_str})"
        elif func == "alertcondition":
            return f"# alertcondition({args_str})"
        elif func == "alert":
            return f"# alert({args_str})"
        elif func == "bgcolor":
            return f"# bgcolor({args_str})"

        return f"{func}({args_str})"

    def _transpile_if(self, node: IfStatement) -> str:
        """Transpile an if statement."""
        lines: list[str] = []
        cond = self._transpile_node(node.condition) if node.condition else "False"
        lines.append(f"if {cond}:")
        for stmt in node.then_body:
            lines.append(f"    {self._transpile_node(stmt)}")
        if not node.then_body:
            lines.append("    pass")

        for elif_cond, elif_body in node.elif_clauses:
            cond = self._transpile_node(elif_cond)
            lines.append(f"elif {cond}:")
            for stmt in elif_body:
                lines.append(f"    {self._transpile_node(stmt)}")
            if not elif_body:
                lines.append("    pass")

        if node.else_body:
            lines.append("else:")
            for stmt in node.else_body:
                lines.append(f"    {self._transpile_node(stmt)}")

        return "\n".join(lines)

    def _transpile_for(self, node: ForLoop) -> str:
        """Transpile a for loop."""
        start = self._transpile_node(node.start) if node.start else "0"
        end = self._transpile_node(node.end) if node.end else "0"
        step = self._transpile_node(node.step) if node.step else "1"
        lines = [f"for {node.var_name} in range({start}, {end}, {step}):"]
        for stmt in node.body:
            lines.append(f"    {self._transpile_node(stmt)}")
        if not node.body:
            lines.append("    pass")
        return "\n".join(lines)

    def _transpile_input_param(self, decl: InputDecl) -> str:
        """Transpile an input declaration to a parameter descriptor."""
        if decl.input_type == "int":
            parts = [f"IntParam(default={decl.default_value or 0}"]
            if decl.min_val is not None:
                parts.append(f"min_val={decl.min_val}")
            if decl.max_val is not None:
                parts.append(f"max_val={decl.max_val}")
            if decl.step is not None:
                parts.append(f"step={decl.step}")
            return f'{decl.name} = {", ".join(parts)})'
        elif decl.input_type == "float":
            return (
                f'{decl.name} = FloatParam(default={decl.default_value or 0.0})'
            )
        elif decl.input_type == "bool":
            val = str(decl.default_value or "false").lower() == "true"
            return f'{decl.name} = BoolParam(default={val})'
        else:
            return f'{decl.name} = IntParam(default={decl.default_value or 0})'

    def _transpile_var_init(self, decl: VarDecl) -> str:
        """Transpile a var declaration to on_init() code."""
        return f"self.{decl.name} = self.create_series(name='{decl.name}')"

    def _map_identifier(self, name: str) -> str:
        """Map Pine Script identifiers to Python equivalents."""
        mapping = {
            "close": "self.close",
            "open": "self.open",
            "high": "self.high",
            "low": "self.low",
            "volume": "self.volume",
            "bar_index": "self.bar_index",
            "strategy.long": "Side.LONG",
            "strategy.short": "Side.SHORT",
        }
        if name in mapping:
            return mapping[name]
        # Check if it's a declared input parameter
        param_names = {p.name for p in self._params}
        if name in param_names:
            return f"self.{name}"
        return name

    def _to_class_name(self, title: str) -> str:
        """Convert a title string to a valid Python class name."""
        words = title.replace("-", " ").replace("_", " ").split()
        return "".join(w.capitalize() for w in words) or "PineStrategy"
