"""Tests for Pine Script parser."""

import pytest

from finsaas.pine.ast_nodes import (
    FunctionCall,
    Identifier,
    InputDecl,
    MethodCall,
    NumberLiteral,
    Script,
    StrategyDecl,
    VarDecl,
)
from finsaas.pine.parser import PineParser


@pytest.fixture
def parser() -> PineParser:
    return PineParser()


class TestVersionParsing:
    def test_parse_version(self, parser: PineParser):
        script = parser.parse("//@version=5")
        assert script.version == 5


class TestStrategyDeclaration:
    def test_parse_strategy_decl(self, parser: PineParser):
        source = '''
//@version=5
strategy("My Strategy", overlay=true, initial_capital=10000)
'''
        script = parser.parse(source)
        assert isinstance(script.indicator_or_strategy, StrategyDecl)
        assert script.indicator_or_strategy.title == "My Strategy"
        assert script.indicator_or_strategy.overlay is True
        assert script.indicator_or_strategy.initial_capital == 10000


class TestInputParsing:
    def test_parse_int_input(self, parser: PineParser):
        source = '''
//@version=5
strategy("Test")
fast_length = input.int(defval=10, title="Fast", minval=1, maxval=100)
'''
        script = parser.parse(source)
        assert len(script.declarations) == 1
        inp = script.declarations[0]
        assert isinstance(inp, InputDecl)
        assert inp.name == "fast_length"
        assert inp.input_type == "int"
        assert inp.default_value == "10"
        assert inp.min_val == "1"
        assert inp.max_val == "100"


class TestExpressionParsing:
    def test_parse_number(self, parser: PineParser):
        node = parser._parse_expr("42")
        assert isinstance(node, NumberLiteral)
        assert node.value == "42"

    def test_parse_identifier(self, parser: PineParser):
        node = parser._parse_expr("close")
        assert isinstance(node, Identifier)
        assert node.name == "close"

    def test_parse_function_call(self, parser: PineParser):
        node = parser._parse_expr("ta.sma(close, 14)")
        assert isinstance(node, MethodCall)
        assert node.object_name == "ta"
        assert node.method == "sma"
        assert len(node.args) == 2


class TestCompleteParsing:
    def test_parse_sma_crossover(self, parser: PineParser):
        source = '''
//@version=5
strategy("SMA Crossover", overlay=true)
fast_length = input.int(defval=10, title="Fast Length", minval=1)
slow_length = input.int(defval=20, title="Slow Length", minval=1)
fast_ma = ta.sma(close, fast_length)
slow_ma = ta.sma(close, slow_length)
'''
        script = parser.parse(source)
        assert script.version == 5
        assert isinstance(script.indicator_or_strategy, StrategyDecl)
        assert len(script.declarations) == 2  # Two inputs
