import pytest
from hour_calculator import HourCalculator


@pytest.fixture
def hour_calculator():
    return HourCalculator


def test_valid_calc1(hour_calculator):
    hours = 'oh 1-2'
    output = hour_calculator(hours).calculate()
    assert output == ({'oh': 1.0, '$total': 1.0}, [])


def test_valid_calc2(hour_calculator):
    hours = 'oh 8-8:30, 9-9:30, 11-1, 1:42-3:12, 4:12-6\n\
             c 8:30-9, 9:30-11, 1-1:42, 3:12-4:12'

    output = hour_calculator(hours).calculate()
    assert output == ({'oh': 6.3, 'c': 3.7, '$total': 10.0}, [])


def test_valid_calc3(hour_calculator):
    hours = 'oh 8-8.5, 9-9.5, 11-1, 1.7-3.2, 4.2-6\n\
             c 8.5-9, 9.5-11, 1-1.7, 3.2-4.2'

    output = hour_calculator(hours).calculate()
    assert output == ({'oh': 6.3, 'c': 3.7, '$total': 10.0}, [])


def test_valid_calc4(hour_calculator):
    hours = 'c 8-12, 4-5\n\
             oh 12-4\n\
             other 18-9'

    output = hour_calculator(hours).calculate()
    assert output == ({'c': 5.0, 'oh': 4.0, 'other': 3.0, '$total': 12.0}, [['5:00', '6:00', '1.0']])


@pytest.mark.parametrize('ordered', [True, False])
def test_unordered_only(ordered, hour_calculator):
    hours = 'b 9-8\n\
             a 7-8'

    try:
        output = hour_calculator(hours).calculate(ordered=ordered)
        assert output == ({'$total': 12.0, 'a': 1.0, 'b': 11.0}, [['8:00', '9:00', '1.0']])
    except RuntimeError:
        assert ordered


@pytest.mark.parametrize('ordered', [True, False])
def test_ordered_only(ordered, hour_calculator):
    hours = 'a 7-12\n\
             b 1-8'

    try:
        output = hour_calculator(hours).calculate(ordered=ordered)
        assert output == ({'$total': 12.0, 'a': 5.0, 'b': 7.0}, [['12:00', '1:00', '1.0']])
    except RuntimeError:
        assert not ordered
