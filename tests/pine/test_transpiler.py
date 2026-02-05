"""Tests for Pine Script transpiler."""

import pytest

from finsaas.pine.parser import PineParser
from finsaas.pine.transpiler import PineTranspiler


@pytest.fixture
def parser() -> PineParser:
    return PineParser()


@pytest.fixture
def transpiler() -> PineTranspiler:
    return PineTranspiler()


class TestTranspiler:
    def test_transpile_simple_strategy(self, parser, transpiler):
        source = '''
//@version=5
strategy("Simple Test", overlay=true)
fast_length = input.int(defval=10, title="Fast", minval=1, maxval=100)
'''
        ast = parser.parse(source)
        python_code = transpiler.transpile(ast)

        assert "class SimpleTest(Strategy):" in python_code
        assert "IntParam" in python_code
        assert "fast_length" in python_code

    def test_transpile_includes_imports(self, parser, transpiler):
        source = '''
//@version=5
strategy("Test")
'''
        ast = parser.parse(source)
        python_code = transpiler.transpile(ast)

        assert "from decimal import Decimal" in python_code
        assert "from finsaas.strategy.base import Strategy" in python_code

    def test_transpile_sma_crossover(self, parser, transpiler):
        source = '''
//@version=5
strategy("SMA Crossover", overlay=true)
fast_length = input.int(defval=10, title="Fast Length", minval=1)
slow_length = input.int(defval=20, title="Slow Length", minval=1)
fast_ma = ta.sma(close, fast_length)
slow_ma = ta.sma(close, slow_length)
'''
        ast = parser.parse(source)
        python_code = transpiler.transpile(ast)

        assert "class SmaCrossover(Strategy):" in python_code
        assert "self.ta.sma" in python_code
        assert "self.close" in python_code

    def test_transpile_strategy_entry(self, parser, transpiler):
        source = '''
//@version=5
strategy("Test")
if ta.crossover(fast_ma, slow_ma)
    strategy.entry("long", strategy.long)
'''
        ast = parser.parse(source)
        python_code = transpiler.transpile(ast)

        assert "self.entry" in python_code
        assert "Side.LONG" in python_code

    def test_transpile_produces_valid_python(self, parser, transpiler):
        """The transpiled code should be syntactically valid Python."""
        source = '''
//@version=5
strategy("Valid Test")
x = input.int(defval=10)
'''
        ast = parser.parse(source)
        python_code = transpiler.transpile(ast)

        # Should compile without syntax errors
        compile(python_code, "<test>", "exec")
