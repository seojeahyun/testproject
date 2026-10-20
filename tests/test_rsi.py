from bot.rsi import compute_rsi


def test_all_up_is_100():
    assert compute_rsi(list(range(1, 30)), 14) == 100.0


def test_all_down_is_0():
    assert compute_rsi(list(range(30, 1, -1)), 14) < 1


def test_wilder_reference():
    # Wilder 교과서 예제 종가
    closes = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
              45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64]
    assert abs(compute_rsi(closes, 14) - 57.97) < 0.2


def test_insufficient_data():
    assert compute_rsi([1, 2, 3], 14) is None
