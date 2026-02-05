"""Equity curve analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from finsaas.engine.portfolio import EquityPoint
from finsaas.strategy.builtins.math_funcs import sqrt as decimal_sqrt


@dataclass
class DrawdownInfo:
    """Information about a drawdown period."""

    peak_equity: Decimal
    trough_equity: Decimal
    drawdown_amount: Decimal
    drawdown_pct: Decimal
    peak_bar: int
    trough_bar: int
    recovery_bar: int | None
    duration_bars: int


@dataclass
class EquityAnalysis:
    """Comprehensive equity curve analysis."""

    initial_equity: Decimal
    final_equity: Decimal
    peak_equity: Decimal
    min_equity: Decimal
    total_bars: int
    max_drawdown: DrawdownInfo | None
    top_drawdowns: list[DrawdownInfo]
    avg_equity: Decimal
    equity_std: Decimal


def analyze_equity(
    equity_curve: list[EquityPoint], initial_capital: Decimal
) -> EquityAnalysis:
    """Perform comprehensive equity curve analysis."""
    if not equity_curve:
        return EquityAnalysis(
            initial_equity=initial_capital, final_equity=initial_capital,
            peak_equity=initial_capital, min_equity=initial_capital,
            total_bars=0, max_drawdown=None, top_drawdowns=[],
            avg_equity=initial_capital, equity_std=Decimal("0"),
        )

    equities = [p.equity for p in equity_curve]

    # Find all drawdowns
    drawdowns = _find_drawdowns(equity_curve)
    drawdowns.sort(key=lambda d: d.drawdown_pct, reverse=True)

    avg = sum(equities) / Decimal(str(len(equities)))
    variance = sum((e - avg) ** 2 for e in equities) / Decimal(str(len(equities)))

    return EquityAnalysis(
        initial_equity=initial_capital,
        final_equity=equities[-1],
        peak_equity=max(equities),
        min_equity=min(equities),
        total_bars=len(equity_curve),
        max_drawdown=drawdowns[0] if drawdowns else None,
        top_drawdowns=drawdowns[:5],
        avg_equity=avg,
        equity_std=decimal_sqrt(variance),
    )


def _find_drawdowns(equity_curve: list[EquityPoint]) -> list[DrawdownInfo]:
    """Find all drawdown periods in the equity curve."""
    if not equity_curve:
        return []

    drawdowns: list[DrawdownInfo] = []
    peak = equity_curve[0].equity
    peak_bar = 0
    trough = peak
    trough_bar = 0
    in_drawdown = False

    for i, point in enumerate(equity_curve):
        if point.equity >= peak:
            # New high - if we were in drawdown, record it
            if in_drawdown and peak > 0:
                dd_pct = ((peak - trough) / peak) * Decimal("100")
                if dd_pct > Decimal("0.01"):  # Ignore tiny drawdowns
                    drawdowns.append(DrawdownInfo(
                        peak_equity=peak,
                        trough_equity=trough,
                        drawdown_amount=peak - trough,
                        drawdown_pct=dd_pct,
                        peak_bar=peak_bar,
                        trough_bar=trough_bar,
                        recovery_bar=i,
                        duration_bars=i - peak_bar,
                    ))
            peak = point.equity
            peak_bar = i
            trough = peak
            trough_bar = i
            in_drawdown = False
        else:
            in_drawdown = True
            if point.equity < trough:
                trough = point.equity
                trough_bar = i

    # Handle ongoing drawdown at end
    if in_drawdown and peak > 0:
        dd_pct = ((peak - trough) / peak) * Decimal("100")
        if dd_pct > Decimal("0.01"):
            drawdowns.append(DrawdownInfo(
                peak_equity=peak,
                trough_equity=trough,
                drawdown_amount=peak - trough,
                drawdown_pct=dd_pct,
                peak_bar=peak_bar,
                trough_bar=trough_bar,
                recovery_bar=None,
                duration_bars=len(equity_curve) - peak_bar,
            ))

    return drawdowns
