"""Technical analysis functions matching Pine Script's ta.* namespace.

All functions use Decimal arithmetic for deterministic results.
Functions operate on Series objects and return Decimal values.
"""

from __future__ import annotations

from decimal import Decimal

from typing import Optional

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


# ── Faz 1: Aliases and Simple Compositions ───────────────────────────


def smma(source: Series[Decimal], length: int) -> Decimal:
    """Smoothed Moving Average (identical to RMA in Pine Script).

    Pine Script equivalent: ta.smma(source, length)
    """
    return rma(source, length)


def cross(series1: Series[Decimal], series2: Series[Decimal]) -> bool:
    """Check if series1 crosses series2 in either direction.

    Pine Script equivalent: ta.cross(series1, series2)
    """
    return crossover(series1, series2) or crossunder(series1, series2)


def mom(source: Series[Decimal], length: int = 10) -> Decimal:
    """Momentum: difference between current and `length` bars ago.

    Pine Script equivalent: ta.mom(source, length)
    """
    return change(source, length)


def roc(source: Series[Decimal], length: int = 10) -> Decimal:
    """Rate of Change (percentage).

    Pine Script equivalent: ta.roc(source, length)
    """
    try:
        prev = source[length]
    except Exception:
        return Decimal("0")
    if prev == 0:
        return Decimal("0")
    return Decimal("100") * (source.current - prev) / prev


# ── Faz 2: Moving Averages ───────────────────────────────────────────


def wma(source: Series[Decimal], length: int) -> Decimal:
    """Weighted Moving Average.

    Pine Script equivalent: ta.wma(source, length)
    Weight for bar i (0=current) is (length - i).
    """
    if len(source) < length - 1:
        return Decimal("0")

    weighted_sum = Decimal("0")
    weight_sum = Decimal("0")
    for i in range(length):
        w = Decimal(str(length - i))
        try:
            val = source.current if i == 0 else source[i]
        except Exception:
            return Decimal("0")
        weighted_sum += w * nz(val)
        weight_sum += w
    return weighted_sum / weight_sum


def hma(source: Series[Decimal], length: int) -> Decimal:
    """Hull Moving Average (simplified).

    Pine Script equivalent: ta.hma(source, length)
    HMA = 2 * WMA(n/2) - WMA(n)
    """
    half_len = max(length // 2, 1)
    wma_half = wma(source, half_len)
    wma_full = wma(source, length)
    return Decimal("2") * wma_half - wma_full


def vwma(source: Series[Decimal], volume: Series[Decimal], length: int) -> Decimal:
    """Volume-Weighted Moving Average.

    Pine Script equivalent: ta.vwma(source, length)
    """
    if len(source) < length - 1 or len(volume) < length - 1:
        return Decimal("0")

    pv_sum = Decimal("0")
    v_sum = Decimal("0")
    for i in range(length):
        try:
            p = source.current if i == 0 else source[i]
            v = volume.current if i == 0 else volume[i]
        except Exception:
            return Decimal("0")
        pv_sum += nz(p) * nz(v)
        v_sum += nz(v)

    if v_sum == 0:
        return Decimal("0")
    return pv_sum / v_sum


# ── Faz 3: Stochastic and Pivot Points ───────────────────────────────


def stoch(
    source: Series[Decimal],
    high_s: Series[Decimal],
    low_s: Series[Decimal],
    length: int,
) -> Decimal:
    """Stochastic %K.

    Pine Script equivalent: ta.stoch(source, high, low, length)
    100 * (source - lowest_low) / (highest_high - lowest_low)
    """
    hi = highest(high_s, length)
    lo = lowest(low_s, length)
    diff = hi - lo
    if diff == 0:
        return Decimal("0")
    return Decimal("100") * (source.current - lo) / diff


def pivothigh(source: Series[Decimal], leftbars: int, rightbars: int) -> Optional[Decimal]:
    """Pivot High detection.

    Pine Script equivalent: ta.pivothigh(source, leftbars, rightbars)
    Returns the pivot value or None. The pivot is confirmed `rightbars` bars after
    the actual peak — no look-ahead bias.
    """
    # The candidate bar is at offset `rightbars` from current
    needed = leftbars + rightbars
    if len(source) < needed:
        return None

    try:
        candidate = source[rightbars]
    except Exception:
        return None

    # Check right side: candidate must be >= all bars from [0..rightbars-1]
    for i in range(rightbars):
        try:
            val = source.current if i == 0 else source[i]
            if nz(val) > candidate:
                return None
        except Exception:
            return None

    # Check left side: candidate must be >= all bars from [rightbars+1..rightbars+leftbars]
    for i in range(rightbars + 1, rightbars + leftbars + 1):
        try:
            val = source[i]
            if nz(val) > candidate:
                return None
        except Exception:
            return None

    return candidate


def pivotlow(source: Series[Decimal], leftbars: int, rightbars: int) -> Optional[Decimal]:
    """Pivot Low detection.

    Pine Script equivalent: ta.pivotlow(source, leftbars, rightbars)
    Returns the pivot value or None.
    """
    needed = leftbars + rightbars
    if len(source) < needed:
        return None

    try:
        candidate = source[rightbars]
    except Exception:
        return None

    for i in range(rightbars):
        try:
            val = source.current if i == 0 else source[i]
            if nz(val) < candidate:
                return None
        except Exception:
            return None

    for i in range(rightbars + 1, rightbars + leftbars + 1):
        try:
            val = source[i]
            if nz(val) < candidate:
                return None
        except Exception:
            return None

    return candidate


# ── Faz 4: DMI/ADX and Linear Regression ─────────────────────────────


def dmi(
    high_s: Series[Decimal],
    low_s: Series[Decimal],
    close_s: Series[Decimal],
    di_length: int = 14,
    adx_smoothing: int = 14,
) -> tuple[Decimal, Decimal, Decimal]:
    """Directional Movement Index.

    Pine Script equivalent: ta.dmi(di_length, adx_smoothing)
    Returns: (plus_di, minus_di, adx)
    """
    if len(high_s) < di_length + 1:
        return Decimal("0"), Decimal("0"), Decimal("0")

    plus_dm_sum = Decimal("0")
    minus_dm_sum = Decimal("0")
    tr_sum = Decimal("0")

    for i in range(di_length):
        try:
            h = high_s.current if i == 0 else high_s[i]
            l = low_s.current if i == 0 else low_s[i]
            prev_h = high_s[i + 1]
            prev_l = low_s[i + 1]
            prev_c = close_s[i + 1] if (i + 1) <= len(close_s) else close_s[i]
        except Exception:
            continue

        up_move = h - prev_h
        down_move = prev_l - l

        plus_dm = up_move if (up_move > down_move and up_move > 0) else Decimal("0")
        minus_dm = down_move if (down_move > up_move and down_move > 0) else Decimal("0")

        tr_val = max(h - l, abs(h - nz(prev_c)), abs(l - nz(prev_c)))

        plus_dm_sum += plus_dm
        minus_dm_sum += minus_dm
        tr_sum += tr_val

    if tr_sum == 0:
        return Decimal("0"), Decimal("0"), Decimal("0")

    plus_di = Decimal("100") * plus_dm_sum / tr_sum
    minus_di = Decimal("100") * minus_dm_sum / tr_sum

    di_sum = plus_di + minus_di
    if di_sum == 0:
        adx_val = Decimal("0")
    else:
        dx = Decimal("100") * abs(plus_di - minus_di) / di_sum
        adx_val = dx  # Simplified: single-period DX as ADX approximation

    return plus_di, minus_di, adx_val


def linreg(source: Series[Decimal], length: int, offset: int = 0) -> Decimal:
    """Linear Regression Value.

    Pine Script equivalent: ta.linreg(source, length, offset)
    Least squares fit y = mx + b evaluated at the most recent point minus offset.
    """
    if len(source) < length - 1:
        return Decimal("0")

    n = Decimal(str(length))
    sum_x = Decimal("0")
    sum_y = Decimal("0")
    sum_xy = Decimal("0")
    sum_x2 = Decimal("0")

    for i in range(length):
        x = Decimal(str(length - 1 - i))  # x=0 oldest, x=length-1 newest
        try:
            y = source.current if i == 0 else source[i]
        except Exception:
            return Decimal("0")
        y = nz(y)
        sum_x += x
        sum_y += y
        sum_xy += x * y
        sum_x2 += x * x

    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return sum_y / n

    m = (n * sum_xy - sum_x * sum_y) / denom
    b = (sum_y - m * sum_x) / n

    eval_x = Decimal(str(length - 1 - offset))
    return m * eval_x + b


# ── Faz 5: Tier 2 Oscillators and Volume ─────────────────────────────


def cci(source: Series[Decimal], length: int = 20) -> Decimal:
    """Commodity Channel Index.

    Pine Script equivalent: ta.cci(source, length)
    CCI = (source - SMA) / (0.015 * mean_deviation)
    """
    if len(source) < length - 1:
        return Decimal("0")

    mean = sma(source, length)

    # Mean deviation
    dev_sum = Decimal("0")
    for i in range(length):
        try:
            val = source.current if i == 0 else source[i]
        except Exception:
            return Decimal("0")
        dev_sum += abs(nz(val) - mean)

    mean_dev = dev_sum / Decimal(str(length))
    if mean_dev == 0:
        return Decimal("0")

    return (source.current - mean) / (Decimal("0.015") * mean_dev)


def mfi(
    high_s: Series[Decimal],
    low_s: Series[Decimal],
    close_s: Series[Decimal],
    volume_s: Series[Decimal],
    length: int = 14,
) -> Decimal:
    """Money Flow Index.

    Pine Script equivalent: ta.mfi(hlc3, length)
    RSI-like but uses typical_price * volume.
    """
    if len(close_s) < length:
        return Decimal("50")

    pos_flow = Decimal("0")
    neg_flow = Decimal("0")

    for i in range(length):
        try:
            h = high_s.current if i == 0 else high_s[i]
            l = low_s.current if i == 0 else low_s[i]
            c = close_s.current if i == 0 else close_s[i]
            v = volume_s.current if i == 0 else volume_s[i]
            prev_h = high_s[i + 1]
            prev_l = low_s[i + 1]
            prev_c = close_s[i + 1]
        except Exception:
            continue

        tp = (h + l + c) / Decimal("3")
        prev_tp = (prev_h + prev_l + prev_c) / Decimal("3")
        raw_mf = tp * nz(v)

        if tp > prev_tp:
            pos_flow += raw_mf
        else:
            neg_flow += raw_mf

    if neg_flow == 0:
        return Decimal("100")

    mf_ratio = pos_flow / neg_flow
    return Decimal("100") - Decimal("100") / (Decimal("1") + mf_ratio)


def wpr(
    high_s: Series[Decimal],
    low_s: Series[Decimal],
    close_s: Series[Decimal],
    length: int = 14,
) -> Decimal:
    """Williams %R.

    Pine Script equivalent: ta.wpr(length)
    -100 * (highest - close) / (highest - lowest)
    """
    hi = highest(high_s, length)
    lo = lowest(low_s, length)
    diff = hi - lo
    if diff == 0:
        return Decimal("0")
    return Decimal("-100") * (hi - close_s.current) / diff


def obv(close_s: Series[Decimal], volume_s: Series[Decimal]) -> Decimal:
    """On-Balance Volume.

    Pine Script equivalent: ta.obv
    Cumulative: if close > close[1] then +volume, else -volume.
    """
    result = Decimal("0")
    available = min(len(close_s), len(volume_s))

    for i in range(available):
        try:
            c = close_s[i]
            v = nz(volume_s[i])
            prev_c = close_s[i + 1]
        except Exception:
            break
        if c > prev_c:
            result += v
        elif c < prev_c:
            result -= v

    # Current bar
    try:
        c_cur = close_s.current
        c_prev = close_s[1]
        v_cur = nz(volume_s.current)
        if c_cur > c_prev:
            result += v_cur
        elif c_cur < c_prev:
            result -= v_cur
    except Exception:
        pass

    return result


def vwap(
    high_s: Series[Decimal],
    low_s: Series[Decimal],
    close_s: Series[Decimal],
    volume_s: Series[Decimal],
) -> Decimal:
    """Volume-Weighted Average Price.

    Pine Script equivalent: ta.vwap
    cumulative(typical_price * volume) / cumulative(volume)
    """
    tp_v_sum = Decimal("0")
    v_sum = Decimal("0")

    # Historical bars
    for i in range(len(close_s)):
        try:
            h = high_s[i]
            l = low_s[i]
            c = close_s[i]
            v = nz(volume_s[i])
        except Exception:
            break
        tp = (h + l + c) / Decimal("3")
        tp_v_sum += tp * v
        v_sum += v

    # Current bar
    try:
        tp_cur = (high_s.current + low_s.current + close_s.current) / Decimal("3")
        v_cur = nz(volume_s.current)
        tp_v_sum += tp_cur * v_cur
        v_sum += v_cur
    except Exception:
        pass

    if v_sum == 0:
        return Decimal("0")
    return tp_v_sum / v_sum


def cum(source: Series[Decimal]) -> Decimal:
    """Cumulative sum of all bars.

    Pine Script equivalent: ta.cum(source)
    """
    total = nz(source.current)
    # Add committed history (buffer), accessed via index 1, 2, ...
    for i in range(1, len(source) + 1):
        try:
            total += nz(source[i])
        except Exception:
            break
    return total


# ── Faz 6: Supertrend, Keltner, SAR ──────────────────────────────────


def kc(
    source: Series[Decimal],
    length: int,
    mult: Decimal,
    atr_length: int,
    high_s: Optional[Series[Decimal]] = None,
    low_s: Optional[Series[Decimal]] = None,
    close_s: Optional[Series[Decimal]] = None,
) -> tuple[Decimal, Decimal, Decimal]:
    """Keltner Channels.

    Pine Script equivalent: ta.kc(source, length, mult)
    Returns: (upper, middle, lower)
    middle = EMA(source, length), upper/lower = middle ± mult * ATR
    """
    middle = ema(source, length)
    if high_s is not None and low_s is not None and close_s is not None:
        atr_val = atr(high_s, low_s, close_s, atr_length)
    else:
        atr_val = atr(source, source, source, atr_length)
    upper = middle + mult * atr_val
    lower = middle - mult * atr_val
    return upper, middle, lower


def supertrend(
    high_s: Series[Decimal],
    low_s: Series[Decimal],
    close_s: Series[Decimal],
    factor: Decimal,
    atr_period: int,
) -> tuple[Decimal, int]:
    """Supertrend indicator.

    Pine Script equivalent: ta.supertrend(factor, atr_period)
    Returns: (value, direction) where direction is 1 (up/bullish) or -1 (down/bearish)
    """
    atr_val = atr(high_s, low_s, close_s, atr_period)
    hl2 = (high_s.current + low_s.current) / Decimal("2")

    upper_band = hl2 + factor * atr_val
    lower_band = hl2 - factor * atr_val

    # Simple direction: if close is above the mid, trend is up
    if close_s.current > hl2:
        return lower_band, 1
    else:
        return upper_band, -1


def sar(
    high_s: Series[Decimal],
    low_s: Series[Decimal],
    start: Decimal = Decimal("0.02"),
    inc: Decimal = Decimal("0.02"),
    max_val: Decimal = Decimal("0.2"),
) -> Decimal:
    """Parabolic SAR.

    Pine Script equivalent: ta.sar(start, inc, max)
    Simplified single-bar computation using available history.
    """
    if len(high_s) < 2:
        return low_s.current

    # Determine initial trend from recent bars
    try:
        prev_close_approx = (high_s[1] + low_s[1]) / Decimal("2")
        curr_close_approx = (high_s.current + low_s.current) / Decimal("2")
    except Exception:
        return low_s.current

    is_long = curr_close_approx >= prev_close_approx
    af = start

    if is_long:
        sar_val = low_s.current
        ep = high_s.current
        # Walk back through history to refine
        for i in range(1, min(len(high_s), 20)):
            try:
                lo = low_s[i]
                hi = high_s[i]
            except Exception:
                break
            if lo < sar_val:
                sar_val = lo
            if hi > ep:
                ep = hi
                af = min(af + inc, max_val)
        sar_val = sar_val + af * (ep - sar_val)
    else:
        sar_val = high_s.current
        ep = low_s.current
        for i in range(1, min(len(low_s), 20)):
            try:
                hi = high_s[i]
                lo = low_s[i]
            except Exception:
                break
            if hi > sar_val:
                sar_val = hi
            if lo < ep:
                ep = lo
                af = min(af + inc, max_val)
        sar_val = sar_val + af * (ep - sar_val)

    return sar_val


# ── Faz 7: Statistics and Utility ─────────────────────────────────────


def rising(source: Series[Decimal], length: int) -> bool:
    """Check if source has been rising for `length` bars.

    Pine Script equivalent: ta.rising(source, length)
    """
    for i in range(length):
        try:
            curr = source.current if i == 0 else source[i]
            prev = source[i + 1]
            if nz(curr) <= nz(prev):
                return False
        except Exception:
            return False
    return True


def falling(source: Series[Decimal], length: int) -> bool:
    """Check if source has been falling for `length` bars.

    Pine Script equivalent: ta.falling(source, length)
    """
    for i in range(length):
        try:
            curr = source.current if i == 0 else source[i]
            prev = source[i + 1]
            if nz(curr) >= nz(prev):
                return False
        except Exception:
            return False
    return True


def variance(source: Series[Decimal], length: int) -> Decimal:
    """Variance over the last `length` bars.

    Pine Script equivalent: ta.variance(source, length)
    """
    sd = stdev(source, length)
    return sd * sd


def median(source: Series[Decimal], length: int) -> Decimal:
    """Median value over the last `length` bars.

    Pine Script equivalent: ta.median(source, length)
    """
    if len(source) < length - 1:
        return Decimal("0")

    vals: list[Decimal] = []
    for i in range(length):
        try:
            val = source.current if i == 0 else source[i]
            vals.append(nz(val))
        except Exception:
            break

    if not vals:
        return Decimal("0")

    vals.sort()
    n = len(vals)
    if n % 2 == 1:
        return vals[n // 2]
    else:
        return (vals[n // 2 - 1] + vals[n // 2]) / Decimal("2")


def correlation(
    source1: Series[Decimal], source2: Series[Decimal], length: int
) -> Decimal:
    """Pearson correlation coefficient between two series.

    Pine Script equivalent: ta.correlation(source1, source2, length)
    """
    if len(source1) < length - 1 or len(source2) < length - 1:
        return Decimal("0")

    n = Decimal(str(length))
    sum_x = Decimal("0")
    sum_y = Decimal("0")
    sum_xy = Decimal("0")
    sum_x2 = Decimal("0")
    sum_y2 = Decimal("0")

    for i in range(length):
        try:
            x = source1.current if i == 0 else source1[i]
            y = source2.current if i == 0 else source2[i]
        except Exception:
            return Decimal("0")
        x = nz(x)
        y = nz(y)
        sum_x += x
        sum_y += y
        sum_xy += x * y
        sum_x2 += x * x
        sum_y2 += y * y

    num = n * sum_xy - sum_x * sum_y
    denom_sq = (n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)
    if denom_sq <= 0:
        return Decimal("0")

    denom = _decimal_sqrt(denom_sq)
    if denom == 0:
        return Decimal("0")
    return num / denom


def highestbars(source: Series[Decimal], length: int) -> int:
    """Bar offset to the highest value over the last `length` bars.

    Pine Script equivalent: ta.highestbars(source, length)
    Returns a negative offset (0 = current bar, -1 = one bar ago, etc.)
    """
    best_val = source.current
    best_idx = 0
    for i in range(1, length):
        try:
            val = source[i]
            if not na(val) and val > best_val:
                best_val = val
                best_idx = i
        except Exception:
            break
    return -best_idx


def lowestbars(source: Series[Decimal], length: int) -> int:
    """Bar offset to the lowest value over the last `length` bars.

    Pine Script equivalent: ta.lowestbars(source, length)
    Returns a negative offset.
    """
    best_val = source.current
    best_idx = 0
    for i in range(1, length):
        try:
            val = source[i]
            if not na(val) and val < best_val:
                best_val = val
                best_idx = i
        except Exception:
            break
    return -best_idx


def bbw(
    source: Series[Decimal], length: int = 20, mult: Decimal = Decimal("2")
) -> Decimal:
    """Bollinger Bands Width.

    Pine Script equivalent: ta.bbw(source, length, mult)
    (upper - lower) / middle
    """
    upper, middle, lower = bb(source, length, mult)
    if middle == 0:
        return Decimal("0")
    return (upper - lower) / middle


def kcw(
    source: Series[Decimal],
    length: int,
    mult: Decimal,
    atr_length: int,
    high_s: Optional[Series[Decimal]] = None,
    low_s: Optional[Series[Decimal]] = None,
    close_s: Optional[Series[Decimal]] = None,
) -> Decimal:
    """Keltner Channel Width.

    Pine Script equivalent: ta.kcw(source, length, mult)
    (upper - lower) / middle
    """
    upper, middle, lower = kc(source, length, mult, atr_length, high_s, low_s, close_s)
    if middle == 0:
        return Decimal("0")
    return (upper - lower) / middle


def barsince(condition: Series[bool]) -> int:
    """Number of bars since condition was last true.

    Pine Script equivalent: ta.barssince(condition)
    """
    try:
        if condition.current:
            return 0
    except Exception:
        pass

    for i in range(1, len(condition) + 1):
        try:
            if condition[i]:
                return i
        except Exception:
            break
    return -1


def valuewhen(
    condition: Series[bool], source: Series[Decimal], occurrence: int = 0
) -> Decimal:
    """Value of source when condition was true, `occurrence` times ago.

    Pine Script equivalent: ta.valuewhen(condition, source, occurrence)
    occurrence=0 means the most recent time condition was true.
    """
    count = 0
    # Check current
    try:
        if condition.current:
            if count == occurrence:
                return source.current
            count += 1
    except Exception:
        pass

    for i in range(1, min(len(condition), len(source)) + 1):
        try:
            if condition[i]:
                if count == occurrence:
                    return nz(source[i])
                count += 1
        except Exception:
            break
    return Decimal("0")
