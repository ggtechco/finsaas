"""Backtest execution endpoint."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, HTTPException

from finsaas.web import UPLOAD_DIR
from finsaas.web.schemas import (
    BacktestRequest,
    BacktestResponse,
    EquityPointResponse,
    TradeResponse,
)

router = APIRouter(tags=["backtest"])


@router.post("/backtest")
def run_backtest(req: BacktestRequest) -> BacktestResponse:
    from finsaas.api.facade import backtest
    from finsaas.strategy.registry import get_strategy

    # Validate CSV exists
    csv_path = UPLOAD_DIR / req.csv_file
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"CSV file not found: {req.csv_file}")

    # Get strategy class and create instance
    try:
        cls = get_strategy(req.strategy)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    strategy = cls()

    # Set parameters
    for key, value in req.parameters.items():
        if hasattr(strategy, key):
            setattr(strategy, key, value)

    try:
        result = backtest(
            strategy=strategy,
            csv_path=str(csv_path),
            symbol=req.symbol,
            timeframe=req.timeframe,
            initial_capital=Decimal(str(req.initial_capital)),
            commission=Decimal(str(req.commission)),
            slippage=Decimal(str(req.slippage)),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    trades = [
        TradeResponse(
            entry_time=t.entry_time.isoformat(),
            exit_time=t.exit_time.isoformat(),
            side=t.side.value,
            entry_price=float(t.entry_price),
            exit_price=float(t.exit_price),
            quantity=float(t.quantity),
            pnl=float(t.pnl),
            pnl_pct=float(t.pnl_pct),
            commission=float(t.commission),
            bars_held=t.bars_held,
        )
        for t in result.trades
    ]

    equity_curve = [
        EquityPointResponse(
            bar_index=ep.bar_index,
            timestamp=ep.timestamp.isoformat(),
            equity=float(ep.equity),
            cash=float(ep.cash),
            position_value=float(ep.position_value),
            drawdown=float(ep.drawdown),
        )
        for ep in result.equity_curve
    ]

    return BacktestResponse(
        strategy=result.strategy_name,
        run_hash=result.run_hash,
        parameters={k: str(v) for k, v in result.parameters.items()},
        config={
            "symbol": result.config.symbol_info.ticker,
            "timeframe": result.config.timeframe.value,
            "initial_capital": float(result.config.initial_capital),
        },
        metrics={k: float(v) for k, v in result.metrics.items()},
        total_bars=result.total_bars,
        final_equity=float(result.final_equity),
        total_trades=len(result.trades),
        trades=trades,
        equity_curve=equity_curve,
    )
