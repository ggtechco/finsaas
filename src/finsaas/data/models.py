"""SQLAlchemy ORM models for the FinSaaS database schema."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Symbol(Base):
    """Symbol metadata (e.g., BTCUSDT on Binance)."""

    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(50), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False, default="crypto")
    tick_size: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False, default=Decimal("0.01")
    )
    lot_size: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False, default=Decimal("0.001")
    )
    base_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    quote_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    bars: Mapped[list[OHLCVBar]] = relationship("OHLCVBar", back_populates="symbol")

    __table_args__ = (
        UniqueConstraint("ticker", "exchange", name="uq_symbol_ticker_exchange"),
    )


class OHLCVBar(Base):
    """Historical OHLCV bar data."""

    __tablename__ = "ohlcv_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False
    )
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False, default=Decimal("0"))

    symbol: Mapped[Symbol] = relationship("Symbol", back_populates="bars")

    __table_args__ = (
        UniqueConstraint(
            "symbol_id", "timeframe", "timestamp", name="uq_ohlcv_symbol_tf_ts"
        ),
        Index("ix_ohlcv_symbol_tf_ts", "symbol_id", "timeframe", "timestamp"),
    )


class BacktestRun(Base):
    """A single backtest run with its configuration and results."""

    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol_ticker: Mapped[str] = mapped_column(String(50), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    initial_capital: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # type: ignore[assignment]
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    slippage_rate: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)

    # Summary metrics
    total_return: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    sortino_ratio: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    win_rate: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    profit_factor: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    total_trades: Mapped[int | None] = mapped_column(Integer)
    metrics_json: Mapped[dict | None] = mapped_column(JSONB)  # type: ignore[assignment]

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    trades: Mapped[list[BacktestTrade]] = relationship(
        "BacktestTrade", back_populates="run", cascade="all, delete-orphan"
    )
    equity_curve: Mapped[list[BacktestEquityCurve]] = relationship(
        "BacktestEquityCurve", back_populates="run", cascade="all, delete-orphan"
    )


class BacktestTrade(Base):
    """Individual trade from a backtest run."""

    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False
    )
    trade_index: Mapped[int] = mapped_column(Integer, nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    exit_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    exit_price: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    pnl: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    pnl_pct: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    bars_held: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_tag: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    exit_tag: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    run: Mapped[BacktestRun] = relationship("BacktestRun", back_populates="trades")

    __table_args__ = (Index("ix_trade_run_id", "run_id"),)


class BacktestEquityCurve(Base):
    """Bar-by-bar equity curve for a backtest run."""

    __tablename__ = "backtest_equity_curve"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False
    )
    bar_index: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    equity: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    cash: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    position_value: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    drawdown: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False, default=Decimal("0"))

    run: Mapped[BacktestRun] = relationship("BacktestRun", back_populates="equity_curve")

    __table_args__ = (Index("ix_equity_run_id_bar", "run_id", "bar_index"),)


class OptimizationRun(Base):
    """An optimization run configuration and summary."""

    __tablename__ = "optimization_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol_ticker: Mapped[str] = mapped_column(String(50), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    objective: Mapped[str] = mapped_column(String(50), nullable=False)
    parameter_space: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[assignment]
    total_trials: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    best_params: Mapped[dict | None] = mapped_column(JSONB)  # type: ignore[assignment]
    best_objective_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    trials: Mapped[list[OptimizationTrial]] = relationship(
        "OptimizationTrial", back_populates="run", cascade="all, delete-orphan"
    )


class OptimizationTrial(Base):
    """A single trial within an optimization run."""

    __tablename__ = "optimization_trials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False
    )
    trial_index: Mapped[int] = mapped_column(Integer, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[assignment]
    objective_value: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    metrics_json: Mapped[dict | None] = mapped_column(JSONB)  # type: ignore[assignment]
    backtest_run_hash: Mapped[str | None] = mapped_column(String(64))

    run: Mapped[OptimizationRun] = relationship(
        "OptimizationRun", back_populates="trials"
    )

    __table_args__ = (Index("ix_trial_run_id", "run_id"),)
