"""Tests for Series[T] - the most critical class."""

from decimal import Decimal

import pytest

from finsaas.core.series import Series, fixnan, na, nz
from finsaas.core.errors import InsufficientDataError, SeriesIndexError


class TestSeriesBasic:
    """Basic Series operations."""

    def test_empty_series(self):
        s: Series[Decimal] = Series(name="test")
        assert len(s) == 0
        assert not bool(s)

    def test_set_and_get_current(self):
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("100")
        assert s.current == Decimal("100")
        assert bool(s)

    def test_commit_adds_to_buffer(self):
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("100")
        s.commit()
        assert len(s) == 1
        assert s[0] == Decimal("100")

    def test_multiple_commits(self):
        s: Series[Decimal] = Series(name="test")
        for i in range(5):
            s.current = Decimal(str(i * 10))
            s.commit()
        assert len(s) == 5
        assert s[0] == Decimal("40")  # Most recent
        assert s[4] == Decimal("0")   # Oldest

    def test_index_access(self):
        """Index 0 = current/latest, index 1 = previous, etc."""
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("10")
        s.commit()
        s.current = Decimal("20")
        s.commit()
        s.current = Decimal("30")
        s.commit()

        assert s[0] == Decimal("30")
        assert s[1] == Decimal("20")
        assert s[2] == Decimal("10")

    def test_current_overrides_index_zero(self):
        """When current is set but not committed, [0] returns current."""
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("10")
        s.commit()
        s.current = Decimal("99")
        assert s[0] == Decimal("99")  # Current (uncommitted)
        assert s[1] == Decimal("10")  # Previous committed

    def test_slice_access(self):
        s: Series[Decimal] = Series(name="test")
        for i in range(5):
            s.current = Decimal(str(i))
            s.commit()
        result = s[0:3]
        assert result == [Decimal("4"), Decimal("3"), Decimal("2")]

    def test_rollback(self):
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("100")
        s.commit()
        s.current = Decimal("999")
        s.rollback()
        assert len(s) == 1
        assert s[0] == Decimal("100")

    def test_commit_without_current_propagates_last(self):
        """If no value is set, commit propagates the last committed value."""
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("100")
        s.commit()
        s.commit()  # No current set
        assert len(s) == 2
        assert s[0] == Decimal("100")
        assert s[1] == Decimal("100")

    def test_max_bars_back(self):
        """Buffer should not exceed max_bars_back."""
        s: Series[Decimal] = Series(max_bars_back=3, name="test")
        for i in range(10):
            s.current = Decimal(str(i))
            s.commit()
        assert len(s) == 3
        assert s[0] == Decimal("9")
        assert s[2] == Decimal("7")


class TestSeriesErrors:
    """Error handling in Series."""

    def test_index_out_of_range(self):
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("100")
        s.commit()
        with pytest.raises(InsufficientDataError):
            _ = s[5]

    def test_negative_index(self):
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("100")
        s.commit()
        with pytest.raises(SeriesIndexError):
            _ = s[-1]

    def test_empty_series_current_raises(self):
        s: Series[Decimal] = Series(name="test")
        with pytest.raises(SeriesIndexError):
            _ = s.current


class TestSeriesHelpers:
    """Tests for na(), nz(), fixnan()."""

    def test_na_none(self):
        assert na(None) is True

    def test_na_decimal_nan(self):
        assert na(Decimal("NaN")) is True

    def test_na_regular_value(self):
        assert na(Decimal("100")) is False

    def test_nz_replaces_none(self):
        result = nz(None)
        assert result == Decimal("0")

    def test_nz_with_replacement(self):
        result = nz(None, Decimal("42"))
        assert result == Decimal("42")

    def test_nz_passes_through_value(self):
        result = nz(Decimal("100"))
        assert result == Decimal("100")

    def test_repr(self):
        s: Series[Decimal] = Series(name="close")
        s.current = Decimal("100")
        assert "close" in repr(s)
        assert "100" in repr(s)
