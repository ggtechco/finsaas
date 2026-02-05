"""Integration tests - full backtest pipeline from CSV to results."""

from decimal import Decimal
from pathlib import Path

import pytest

from finsaas.core.context import BarContext
from finsaas.core.types import Side, SymbolInfo, Timeframe
from finsaas.data.feed import CSVFeed
from finsaas.engine.commission import PercentageCommission
from finsaas.engine.runner import BacktestConfig, BacktestResult, BacktestRunner
from finsaas.engine.slippage import PercentageSlippage
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import IntParam


FIXTURES = Path(__file__).parent.parent / "fixtures"


class SMACrossover(Strategy):
    """Standard SMA crossover strategy for integration testing."""

    fast_length = IntParam(default=3, min_val=2, max_val=10)
    slow_length = IntParam(default=5, min_val=3, max_val=20)

    def on_init(self):
        self.fast_ma = self.create_series("fast_ma")
        self.slow_ma = self.create_series("slow_ma")

    def on_bar(self, ctx: BarContext) -> None:
        self.fast_ma.current = self.ta.sma(self.close, self.fast_length)
        self.slow_ma.current = self.ta.sma(self.close, self.slow_length)

        if self.ta.crossover(self.fast_ma, self.slow_ma):
            self.entry("long", Side.LONG)
        elif self.ta.crossunder(self.fast_ma, self.slow_ma):
            self.close_position("long")


class TestFullBacktest:
    def test_csv_to_backtest(self):
        """Full pipeline: CSV -> Feed -> Strategy -> Runner -> Result."""
        csv_path = FIXTURES / "sample_ohlcv.csv"
        feed = CSVFeed(filepath=str(csv_path), symbol="BTCUSDT", timeframe="1h")

        config = BacktestConfig(
            symbol_info=SymbolInfo(ticker="BTCUSDT", exchange="Binance"),
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
            commission_model=PercentageCommission(Decimal("0.001")),
            slippage_model=PercentageSlippage(Decimal("0.0005")),
        )

        strategy = SMACrossover()
        runner = BacktestRunner(feed, config)
        result = runner.run(strategy)

        # Basic sanity checks
        assert isinstance(result, BacktestResult)
        assert result.run_hash  # Non-empty hash
        assert result.strategy_name == "SMACrossover"
        assert result.total_bars == 24  # 24 bars in sample CSV
        assert result.final_equity > 0
        assert len(result.equity_curve) == 24

        # Metrics should be present
        assert "total_return" in result.metrics
        assert "sharpe_ratio" in result.metrics
        assert "max_drawdown" in result.metrics
        assert "win_rate" in result.metrics

    def test_text_report_generation(self):
        """Verify text report can be generated from results."""
        from finsaas.analytics.report import generate_text_report

        csv_path = FIXTURES / "sample_ohlcv.csv"
        feed = CSVFeed(filepath=str(csv_path), symbol="BTCUSDT", timeframe="1h")
        config = BacktestConfig(
            symbol_info=SymbolInfo(ticker="BTCUSDT"),
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
        )

        result = BacktestRunner(feed, config).run(SMACrossover())
        report = generate_text_report(result)

        assert "BACKTEST REPORT" in report
        assert "SMACrossover" in report
        assert "Final Equity" in report

    def test_json_report_generation(self):
        """Verify JSON report can be generated from results."""
        import json
        from finsaas.analytics.report import generate_json_report

        csv_path = FIXTURES / "sample_ohlcv.csv"
        feed = CSVFeed(filepath=str(csv_path), symbol="BTCUSDT", timeframe="1h")
        config = BacktestConfig(
            symbol_info=SymbolInfo(ticker="BTCUSDT"),
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
        )

        result = BacktestRunner(feed, config).run(SMACrossover())
        json_str = generate_json_report(result)
        data = json.loads(json_str)

        assert data["strategy"] == "SMACrossover"
        assert "metrics" in data
        assert "trades" in data
        assert data["total_bars"] == 24

    def test_facade_api(self):
        """Test the high-level facade API."""
        from finsaas.api.facade import backtest

        csv_path = FIXTURES / "sample_ohlcv.csv"
        result = backtest(
            strategy=SMACrossover(),
            csv_path=csv_path,
            symbol="BTCUSDT",
            timeframe="1h",
            initial_capital=Decimal("10000"),
            commission=Decimal("0.001"),
            slippage=Decimal("0"),
        )

        assert isinstance(result, BacktestResult)
        assert result.total_bars == 24
