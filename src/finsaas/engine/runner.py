"""BacktestRunner - top-level orchestrator for running backtests."""

from __future__ import annotations

import hashlib
import json
import structlog
from dataclasses import dataclass, field
from decimal import Decimal

from finsaas.core.config import Settings, get_settings
from finsaas.core.types import SymbolInfo, Timeframe, TradeResult
from finsaas.data.feed import DataFeed
from finsaas.engine.commission import CommissionModel, PercentageCommission
from finsaas.engine.loop import EventLoop
from finsaas.engine.portfolio import EquityPoint
from finsaas.engine.slippage import PercentageSlippage, SlippageModel

logger = structlog.get_logger()


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""

    symbol_info: SymbolInfo
    timeframe: Timeframe
    initial_capital: Decimal = Decimal("10000")
    commission_model: CommissionModel | None = None
    slippage_model: SlippageModel | None = None
    max_bars_back: int = 5000


@dataclass
class BacktestResult:
    """Complete result of a backtest run."""

    run_hash: str
    strategy_name: str
    parameters: dict[str, object]
    config: BacktestConfig
    trades: list[TradeResult]
    equity_curve: list[EquityPoint]
    final_equity: Decimal
    total_bars: int
    metrics: dict[str, Decimal] = field(default_factory=dict)


class BacktestRunner:
    """Top-level orchestrator for running backtests.

    Usage:
        runner = BacktestRunner(feed, config)
        result = runner.run(strategy)
    """

    def __init__(
        self,
        feed: DataFeed,
        config: BacktestConfig | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._feed = feed
        self._settings = settings or get_settings()

        if config is None:
            config = BacktestConfig(
                symbol_info=SymbolInfo(ticker=feed.symbol),
                timeframe=Timeframe(feed.timeframe),
                initial_capital=self._settings.default_initial_capital,
                commission_model=PercentageCommission(self._settings.default_commission_rate),
                slippage_model=PercentageSlippage(self._settings.default_slippage_rate),
            )
        self._config = config

    def run(self, strategy: object) -> BacktestResult:
        """Run a backtest with the given strategy.

        Returns a BacktestResult with trades, equity curve, and metrics.
        """
        from finsaas.strategy.base import Strategy

        strat: Strategy = strategy  # type: ignore[assignment]

        # Compute deterministic run hash
        run_hash = self._compute_hash(strat)

        logger.info("backtest_start", strategy=strat.name, symbol=self._feed.symbol,
                     run_hash=run_hash)

        loop = EventLoop(
            feed=self._feed,
            symbol_info=self._config.symbol_info,
            timeframe=self._config.timeframe,
            initial_capital=self._config.initial_capital,
            commission_model=self._config.commission_model,
            slippage_model=self._config.slippage_model,
            max_bars_back=self._config.max_bars_back,
        )

        loop.run(strat)

        # Get bars for final equity
        bars = list(self._feed)
        final_equity = Decimal("0")
        if bars:
            final_equity = loop.portfolio.equity(bars[-1].close)

        # Compute metrics
        from finsaas.analytics.metrics import compute_all_metrics

        metrics = compute_all_metrics(
            loop.portfolio.trade_results,
            loop.portfolio.equity_curve,
            self._config.initial_capital,
        )

        result = BacktestResult(
            run_hash=run_hash,
            strategy_name=strat.name,
            parameters=strat.get_parameters(),
            config=self._config,
            trades=loop.portfolio.trade_results,
            equity_curve=loop.portfolio.equity_curve,
            final_equity=final_equity,
            total_bars=len(bars),
            metrics=metrics,
        )

        logger.info("backtest_complete", strategy=strat.name,
                     final_equity=str(final_equity),
                     total_trades=len(result.trades))

        return result

    def _compute_hash(self, strategy: object) -> str:
        """Compute a deterministic hash of all backtest inputs.

        SHA-256(strategy_name + parameters + symbol + timeframe + data_hash + config)
        Same hash = same results (deterministic guarantee).
        """
        from finsaas.strategy.base import Strategy

        strat: Strategy = strategy  # type: ignore[assignment]

        components = [
            strat.name,
            json.dumps(strat.get_parameters(), sort_keys=True, default=str),
            self._feed.symbol,
            self._feed.timeframe,
            str(self._config.initial_capital),
            str(len(list(self._feed))),
        ]
        raw = "|".join(components)
        return hashlib.sha256(raw.encode()).hexdigest()
