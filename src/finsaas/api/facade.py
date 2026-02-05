"""Programmatic Python API facade for FinSaaS.

Provides a clean, high-level interface for running backtests
and optimizations from Python code.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from finsaas.core.types import SymbolInfo, Timeframe
from finsaas.data.feed import CSVFeed, DataFeed, InMemoryFeed
from finsaas.engine.commission import CommissionModel, PercentageCommission, ZeroCommission
from finsaas.engine.runner import BacktestConfig, BacktestResult, BacktestRunner
from finsaas.engine.slippage import PercentageSlippage, SlippageModel, ZeroSlippage
from finsaas.strategy.base import Strategy


def backtest(
    strategy: Strategy,
    feed: DataFeed | None = None,
    csv_path: str | Path | None = None,
    symbol: str = "UNKNOWN",
    timeframe: str = "1h",
    initial_capital: Decimal = Decimal("10000"),
    commission: Decimal | CommissionModel = Decimal("0.001"),
    slippage: Decimal | SlippageModel = Decimal("0.0005"),
    max_bars_back: int = 5000,
) -> BacktestResult:
    """Run a backtest with minimal boilerplate.

    Usage:
        from finsaas.api.facade import backtest
        from my_strategy import SMACrossover

        result = backtest(
            strategy=SMACrossover(),
            csv_path="data.csv",
            symbol="BTCUSDT",
            initial_capital=Decimal("10000"),
        )
        print(f"Return: {result.metrics['total_return_pct']:.2f}%")
    """
    # Create feed
    if feed is None:
        if csv_path is not None:
            feed = CSVFeed(filepath=str(csv_path), symbol=symbol, timeframe=timeframe)
        else:
            raise ValueError("Either feed or csv_path must be provided")

    # Create commission/slippage models
    comm_model: CommissionModel
    if isinstance(commission, CommissionModel):
        comm_model = commission
    elif commission == 0:
        comm_model = ZeroCommission()
    else:
        comm_model = PercentageCommission(Decimal(str(commission)))

    slip_model: SlippageModel
    if isinstance(slippage, SlippageModel):
        slip_model = slippage
    elif slippage == 0:
        slip_model = ZeroSlippage()
    else:
        slip_model = PercentageSlippage(Decimal(str(slippage)))

    config = BacktestConfig(
        symbol_info=SymbolInfo(ticker=feed.symbol),
        timeframe=Timeframe(feed.timeframe),
        initial_capital=initial_capital,
        commission_model=comm_model,
        slippage_model=slip_model,
        max_bars_back=max_bars_back,
    )

    runner = BacktestRunner(feed, config)
    return runner.run(strategy)


def optimize(
    strategy_cls: type,
    feed: DataFeed | None = None,
    csv_path: str | Path | None = None,
    symbol: str = "UNKNOWN",
    timeframe: str = "1h",
    initial_capital: Decimal = Decimal("10000"),
    method: str = "grid",
    objective: str = "sharpe",
    max_workers: int = 1,
    **opt_kwargs: object,
) -> object:
    """Run parameter optimization with minimal boilerplate.

    Usage:
        from finsaas.api.facade import optimize
        from my_strategy import SMACrossover

        result = optimize(
            strategy_cls=SMACrossover,
            csv_path="data.csv",
            symbol="BTCUSDT",
            method="genetic",
            objective="sharpe",
        )
    """
    from finsaas.engine.runner import BacktestConfig
    from finsaas.optimization.optimizer import run_optimization

    if feed is None:
        if csv_path is not None:
            feed = CSVFeed(filepath=str(csv_path), symbol=symbol, timeframe=timeframe)
        else:
            raise ValueError("Either feed or csv_path must be provided")

    config = BacktestConfig(
        symbol_info=SymbolInfo(ticker=feed.symbol),
        timeframe=Timeframe(feed.timeframe),
        initial_capital=initial_capital,
    )

    return run_optimization(
        strategy_cls=strategy_cls,
        feed=feed,
        config=config,
        method=method,
        objective=objective,
        max_workers=max_workers,
        **opt_kwargs,  # type: ignore[arg-type]
    )
