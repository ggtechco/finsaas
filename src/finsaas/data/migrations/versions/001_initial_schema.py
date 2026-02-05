"""Initial schema - all tables.

Revision ID: 001
Revises: None
Create Date: 2024-01-01 00:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Symbols table
    op.create_table(
        "symbols",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(50), nullable=False),
        sa.Column("exchange", sa.String(50), nullable=False, server_default=""),
        sa.Column("asset_type", sa.String(20), nullable=False, server_default="crypto"),
        sa.Column("tick_size", sa.Numeric(20, 10), nullable=False, server_default="0.01"),
        sa.Column("lot_size", sa.Numeric(20, 10), nullable=False, server_default="0.001"),
        sa.Column("base_currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("quote_currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "exchange", name="uq_symbol_ticker_exchange"),
    )

    # OHLCV bars table
    op.create_table(
        "ohlcv_bars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol_id", sa.Integer(), sa.ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timeframe", sa.String(10), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("open", sa.Numeric(20, 10), nullable=False),
        sa.Column("high", sa.Numeric(20, 10), nullable=False),
        sa.Column("low", sa.Numeric(20, 10), nullable=False),
        sa.Column("close", sa.Numeric(20, 10), nullable=False),
        sa.Column("volume", sa.Numeric(20, 10), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol_id", "timeframe", "timestamp", name="uq_ohlcv_symbol_tf_ts"),
    )
    op.create_index("ix_ohlcv_symbol_tf_ts", "ohlcv_bars", ["symbol_id", "timeframe", "timestamp"])

    # Backtest runs table
    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("strategy_name", sa.String(100), nullable=False),
        sa.Column("symbol_ticker", sa.String(50), nullable=False),
        sa.Column("timeframe", sa.String(10), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("initial_capital", sa.Numeric(20, 10), nullable=False),
        sa.Column("parameters", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("commission_rate", sa.Numeric(20, 10), nullable=False),
        sa.Column("slippage_rate", sa.Numeric(20, 10), nullable=False),
        sa.Column("total_return", sa.Numeric(20, 10)),
        sa.Column("sharpe_ratio", sa.Numeric(20, 10)),
        sa.Column("sortino_ratio", sa.Numeric(20, 10)),
        sa.Column("max_drawdown", sa.Numeric(20, 10)),
        sa.Column("win_rate", sa.Numeric(20, 10)),
        sa.Column("profit_factor", sa.Numeric(20, 10)),
        sa.Column("total_trades", sa.Integer()),
        sa.Column("metrics_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Backtest trades table
    op.create_table(
        "backtest_trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trade_index", sa.Integer(), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("entry_time", sa.DateTime(), nullable=False),
        sa.Column("exit_time", sa.DateTime(), nullable=False),
        sa.Column("entry_price", sa.Numeric(20, 10), nullable=False),
        sa.Column("exit_price", sa.Numeric(20, 10), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 10), nullable=False),
        sa.Column("pnl", sa.Numeric(20, 10), nullable=False),
        sa.Column("pnl_pct", sa.Numeric(20, 10), nullable=False),
        sa.Column("commission", sa.Numeric(20, 10), nullable=False),
        sa.Column("bars_held", sa.Integer(), nullable=False),
        sa.Column("entry_tag", sa.String(100), nullable=False, server_default=""),
        sa.Column("exit_tag", sa.String(100), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trade_run_id", "backtest_trades", ["run_id"])

    # Backtest equity curve table
    op.create_table(
        "backtest_equity_curve",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bar_index", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("equity", sa.Numeric(20, 10), nullable=False),
        sa.Column("cash", sa.Numeric(20, 10), nullable=False),
        sa.Column("position_value", sa.Numeric(20, 10), nullable=False),
        sa.Column("drawdown", sa.Numeric(20, 10), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equity_run_id_bar", "backtest_equity_curve", ["run_id", "bar_index"])

    # Optimization runs table
    op.create_table(
        "optimization_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("strategy_name", sa.String(100), nullable=False),
        sa.Column("symbol_ticker", sa.String(50), nullable=False),
        sa.Column("timeframe", sa.String(10), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("objective", sa.String(50), nullable=False),
        sa.Column("parameter_space", postgresql.JSONB(), nullable=False),
        sa.Column("total_trials", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_params", postgresql.JSONB()),
        sa.Column("best_objective_value", sa.Numeric(20, 10)),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Optimization trials table
    op.create_table(
        "optimization_trials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trial_index", sa.Integer(), nullable=False),
        sa.Column("parameters", postgresql.JSONB(), nullable=False),
        sa.Column("objective_value", sa.Numeric(20, 10), nullable=False),
        sa.Column("metrics_json", postgresql.JSONB()),
        sa.Column("backtest_run_hash", sa.String(64)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trial_run_id", "optimization_trials", ["run_id"])


def downgrade() -> None:
    op.drop_table("optimization_trials")
    op.drop_table("optimization_runs")
    op.drop_table("backtest_equity_curve")
    op.drop_table("backtest_trades")
    op.drop_table("backtest_runs")
    op.drop_table("ohlcv_bars")
    op.drop_table("symbols")
