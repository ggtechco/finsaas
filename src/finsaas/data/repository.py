"""Repository pattern for database access."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finsaas.core.types import OHLCV
from finsaas.data.models import (
    BacktestEquityCurve,
    BacktestRun,
    BacktestTrade,
    OHLCVBar,
    OptimizationRun,
    OptimizationTrial,
    Symbol,
)


class SymbolRepository:
    """CRUD operations for Symbol entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create(
        self, ticker: str, exchange: str = "", **kwargs: object
    ) -> Symbol:
        stmt = select(Symbol).where(
            Symbol.ticker == ticker, Symbol.exchange == exchange
        )
        symbol = self._session.execute(stmt).scalar_one_or_none()
        if symbol is None:
            symbol = Symbol(ticker=ticker, exchange=exchange, **kwargs)  # type: ignore[arg-type]
            self._session.add(symbol)
            self._session.flush()
        return symbol

    def get_by_ticker(self, ticker: str, exchange: str = "") -> Symbol | None:
        stmt = select(Symbol).where(
            Symbol.ticker == ticker, Symbol.exchange == exchange
        )
        return self._session.execute(stmt).scalar_one_or_none()


class OHLCVRepository:
    """CRUD operations for OHLCV bar data."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def bulk_insert(self, bars: list[OHLCVBar]) -> int:
        self._session.add_all(bars)
        self._session.flush()
        return len(bars)

    def get_bars(
        self,
        symbol_id: int,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[OHLCV]:
        """Fetch OHLCV bars as core OHLCV tuples, ordered by timestamp."""
        stmt = (
            select(OHLCVBar)
            .where(OHLCVBar.symbol_id == symbol_id, OHLCVBar.timeframe == timeframe)
            .order_by(OHLCVBar.timestamp)
        )
        if start:
            stmt = stmt.where(OHLCVBar.timestamp >= start)
        if end:
            stmt = stmt.where(OHLCVBar.timestamp <= end)

        rows = self._session.execute(stmt).scalars().all()
        return [
            OHLCV(
                timestamp=row.timestamp,
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                volume=row.volume,
            )
            for row in rows
        ]

    def count(self, symbol_id: int, timeframe: str) -> int:
        from sqlalchemy import func

        stmt = select(func.count(OHLCVBar.id)).where(
            OHLCVBar.symbol_id == symbol_id, OHLCVBar.timeframe == timeframe
        )
        result = self._session.execute(stmt).scalar()
        return result or 0


class BacktestRepository:
    """CRUD operations for backtest results."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save_run(self, run: BacktestRun) -> BacktestRun:
        self._session.add(run)
        self._session.flush()
        return run

    def get_by_hash(self, run_hash: str) -> BacktestRun | None:
        stmt = select(BacktestRun).where(BacktestRun.run_hash == run_hash)
        return self._session.execute(stmt).scalar_one_or_none()

    def save_trades(self, trades: list[BacktestTrade]) -> int:
        self._session.add_all(trades)
        self._session.flush()
        return len(trades)

    def save_equity_curve(self, points: list[BacktestEquityCurve]) -> int:
        self._session.add_all(points)
        self._session.flush()
        return len(points)

    def get_trades(self, run_id: int) -> list[BacktestTrade]:
        stmt = (
            select(BacktestTrade)
            .where(BacktestTrade.run_id == run_id)
            .order_by(BacktestTrade.trade_index)
        )
        return list(self._session.execute(stmt).scalars().all())

    def get_equity_curve(self, run_id: int) -> list[BacktestEquityCurve]:
        stmt = (
            select(BacktestEquityCurve)
            .where(BacktestEquityCurve.run_id == run_id)
            .order_by(BacktestEquityCurve.bar_index)
        )
        return list(self._session.execute(stmt).scalars().all())


class OptimizationRepository:
    """CRUD operations for optimization results."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save_run(self, run: OptimizationRun) -> OptimizationRun:
        self._session.add(run)
        self._session.flush()
        return run

    def save_trial(self, trial: OptimizationTrial) -> OptimizationTrial:
        self._session.add(trial)
        self._session.flush()
        return trial

    def save_trials(self, trials: list[OptimizationTrial]) -> int:
        self._session.add_all(trials)
        self._session.flush()
        return len(trials)

    def get_best_trial(self, run_id: int) -> OptimizationTrial | None:
        stmt = (
            select(OptimizationTrial)
            .where(OptimizationTrial.run_id == run_id)
            .order_by(OptimizationTrial.objective_value.desc())
            .limit(1)
        )
        return self._session.execute(stmt).scalar_one_or_none()
