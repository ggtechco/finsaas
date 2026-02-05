"""Performance metrics computation.

All metrics use Decimal arithmetic for deterministic results.
"""

from __future__ import annotations

from decimal import Decimal

from finsaas.core.types import TradeResult
from finsaas.engine.portfolio import EquityPoint
from finsaas.strategy.builtins.math_funcs import sqrt as decimal_sqrt


def compute_all_metrics(
    trades: list[TradeResult],
    equity_curve: list[EquityPoint],
    initial_capital: Decimal,
) -> dict[str, Decimal]:
    """Compute all performance metrics from trade results and equity curve."""
    return {
        "total_return": total_return(equity_curve, initial_capital),
        "total_return_pct": total_return_pct(equity_curve, initial_capital),
        "sharpe_ratio": sharpe_ratio(equity_curve, initial_capital),
        "sortino_ratio": sortino_ratio(equity_curve, initial_capital),
        "calmar_ratio": calmar_ratio(equity_curve, initial_capital),
        "max_drawdown": max_drawdown(equity_curve),
        "max_drawdown_pct": max_drawdown_pct(equity_curve),
        "win_rate": win_rate(trades),
        "profit_factor": profit_factor(trades),
        "total_trades": Decimal(str(len(trades))),
        "winning_trades": Decimal(str(sum(1 for t in trades if t.pnl > 0))),
        "losing_trades": Decimal(str(sum(1 for t in trades if t.pnl <= 0))),
        "avg_trade_pnl": avg_trade_pnl(trades),
        "avg_win": avg_win(trades),
        "avg_loss": avg_loss(trades),
        "largest_win": largest_win(trades),
        "largest_loss": largest_loss(trades),
        "avg_bars_held": avg_bars_held(trades),
        "total_commission": total_commission(trades),
        "expectancy": expectancy(trades),
        "recovery_factor": recovery_factor(equity_curve, initial_capital),
    }


def total_return(equity_curve: list[EquityPoint], initial_capital: Decimal) -> Decimal:
    """Absolute total return."""
    if not equity_curve:
        return Decimal("0")
    return equity_curve[-1].equity - initial_capital


def total_return_pct(equity_curve: list[EquityPoint], initial_capital: Decimal) -> Decimal:
    """Total return as percentage."""
    if not equity_curve or initial_capital == 0:
        return Decimal("0")
    return ((equity_curve[-1].equity - initial_capital) / initial_capital) * Decimal("100")


def sharpe_ratio(
    equity_curve: list[EquityPoint],
    initial_capital: Decimal,
    risk_free_rate: Decimal = Decimal("0"),
    periods_per_year: int = 252,
) -> Decimal:
    """Annualized Sharpe ratio from equity curve returns."""
    returns = _equity_returns(equity_curve)
    if len(returns) < 2:
        return Decimal("0")

    mean_ret = sum(returns) / Decimal(str(len(returns)))
    excess_ret = mean_ret - risk_free_rate / Decimal(str(periods_per_year))

    std = _std(returns)
    if std == 0:
        return Decimal("0")

    return (excess_ret / std) * decimal_sqrt(Decimal(str(periods_per_year)))


def sortino_ratio(
    equity_curve: list[EquityPoint],
    initial_capital: Decimal,
    risk_free_rate: Decimal = Decimal("0"),
    periods_per_year: int = 252,
) -> Decimal:
    """Annualized Sortino ratio (uses downside deviation)."""
    returns = _equity_returns(equity_curve)
    if len(returns) < 2:
        return Decimal("0")

    mean_ret = sum(returns) / Decimal(str(len(returns)))
    target = risk_free_rate / Decimal(str(periods_per_year))
    excess_ret = mean_ret - target

    downside_returns = [r for r in returns if r < target]
    if not downside_returns:
        return Decimal("0") if excess_ret <= 0 else Decimal("999")

    downside_std = _std(downside_returns)
    if downside_std == 0:
        return Decimal("0")

    return (excess_ret / downside_std) * decimal_sqrt(Decimal(str(periods_per_year)))


def calmar_ratio(
    equity_curve: list[EquityPoint], initial_capital: Decimal
) -> Decimal:
    """Calmar ratio = annualized return / max drawdown."""
    ret = total_return_pct(equity_curve, initial_capital)
    mdd = max_drawdown_pct(equity_curve)
    if mdd == 0:
        return Decimal("0")
    return ret / mdd


def max_drawdown(equity_curve: list[EquityPoint]) -> Decimal:
    """Maximum drawdown in absolute terms."""
    if not equity_curve:
        return Decimal("0")
    peak = equity_curve[0].equity
    max_dd = Decimal("0")
    for point in equity_curve:
        if point.equity > peak:
            peak = point.equity
        dd = peak - point.equity
        if dd > max_dd:
            max_dd = dd
    return max_dd


def max_drawdown_pct(equity_curve: list[EquityPoint]) -> Decimal:
    """Maximum drawdown as percentage."""
    if not equity_curve:
        return Decimal("0")
    peak = equity_curve[0].equity
    max_dd_pct = Decimal("0")
    for point in equity_curve:
        if point.equity > peak:
            peak = point.equity
        if peak > 0:
            dd_pct = ((peak - point.equity) / peak) * Decimal("100")
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
    return max_dd_pct


def win_rate(trades: list[TradeResult]) -> Decimal:
    """Percentage of winning trades."""
    if not trades:
        return Decimal("0")
    winners = sum(1 for t in trades if t.pnl > 0)
    return Decimal(str(winners)) / Decimal(str(len(trades))) * Decimal("100")


def profit_factor(trades: list[TradeResult]) -> Decimal:
    """Gross profit / gross loss."""
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
    if gross_loss == 0:
        return Decimal("0") if gross_profit == 0 else Decimal("999")
    return gross_profit / gross_loss


def avg_trade_pnl(trades: list[TradeResult]) -> Decimal:
    if not trades:
        return Decimal("0")
    return sum(t.pnl for t in trades) / Decimal(str(len(trades)))


def avg_win(trades: list[TradeResult]) -> Decimal:
    winners = [t for t in trades if t.pnl > 0]
    if not winners:
        return Decimal("0")
    return sum(t.pnl for t in winners) / Decimal(str(len(winners)))


def avg_loss(trades: list[TradeResult]) -> Decimal:
    losers = [t for t in trades if t.pnl <= 0]
    if not losers:
        return Decimal("0")
    return sum(t.pnl for t in losers) / Decimal(str(len(losers)))


def largest_win(trades: list[TradeResult]) -> Decimal:
    if not trades:
        return Decimal("0")
    return max(t.pnl for t in trades)


def largest_loss(trades: list[TradeResult]) -> Decimal:
    if not trades:
        return Decimal("0")
    return min(t.pnl for t in trades)


def avg_bars_held(trades: list[TradeResult]) -> Decimal:
    if not trades:
        return Decimal("0")
    return Decimal(str(sum(t.bars_held for t in trades))) / Decimal(str(len(trades)))


def total_commission(trades: list[TradeResult]) -> Decimal:
    return sum(t.commission for t in trades)


def expectancy(trades: list[TradeResult]) -> Decimal:
    """Mathematical expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)."""
    if not trades:
        return Decimal("0")
    wr = win_rate(trades) / Decimal("100")
    lr = Decimal("1") - wr
    aw = avg_win(trades)
    al = abs(avg_loss(trades))
    return wr * aw - lr * al


def recovery_factor(
    equity_curve: list[EquityPoint], initial_capital: Decimal
) -> Decimal:
    """Total return / max drawdown."""
    ret = total_return(equity_curve, initial_capital)
    mdd = max_drawdown(equity_curve)
    if mdd == 0:
        return Decimal("0")
    return ret / mdd


def _equity_returns(equity_curve: list[EquityPoint]) -> list[Decimal]:
    """Compute bar-to-bar returns from equity curve."""
    if len(equity_curve) < 2:
        return []
    returns: list[Decimal] = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1].equity
        curr = equity_curve[i].equity
        if prev > 0:
            returns.append((curr - prev) / prev)
        else:
            returns.append(Decimal("0"))
    return returns


def _std(values: list[Decimal]) -> Decimal:
    """Standard deviation of a list of Decimal values."""
    if len(values) < 2:
        return Decimal("0")
    mean = sum(values) / Decimal(str(len(values)))
    variance = sum((v - mean) ** 2 for v in values) / Decimal(str(len(values)))
    return decimal_sqrt(variance)
