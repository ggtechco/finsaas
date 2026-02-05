"""Trade analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from finsaas.core.types import Side, TradeResult


@dataclass
class TradeAnalysis:
    """Aggregated trade analysis."""

    total_trades: int
    long_trades: int
    short_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    avg_pnl: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    largest_win: Decimal
    largest_loss: Decimal
    avg_bars_held: Decimal
    max_consecutive_wins: int
    max_consecutive_losses: int
    gross_profit: Decimal
    gross_loss: Decimal
    net_profit: Decimal


def analyze_trades(trades: list[TradeResult]) -> TradeAnalysis:
    """Perform comprehensive trade analysis."""
    if not trades:
        return TradeAnalysis(
            total_trades=0, long_trades=0, short_trades=0,
            winning_trades=0, losing_trades=0,
            win_rate=Decimal("0"), avg_pnl=Decimal("0"),
            avg_win=Decimal("0"), avg_loss=Decimal("0"),
            largest_win=Decimal("0"), largest_loss=Decimal("0"),
            avg_bars_held=Decimal("0"),
            max_consecutive_wins=0, max_consecutive_losses=0,
            gross_profit=Decimal("0"), gross_loss=Decimal("0"),
            net_profit=Decimal("0"),
        )

    winners = [t for t in trades if t.pnl > 0]
    losers = [t for t in trades if t.pnl <= 0]
    longs = [t for t in trades if t.side == Side.LONG]
    shorts = [t for t in trades if t.side == Side.SHORT]

    gross_profit = sum(t.pnl for t in winners)
    gross_loss = sum(t.pnl for t in losers)

    # Consecutive wins/losses
    max_consec_wins = 0
    max_consec_losses = 0
    current_wins = 0
    current_losses = 0
    for t in trades:
        if t.pnl > 0:
            current_wins += 1
            current_losses = 0
            max_consec_wins = max(max_consec_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            max_consec_losses = max(max_consec_losses, current_losses)

    n = len(trades)
    return TradeAnalysis(
        total_trades=n,
        long_trades=len(longs),
        short_trades=len(shorts),
        winning_trades=len(winners),
        losing_trades=len(losers),
        win_rate=Decimal(str(len(winners))) / Decimal(str(n)) * Decimal("100") if n > 0 else Decimal("0"),
        avg_pnl=sum(t.pnl for t in trades) / Decimal(str(n)),
        avg_win=sum(t.pnl for t in winners) / Decimal(str(len(winners))) if winners else Decimal("0"),
        avg_loss=sum(t.pnl for t in losers) / Decimal(str(len(losers))) if losers else Decimal("0"),
        largest_win=max((t.pnl for t in trades), default=Decimal("0")),
        largest_loss=min((t.pnl for t in trades), default=Decimal("0")),
        avg_bars_held=Decimal(str(sum(t.bars_held for t in trades))) / Decimal(str(n)),
        max_consecutive_wins=max_consec_wins,
        max_consecutive_losses=max_consec_losses,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_profit=gross_profit + gross_loss,
    )
