"""Integration tests - Pine Script parse -> transpile pipeline."""

from pathlib import Path

import pytest

from finsaas.pine.parser import PineParser
from finsaas.pine.transpiler import PineTranspiler


FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestPineBacktest:
    def test_parse_sample_pine(self):
        """Parse the sample SMA crossover Pine script."""
        pine_path = FIXTURES / "sample_pine_scripts" / "sma_crossover.pine"
        source = pine_path.read_text()

        parser = PineParser()
        ast = parser.parse(source)

        assert ast.version == 5
        assert ast.indicator_or_strategy is not None

    def test_transpile_sample_pine(self):
        """Transpile the sample SMA crossover Pine script to Python."""
        pine_path = FIXTURES / "sample_pine_scripts" / "sma_crossover.pine"
        source = pine_path.read_text()

        parser = PineParser()
        ast = parser.parse(source)

        transpiler = PineTranspiler()
        python_code = transpiler.transpile(ast)

        # Check for expected content
        assert "class SmaCrossover(Strategy):" in python_code
        assert "IntParam" in python_code
        assert "self.ta.sma" in python_code
        assert "self.close" in python_code
        assert "self.entry" in python_code
        assert "Side.LONG" in python_code

    def test_transpiled_code_compiles(self):
        """The transpiled code should be syntactically valid Python."""
        pine_path = FIXTURES / "sample_pine_scripts" / "sma_crossover.pine"
        source = pine_path.read_text()

        parser = PineParser()
        ast = parser.parse(source)

        transpiler = PineTranspiler()
        python_code = transpiler.transpile(ast)

        # Should not raise SyntaxError
        compile(python_code, "<pine_test>", "exec")

    def test_round_trip_parse_transpile(self):
        """Parse multiple simple scripts and verify transpilation."""
        scripts = [
            '''
//@version=5
strategy("Simple", overlay=true)
length = input.int(defval=14, title="Length")
ma = ta.sma(close, length)
plot(ma)
''',
            '''
//@version=5
indicator("RSI Test")
rsi_val = ta.rsi(close, 14)
''',
        ]

        parser = PineParser()
        transpiler = PineTranspiler()

        for source in scripts:
            ast = parser.parse(source)
            python_code = transpiler.transpile(ast)
            # Should compile without errors
            compile(python_code, "<test>", "exec")
