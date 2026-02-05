"""Pine Script parser - text to AST conversion.

Uses a simplified recursive descent approach for Pine Script v5.
The Lark grammar is provided for reference but the parser operates
on a line-by-line tokenized approach for pragmatic handling of
Pine Script's indent-sensitive syntax.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from finsaas.core.errors import PineSyntaxError
from finsaas.pine.ast_nodes import (
    Assignment,
    BinaryOp,
    BoolLiteral,
    Comparison,
    FunctionCall,
    Identifier,
    IfStatement,
    IndexAccess,
    InputDecl,
    LogicalOp,
    MethodCall,
    NaLiteral,
    NumberLiteral,
    Script,
    StrategyDecl,
    StringLiteral,
    TernaryExpr,
    UnaryOp,
    VarDecl,
    PineNode,
    ForLoop,
    PlotCall,
    IndicatorDecl,
)


class PineParser:
    """Parse Pine Script v5 source code into an AST."""

    def parse(self, source: str) -> Script:
        """Parse Pine Script source code into a Script AST node."""
        lines = source.strip().split("\n")
        script = Script()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line or line.startswith("//"):
                i += 1
                continue

            # Version declaration
            if line.startswith("//@version="):
                script.version = int(line.split("=")[1])
                i += 1
                continue

            # Strategy declaration
            if line.startswith("strategy(") or line.startswith("strategy ("):
                script.indicator_or_strategy = self._parse_strategy_decl(line)
                i += 1
                continue

            # Indicator declaration
            if line.startswith("indicator(") or line.startswith("indicator ("):
                script.indicator_or_strategy = self._parse_indicator_decl(line)
                i += 1
                continue

            # Input declaration
            if "= input" in line and ("input.int" in line or "input.float" in line
                                       or "input.bool" in line or "input.string" in line
                                       or "input(" in line or "input.source" in line):
                node = self._parse_input(line)
                script.declarations.append(node)
                i += 1
                continue

            # If statement (collect indented body)
            if line.startswith("if "):
                node, consumed = self._parse_if(lines, i)
                script.body.append(node)
                i += consumed
                continue

            # For loop
            if line.startswith("for "):
                node, consumed = self._parse_for(lines, i)
                script.body.append(node)
                i += consumed
                continue

            # Variable declaration (var keyword)
            if line.startswith("var "):
                node = self._parse_var_decl(line, is_var=True)
                script.declarations.append(node)
                i += 1
                continue

            # Assignment or expression
            if "=" in line and ":=" not in line and not line.startswith("//"):
                parts = line.split("=", 1)
                if parts[0].strip().isidentifier():
                    node = self._parse_var_decl(line, is_var=False)
                    script.body.append(node)
                    i += 1
                    continue

            # Reassignment
            if ":=" in line:
                name, _, expr_str = line.partition(":=")
                node = Assignment(
                    target=name.strip(),
                    value=self._parse_expr(expr_str.strip()),
                    is_reassignment=True,
                )
                script.body.append(node)
                i += 1
                continue

            # Function call or other expression
            node = self._parse_expr(line)
            script.body.append(node)
            i += 1

        return script

    def _parse_strategy_decl(self, line: str) -> StrategyDecl:
        """Parse strategy() declaration."""
        decl = StrategyDecl()
        # Extract arguments from strategy(...)
        inner = self._extract_parens(line, "strategy")
        kwargs = self._parse_kwargs_str(inner)
        decl.title = kwargs.get("title", kwargs.get("0", ""))
        decl.overlay = kwargs.get("overlay", "false").lower() == "true"
        if "initial_capital" in kwargs:
            try:
                decl.initial_capital = float(kwargs["initial_capital"])
            except ValueError:
                pass
        return decl

    def _parse_indicator_decl(self, line: str) -> IndicatorDecl:
        """Parse indicator() declaration."""
        decl = IndicatorDecl()
        inner = self._extract_parens(line, "indicator")
        kwargs = self._parse_kwargs_str(inner)
        decl.title = kwargs.get("title", kwargs.get("0", ""))
        decl.overlay = kwargs.get("overlay", "false").lower() == "true"
        return decl

    def _parse_input(self, line: str) -> InputDecl:
        """Parse input.*() declaration."""
        name, _, rhs = line.partition("=")
        name = name.strip()
        rhs = rhs.strip()

        decl = InputDecl(name=name)

        # Determine input type
        if "input.int" in rhs:
            decl.input_type = "int"
            inner = self._extract_parens(rhs, "input.int")
        elif "input.float" in rhs:
            decl.input_type = "float"
            inner = self._extract_parens(rhs, "input.float")
        elif "input.bool" in rhs:
            decl.input_type = "bool"
            inner = self._extract_parens(rhs, "input.bool")
        elif "input.string" in rhs:
            decl.input_type = "string"
            inner = self._extract_parens(rhs, "input.string")
        elif "input.source" in rhs:
            decl.input_type = "source"
            inner = self._extract_parens(rhs, "input.source")
        else:
            decl.input_type = "int"
            inner = self._extract_parens(rhs, "input")

        kwargs = self._parse_kwargs_str(inner)
        if "defval" in kwargs:
            decl.default_value = kwargs["defval"]
        elif "0" in kwargs:
            decl.default_value = kwargs["0"]
        decl.title = kwargs.get("title", name)
        decl.min_val = kwargs.get("minval")
        decl.max_val = kwargs.get("maxval")
        decl.step = kwargs.get("step")

        return decl

    def _parse_var_decl(self, line: str, is_var: bool) -> VarDecl:
        """Parse a variable declaration."""
        text = line
        if is_var:
            text = text[4:].strip()  # Remove "var "

        name, _, expr_str = text.partition("=")
        name = name.strip()
        return VarDecl(
            name=name,
            value=self._parse_expr(expr_str.strip()),
            is_var=is_var,
        )

    def _parse_if(self, lines: list[str], start: int) -> tuple[IfStatement, int]:
        """Parse an if/else if/else statement."""
        line = lines[start].strip()
        condition_str = line[3:].strip()  # Remove "if "
        node = IfStatement(condition=self._parse_expr(condition_str))

        i = start + 1
        # Collect then body (indented lines)
        then_body, consumed = self._collect_indented_body(lines, i)
        node.then_body = [self._parse_expr(l.strip()) for l in then_body]
        i += consumed

        # Check for else if / else
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("else if "):
                elif_cond = self._parse_expr(line[8:].strip())
                i += 1
                elif_body, consumed = self._collect_indented_body(lines, i)
                node.elif_clauses.append(
                    (elif_cond, [self._parse_expr(l.strip()) for l in elif_body])
                )
                i += consumed
            elif line == "else" or line.startswith("else"):
                i += 1
                else_body, consumed = self._collect_indented_body(lines, i)
                node.else_body = [self._parse_expr(l.strip()) for l in else_body]
                i += consumed
                break
            else:
                break

        return node, i - start

    def _parse_for(self, lines: list[str], start: int) -> tuple[ForLoop, int]:
        """Parse a for loop."""
        line = lines[start].strip()
        # for i = 0 to 10 [by 1]
        match = re.match(
            r"for\s+(\w+)\s*=\s*(.+?)\s+to\s+(.+?)(?:\s+by\s+(.+))?\s*$", line
        )
        if not match:
            raise PineSyntaxError(f"Invalid for loop: {line}")

        node = ForLoop(
            var_name=match.group(1),
            start=self._parse_expr(match.group(2)),
            end=self._parse_expr(match.group(3)),
            step=self._parse_expr(match.group(4)) if match.group(4) else None,
        )

        i = start + 1
        body_lines, consumed = self._collect_indented_body(lines, i)
        node.body = [self._parse_expr(l.strip()) for l in body_lines]
        return node, 1 + consumed

    def _collect_indented_body(
        self, lines: list[str], start: int
    ) -> tuple[list[str], int]:
        """Collect consecutive indented lines."""
        body: list[str] = []
        i = start
        if i >= len(lines):
            return body, 0

        # Determine indentation level from first line
        first_line = lines[i]
        indent = len(first_line) - len(first_line.lstrip())
        if indent == 0:
            return body, 0

        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            line_indent = len(line) - len(line.lstrip())
            if line_indent >= indent:
                body.append(line)
                i += 1
            else:
                break

        return body, i - start

    def _parse_expr(self, text: str) -> PineNode:
        """Parse an expression string into an AST node."""
        text = text.strip()
        if not text:
            return NaLiteral()

        # Ternary
        if " ? " in text and " : " in text:
            q_idx = text.index(" ? ")
            c_idx = text.rindex(" : ")
            return TernaryExpr(
                condition=self._parse_expr(text[:q_idx]),
                then_expr=self._parse_expr(text[q_idx + 3 : c_idx]),
                else_expr=self._parse_expr(text[c_idx + 3 :]),
            )

        # Logical operators
        for op in [" or ", " and "]:
            if op in text:
                parts = text.rsplit(op, 1)
                return LogicalOp(
                    op=op.strip(),
                    left=self._parse_expr(parts[0]),
                    right=self._parse_expr(parts[1]),
                )

        # not
        if text.startswith("not "):
            return UnaryOp(op="not", operand=self._parse_expr(text[4:]))

        # Comparisons
        for op in [">=", "<=", "!=", "==", ">", "<"]:
            if op in text:
                parts = text.split(op, 1)
                if parts[0].strip() and parts[1].strip():
                    return Comparison(
                        op=op,
                        left=self._parse_expr(parts[0]),
                        right=self._parse_expr(parts[1]),
                    )

        # Addition/subtraction (right-to-left scan for correct precedence)
        depth = 0
        for i in range(len(text) - 1, 0, -1):
            if text[i] == ')':
                depth += 1
            elif text[i] == '(':
                depth -= 1
            elif depth == 0 and text[i] in "+-" and text[i - 1] != "(":
                left = text[:i].strip()
                right = text[i + 1:].strip()
                if left and right:
                    return BinaryOp(
                        op=text[i],
                        left=self._parse_expr(left),
                        right=self._parse_expr(right),
                    )

        # Multiplication/division
        depth = 0
        for i in range(len(text) - 1, 0, -1):
            if text[i] == ')':
                depth += 1
            elif text[i] == '(':
                depth -= 1
            elif depth == 0 and text[i] in "*/%":
                left = text[:i].strip()
                right = text[i + 1:].strip()
                if left and right:
                    return BinaryOp(
                        op=text[i],
                        left=self._parse_expr(left),
                        right=self._parse_expr(right),
                    )

        # Unary minus
        if text.startswith("-"):
            return UnaryOp(op="-", operand=self._parse_expr(text[1:]))

        # Parenthesized
        if text.startswith("(") and text.endswith(")"):
            return self._parse_expr(text[1:-1])

        # Series index access: expr[index]
        if text.endswith("]") and "[" in text:
            bracket_idx = text.rindex("[")
            series_part = text[:bracket_idx]
            index_part = text[bracket_idx + 1:-1]
            return IndexAccess(
                series=self._parse_expr(series_part),
                index=self._parse_expr(index_part),
            )

        # Method/function call: obj.method(args) or func(args)
        if "(" in text and text.endswith(")"):
            paren_idx = text.index("(")
            func_name = text[:paren_idx].strip()
            args_str = text[paren_idx + 1:-1]

            if "." in func_name:
                parts = func_name.split(".", 1)
                return MethodCall(
                    object_name=parts[0],
                    method=parts[1],
                    args=self._parse_call_args(args_str),
                )
            else:
                return FunctionCall(
                    name=func_name,
                    args=self._parse_call_args(args_str),
                )

        # Dot access without call
        if "." in text and "(" not in text:
            parts = text.split(".", 1)
            return MethodCall(object_name=parts[0], method=parts[1])

        # Literals
        if text == "na":
            return NaLiteral()
        if text == "true":
            return BoolLiteral(value=True)
        if text == "false":
            return BoolLiteral(value=False)
        if text.startswith('"') and text.endswith('"'):
            return StringLiteral(value=text[1:-1])
        if text.startswith("'") and text.endswith("'"):
            return StringLiteral(value=text[1:-1])

        # Number
        try:
            if "." in text:
                float(text)
                return NumberLiteral(value=text, is_float=True)
            else:
                int(text)
                return NumberLiteral(value=text, is_float=False)
        except ValueError:
            pass

        # Identifier
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", text):
            return Identifier(name=text)

        # Fallback - try as identifier
        return Identifier(name=text)

    def _parse_call_args(self, args_str: str) -> list[PineNode]:
        """Parse function call arguments."""
        if not args_str.strip():
            return []

        args: list[PineNode] = []
        # Simple split by comma (doesn't handle nested commas properly)
        depth = 0
        current = ""
        for ch in args_str:
            if ch in "([":
                depth += 1
                current += ch
            elif ch in ")]":
                depth -= 1
                current += ch
            elif ch == "," and depth == 0:
                args.append(self._parse_expr(current.strip()))
                current = ""
            else:
                current += ch

        if current.strip():
            args.append(self._parse_expr(current.strip()))

        return args

    def _extract_parens(self, text: str, prefix: str) -> str:
        """Extract content within parentheses after a prefix."""
        idx = text.index(prefix) + len(prefix)
        # Find the opening paren
        while idx < len(text) and text[idx] != "(":
            idx += 1
        if idx >= len(text):
            return ""

        depth = 0
        start = idx + 1
        for i in range(idx, len(text)):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    return text[start:i]
        return text[start:]

    def _parse_kwargs_str(self, text: str) -> dict[str, str]:
        """Parse keyword arguments from a string."""
        result: dict[str, str] = {}
        positional = 0

        if not text.strip():
            return result

        depth = 0
        current = ""
        for ch in text:
            if ch in "([":
                depth += 1
                current += ch
            elif ch in ")]":
                depth -= 1
                current += ch
            elif ch == "," and depth == 0:
                self._add_kwarg(result, current.strip(), positional)
                if "=" not in current:
                    positional += 1
                current = ""
            else:
                current += ch

        if current.strip():
            self._add_kwarg(result, current.strip(), positional)

        return result

    def _add_kwarg(self, result: dict[str, str], arg: str, pos: int) -> None:
        """Add a parsed argument to the result dict."""
        if "=" in arg:
            key, _, value = arg.partition("=")
            result[key.strip()] = value.strip().strip('"').strip("'")
        else:
            result[str(pos)] = arg.strip().strip('"').strip("'")
