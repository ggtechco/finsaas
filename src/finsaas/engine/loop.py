"""EventLoop - bar-by-bar simulation engine.

Implements the core simulation loop:
1. Commit series (finalize previous bar values)
2. Update context (OHLCV built-in series)
3. Process pending orders (no look-ahead bias)
4. Call strategy.on_bar()
5. Collect new orders -> send to broker
6. Record equity
"""

from __future__ import annotations

import structlog
from decimal import Decimal

from finsaas.core.context import BarContext
from finsaas.core.types import OHLCV, OrderAction, SymbolInfo, Timeframe
from finsaas.data.feed import DataFeed
from finsaas.engine.broker import SimulatedBroker
from finsaas.engine.commission import CommissionModel
from finsaas.engine.order import Order
from finsaas.engine.portfolio import Portfolio
from finsaas.engine.slippage import SlippageModel

logger = structlog.get_logger()


class EventLoop:
    """Core bar-by-bar simulation loop.

    Orchestrates the interaction between DataFeed, BarContext,
    SimulatedBroker, Portfolio, and Strategy.
    """

    def __init__(
        self,
        feed: DataFeed,
        symbol_info: SymbolInfo,
        timeframe: Timeframe,
        initial_capital: Decimal = Decimal("10000"),
        commission_model: CommissionModel | None = None,
        slippage_model: SlippageModel | None = None,
        max_bars_back: int = 5000,
    ) -> None:
        self._feed = feed
        self._context = BarContext(
            symbol_info=symbol_info,
            timeframe=timeframe,
            max_bars_back=max_bars_back,
        )
        self._broker = SimulatedBroker(
            commission_model=commission_model,
            slippage_model=slippage_model,
        )
        self._portfolio = Portfolio(initial_capital=initial_capital)
        self._order_queue: list[tuple[Order, OrderAction]] = []
        self._action_map: dict[str, OrderAction] = {}
        self._bar_count = 0

    @property
    def context(self) -> BarContext:
        return self._context

    @property
    def broker(self) -> SimulatedBroker:
        return self._broker

    @property
    def portfolio(self) -> Portfolio:
        return self._portfolio

    def submit_order(self, order: Order, action: OrderAction) -> None:
        """Queue an order from the strategy. Will be sent to broker after on_bar()."""
        self._order_queue.append((order, action))

    def run(self, strategy: object) -> None:
        """Run the full simulation loop.

        Args:
            strategy: A Strategy instance with on_init() and on_bar() methods.
        """
        from finsaas.strategy.base import Strategy

        strat: Strategy = strategy  # type: ignore[assignment]

        # Initialize strategy
        strat._bind(self)
        strat.on_init()

        bars = list(self._feed)
        total_bars = len(bars)
        logger.info("simulation_start", total_bars=total_bars, symbol=self._feed.symbol)

        for bar_index, bar in enumerate(bars):
            self._process_bar(strat, bar, bar_index)

        # Close all positions at the end
        if bars:
            last_bar = bars[-1]
            self._portfolio.close_all_positions(
                last_bar.close, last_bar.timestamp, len(bars) - 1
            )

        self._bar_count = total_bars
        logger.info(
            "simulation_complete",
            total_bars=total_bars,
            total_trades=len(self._portfolio.trade_results),
            final_equity=str(self._portfolio.equity(bars[-1].close) if bars else "0"),
        )

    def _process_bar(self, strategy: object, bar: OHLCV, bar_index: int) -> None:
        """Process a single bar through the simulation pipeline."""
        from finsaas.strategy.base import Strategy

        strat: Strategy = strategy  # type: ignore[assignment]

        # Step 1: Commit all series from previous bar
        if bar_index > 0:
            self._context.commit_all()

        # Step 2: Update context with new bar data
        self._context.update(bar, bar_index)

        # Step 3: Process pending orders (from previous bar's on_bar)
        fills = self._broker.process_bar(bar, bar_index)
        for fill in fills:
            action = self._action_map.pop(fill.order_id, OrderAction.ENTRY)
            self._portfolio.process_fill(fill, action, bar_index)

        # Step 4: Call strategy.on_bar()
        try:
            strat.on_bar(self._context)
        except Exception:
            self._context.rollback_all()
            logger.exception("strategy_error", bar_index=bar_index)
            raise

        # Step 5: Send queued orders to broker
        for order, action in self._order_queue:
            order.created_bar = bar_index
            order.created_at = bar.timestamp
            self._broker.submit_order(order)
            self._action_map[order.id] = action
        self._order_queue.clear()

        # Step 6: Record equity
        self._portfolio.record_equity(bar, bar_index)
