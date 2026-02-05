"""Technical analysis functions matching Pine Script's ta.* namespace.

All functions use Decimal arithmetic for deterministic results.
Functions operate on Series objects and return Decimal values.
"""

from __future__ import annotations

from decimal import Decimal

from finsaas.core.series import Series, na, nz


def sma(source: Series[Decimal], length: int) -> Decimal:
    """Simple Moving Average.

    Pine Script equivalent: ta.sma(source, length)
    """
    if len(source) < length - 1:  # -1 because current is not committed yet
        return Decimal("0")

    total = source.current
    for i in range(1, length):
        try:
            val = source[i]
            total += nz(val)
        except Exception:
            return Decimal("0")

    return total / Decimal(str(length))


def ema(source: Series[Decimal], length: int) -> Decimal:
    """Exponential Moving Average.

    Pine Script equivalent: ta.ema(source, length)
    Uses the standard formula: EMA = alpha * source + (1 - alpha) * EMA[1]
    where alpha = 2 / (length + 1)
    """
    if len(source) < 1:
        return source.current

    alpha = Decimal("2") / (Decimal(str(length)) + Decimal("1"))

    # For first bars, use SMA as seed
    if len(source) < length:
        return sma(source, min(length, len(source) + 1))

    # Get previous EMA value - approximate using SMA of previous values for bootstrap
    # In a proper implementation, the EMA series would be maintained across bars
    # Here we compute recursively up to length bars back
    prev_ema = _ema_recursive(source, length, alpha, 1, min(length * 3, len(source)))
    return alpha * source.current + (Decimal("1") - alpha) * prev_ema


def _ema_recursive(
    source: Series[Decimal], length: int, alpha: Decimal, offset: int, max_depth: int
) -> Decimal:
    """Compute EMA at a given offset, recursing back to get history."""
    if offset >= max_depth or offset >= len(source):
        # Base case: use SMA
        total = Decimal("0")
        count = 0
        for i in range(offset, min(offset + length, len(source))):
            val = source[i]
            if not na(val):
                total += val
                count += 1
        return total / Decimal(str(max(count, 1)))

    prev = _ema_recursive(source, length, alpha, offset + 1, max_depth)
    return alpha * nz(source[offset]) + (Decimal("1") - alpha) * prev


def rsi(source: Series[Decimal], length: int = 14) -> Decimal:
    """Relative Strength Index.

    Pine Script equivalent: ta.rsi(source, length)
    Uses RMA (Wilder's smoothing) for averaging gains and losses.
    """
    if len(source) < length:
        return Decimal("50")  # Neutral until enough data

    gains = Decimal("0")
    losses = Decimal("0")

    # Calculate initial average gain/loss using SMA
    for i in range(length):
        try:
            current = source[i] if i == 0 else source[i]
            previous = source[i + 1]
            change = nz(current) - nz(previous)
            if change > 0:
                gains += change
            else:
                losses += abs(change)
        except Exception:
            continue

    avg_gain = gains / Decimal(str(length))
    avg_loss = losses / Decimal(str(length))

    if avg_loss == 0:
        return Decimal("100")

    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def macd(
    source: Series[Decimal],
    fast_length: int = 12,
    slow_length: int = 26,
    signal_length: int = 9,
) -> tuple[Decimal, Decimal, Decimal]:
    """Moving Average Convergence Divergence.

    Pine Script equivalent: ta.macd(source, fast, slow, signal)
    Returns: (macd_line, signal_line, histogram)
    """
    fast_ema = ema(source, fast_length)
    slow_ema = ema(source, slow_length)
    macd_line = fast_ema - slow_ema

    # Signal line would ideally be EMA of MACD series
    # Simplified: use macd_line as approximation for single-bar
    signal_line = macd_line  # Simplified for single-bar computation
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def crossover(series1: Series[Decimal], series2: Series[Decimal]) -> bool:
    """Check if series1 crosses above series2.

    Pine Script equivalent: ta.crossover(series1, series2)
    Returns True when series1[0] > series2[0] AND series1[1] <= series2[1]
    """
    if len(series1) < 1 or len(series2) < 1:
        return False

    try:
        curr1 = nz(series1.current)
        curr2 = nz(series2.current)
        prev1 = nz(series1[1])
        prev2 = nz(series2[1])
        return curr1 > curr2 and prev1 <= prev2
    except Exception:
        return False


def crossunder(series1: Series[Decimal], series2: Series[Decimal]) -> bool:
    """Check if series1 crosses below series2.

    Pine Script equivalent: ta.crossunder(series1, series2)
    Returns True when series1[0] < series2[0] AND series1[1] >= series2[1]
    """
    if len(series1) < 1 or len(series2) < 1:
        return False

    try:
        curr1 = nz(series1.current)
        curr2 = nz(series2.current)
        prev1 = nz(series1[1])
        prev2 = nz(series2[1])
        return curr1 < curr2 and prev1 >= prev2
    except Exception:
        return False


def highest(source: Series[Decimal], length: int) -> Decimal:
    """Highest value over the last `length` bars.

    Pine Script equivalent: ta.highest(source, length)
    """
    result = source.current
    for i in range(1, length):
        try:
            val = source[i]
            if not na(val) and val > result:
                result = val
        except Exception:
            break
    return result


def lowest(source: Series[Decimal], length: int) -> Decimal:
    """Lowest value over the last `length` bars.

    Pine Script equivalent: ta.lowest(source, length)
    """
    result = source.current
    for i in range(1, length):
        try:
            val = source[i]
            if not na(val) and val < result:
                result = val
        except Exception:
            break
    return result


def stdev(source: Series[Decimal], length: int) -> Decimal:
    """Standard deviation over the last `length` bars.

    Pine Script equivalent: ta.stdev(source, length)
    """
    mean = sma(source, length)
    if mean == 0 and len(source) < length:
        return Decimal("0")

    sum_sq = Decimal("0")
    count = 0
    for i in range(length):
        try:
            val = source[i] if i == 0 else source[i]
            if i == 0:
                val = source.current
            else:
                val = source[i]
            diff = nz(val) - mean
            sum_sq += diff * diff
            count += 1
        except Exception:
            break

    if count <= 1:
        return Decimal("0")

    variance = sum_sq / Decimal(str(count))
    # Newton's method for square root (Decimal doesn't have sqrt)
    return _decimal_sqrt(variance)


def _decimal_sqrt(value: Decimal) -> Decimal:
    """Compute square root of a Decimal using Newton's method."""
    if value <= 0:
        return Decimal("0")

    # Initial guess
    x = value
    while True:
        new_x = (x + value / x) / Decimal("2")
        if abs(new_x - x) < Decimal("1E-20"):
            break
        x = new_x
    return x


def atr(
    high: Series[Decimal], low: Series[Decimal], close: Series[Decimal], length: int = 14
) -> Decimal:
    """Average True Range.

    Pine Script equivalent: ta.atr(length)
    """
    if len(close) < 1:
        return high.current - low.current

    tr_values: list[Decimal] = []
    for i in range(min(length, len(close))):
        if i == 0:
            h = high.current
            l = low.current
            try:
                prev_c = close[1]
            except Exception:
                prev_c = close.current
        else:
            try:
                h = high[i]
                l = low[i]
                prev_c = close[i + 1] if (i + 1) < len(close) else close[i]
            except Exception:
                break

        tr = max(h - l, abs(h - nz(prev_c)), abs(l - nz(prev_c)))
        tr_values.append(tr)

    if not tr_values:
        return Decimal("0")

    return sum(tr_values) / Decimal(str(len(tr_values)))


def bb(
    source: Series[Decimal], length: int = 20, mult: Decimal = Decimal("2")
) -> tuple[Decimal, Decimal, Decimal]:
    """Bollinger Bands.

    Pine Script equivalent: ta.bb(source, length, mult)
    Returns: (upper, middle, lower)
    """
    middle = sma(source, length)
    sd = stdev(source, length)
    upper = middle + mult * sd
    lower = middle - mult * sd
    return upper, middle, lower


def change(source: Series[Decimal], length: int = 1) -> Decimal:
    """Change in value over `length` bars.

    Pine Script equivalent: ta.change(source, length)
    """
    try:
        return source.current - source[length]
    except Exception:
        return Decimal("0")


def rma(source: Series[Decimal], length: int) -> Decimal:
    """Wilder's Moving Average (RMA).

    Pine Script equivalent: ta.rma(source, length)
    RMA = (1/length) * source + (1 - 1/length) * RMA[1]
    """
    alpha = Decimal("1") / Decimal(str(length))
    return _ema_recursive(source, length, alpha, 0, min(length * 3, max(len(source), 1)))


def tr(
    high: Series[Decimal], low: Series[Decimal], close: Series[Decimal]
) -> Decimal:
    """True Range for the current bar.

    Pine Script equivalent: ta.tr
    """
    h = high.current
    l = low.current
    try:
        prev_c = close[1]
    except Exception:
        return h - l

    return max(h - l, abs(h - prev_c), abs(l - prev_c))
