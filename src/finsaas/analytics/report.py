"""Report generation for backtest results."""

from __future__ import annotations

import json
from decimal import Decimal

from finsaas.analytics.equity import analyze_equity
from finsaas.analytics.trades import analyze_trades
from finsaas.engine.runner import BacktestResult


def generate_text_report(result: BacktestResult) -> str:
    """Generate a plain-text performance report."""
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append(f"  BACKTEST REPORT: {result.strategy_name}")
    lines.append("=" * 60)
    lines.append("")

    # Configuration
    lines.append("Configuration:")
    lines.append(f"  Symbol:          {result.config.symbol_info.ticker}")
    lines.append(f"  Timeframe:       {result.config.timeframe.value}")
    lines.append(f"  Initial Capital: {result.config.initial_capital}")
    lines.append(f"  Parameters:      {result.parameters}")
    lines.append(f"  Run Hash:        {result.run_hash[:16]}...")
    lines.append(f"  Total Bars:      {result.total_bars}")
    lines.append("")

    # Key Metrics
    m = result.metrics
    lines.append("Performance Metrics:")
    lines.append(f"  Final Equity:    {result.final_equity:.2f}")
    lines.append(f"  Total Return:    {m.get('total_return', Decimal('0')):.2f}")
    lines.append(f"  Total Return %:  {m.get('total_return_pct', Decimal('0')):.2f}%")
    lines.append(f"  Sharpe Ratio:    {m.get('sharpe_ratio', Decimal('0')):.4f}")
    lines.append(f"  Sortino Ratio:   {m.get('sortino_ratio', Decimal('0')):.4f}")
    lines.append(f"  Calmar Ratio:    {m.get('calmar_ratio', Decimal('0')):.4f}")
    lines.append(f"  Max Drawdown:    {m.get('max_drawdown_pct', Decimal('0')):.2f}%")
    lines.append("")

    # Trade Stats
    lines.append("Trade Statistics:")
    lines.append(f"  Total Trades:    {m.get('total_trades', Decimal('0')):.0f}")
    lines.append(f"  Win Rate:        {m.get('win_rate', Decimal('0')):.2f}%")
    lines.append(f"  Profit Factor:   {m.get('profit_factor', Decimal('0')):.4f}")
    lines.append(f"  Avg Trade P&L:   {m.get('avg_trade_pnl', Decimal('0')):.2f}")
    lines.append(f"  Avg Win:         {m.get('avg_win', Decimal('0')):.2f}")
    lines.append(f"  Avg Loss:        {m.get('avg_loss', Decimal('0')):.2f}")
    lines.append(f"  Largest Win:     {m.get('largest_win', Decimal('0')):.2f}")
    lines.append(f"  Largest Loss:    {m.get('largest_loss', Decimal('0')):.2f}")
    lines.append(f"  Avg Bars Held:   {m.get('avg_bars_held', Decimal('0')):.1f}")
    lines.append(f"  Total Commission:{m.get('total_commission', Decimal('0')):.2f}")
    lines.append(f"  Expectancy:      {m.get('expectancy', Decimal('0')):.2f}")
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def generate_json_report(result: BacktestResult) -> str:
    """Generate a JSON report of backtest results."""

    def decimal_default(obj: object) -> object:
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    report = {
        "strategy": result.strategy_name,
        "run_hash": result.run_hash,
        "parameters": {k: str(v) for k, v in result.parameters.items()},
        "config": {
            "symbol": result.config.symbol_info.ticker,
            "timeframe": result.config.timeframe.value,
            "initial_capital": float(result.config.initial_capital),
        },
        "metrics": {k: float(v) for k, v in result.metrics.items()},
        "total_bars": result.total_bars,
        "final_equity": float(result.final_equity),
        "total_trades": len(result.trades),
        "trades": [
            {
                "entry_time": t.entry_time.isoformat(),
                "exit_time": t.exit_time.isoformat(),
                "side": t.side.value,
                "entry_price": float(t.entry_price),
                "exit_price": float(t.exit_price),
                "quantity": float(t.quantity),
                "pnl": float(t.pnl),
                "pnl_pct": float(t.pnl_pct),
                "commission": float(t.commission),
                "bars_held": t.bars_held,
            }
            for t in result.trades
        ],
    }

    return json.dumps(report, indent=2, default=decimal_default)
