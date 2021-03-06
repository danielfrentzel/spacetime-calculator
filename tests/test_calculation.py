import pytest
from hour_calculator import HourCalculator

valid_calcs = [
    ('oh 1-2', ({
        'oh': 1.0,
        '$total': 1.0
    }, [])),
    ('a 8-8:30, 9-9:30, 11-1, 1:42-3:12, 4:12-6\n b 8:30-9, 9:30-11, 1-1:42, 3:12-4:12', ({
        'a': 6.3,
        'b': 3.7,
        '$total': 10.0
    }, [])),
    ('a 8-8.5, 9-9.5, 11-1, 1.7-3.2, 4.2-6\n b 8.5-9, 9.5-11, 1-1.7, 3.2-4.2', ({
        'a': 6.3,
        'b': 3.7,
        '$total': 10.0
    }, [])),
    ('a 4:30-20:30', ({
        'a': 16.0,
        '$total': 16.0
    }, [])),
    ('a 7:15-8p, 10-12', ({
        'a': 14.75,
        '$total': 14.8
    }, [['20:00', '22:00', '2.0']])),
    ('a 12am-2:30, 8-8pm', ({
        'a': 14.5,
        '$total': 14.5
    }, [['2:30', '8:00', '5.5']])),
    ('a 4:30-20:30', ({
        'a': 16.0,
        '$total': 16.0
    }, [])),
    ('a 0-0:34, 7:10-6p', ({
        'a': 11.4,
        '$total': 11.4
    }, [['0:34', '7:10', '6.6']])),
    ('a 12a-2:30, 7:30-8p, 9:30-12', ({
        'a': 17.5,
        '$total': 17.5
    }, [['2:30', '7:30', '5.0'], ['20:00', '21:30', '1.5']])),
]

invalid_calcs = [('a 7:50-8:15\n b 8:15-8:36\n c 8:36-11:10, 12-6:33\n a 11:10-12',
                  'Repeated identifier: a. Combine hours or use unique identifiers.')]


@pytest.fixture
def hour_calculator():
    return HourCalculator


@pytest.mark.parametrize('hours, expected', valid_calcs)
def test_valid_calcs(hour_calculator, hours, expected):
    assert hour_calculator(hours).calculate() == expected


@pytest.mark.parametrize('hours, exception', invalid_calcs)
def test_invalid_calcs(hour_calculator, hours, exception):
    try:
        hour_calculator(hours).calculate()
    except Exception as e:
        assert str(e) == exception


def test_valid_calc_break(hour_calculator):
    hours = 'c 8-12, 4-5\n\
             oh 12-4\n\
             other 18-9'

    output = hour_calculator(hours).calculate()
    assert output == ({'c': 5.0, 'oh': 4.0, 'other': 3.0, '$total': 12.0}, [['17:00', '18:00', '1.0']])


def test_valid_calc_breaks(hour_calculator):
    hours = 'c 8-11, 4-5\n\
             oh 12-4\n\
             other 18-9'

    output = hour_calculator(hours).calculate()
    assert output == ({
        'c': 4.0,
        'oh': 4.0,
        'other': 3.0,
        '$total': 11.0
    }, [['11:00', '12:00', '1.0'], ['17:00', '18:00', '1.0']])


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
        assert output == ({'$total': 12.0, 'a': 5.0, 'b': 7.0}, [['12:00', '13:00', '1.0']])
    except RuntimeError:
        assert not ordered


@pytest.mark.parametrize('ordered', [True, False])
def test_break_disagree(ordered, hour_calculator):
    hours = 'a 8-10\n\
             b 10-1, 2-6\n\
             c 7-8'

    output = hour_calculator(hours).calculate(ordered=ordered)
    if ordered:
        assert output == ({
            'a': 2.0,
            'b': 7.0,
            'c': 1.0,
            '$total': 10.0
        }, [['13:00', '14:00', '1.0'], ['18:00', '19:00', '1.0']])
    else:
        assert output == ({'a': 2.0, 'b': 7.0, 'c': 1.0, '$total': 10.0}, [['13:00', '14:00', '1.0']])


@pytest.mark.parametrize('ordered', [True, False])
def test_disagree(ordered, hour_calculator):
    hours = 'a 8-10\n\
             c 1-2\n\
             b 10-1, 2-6'

    output = hour_calculator(hours).calculate(ordered=ordered)
    if ordered:
        assert output == ({
            'a': 2.0,
            'c': 1.0,
            'b': 13.0,
            '$total': 16.0
        }, [['10:00', '13:00', '3.0'], ['14:00', '22:00', '8.0'], ['13:00', '14:00', '1.0']])
    else:
        assert output == ({
            'a': 2.0,
            'c': 1.0,
            'b': 7.0,
            '$total': 10.0
        }, [['2:00', '8:00', '6.0'], ['13:00', '14:00', '1.0']])


"""
Test Cases

a 8-10
b 10-1, 2-6
c 1-1.1

a 8-10
c 1-1.5
b 10-1, 2-6

a 8-10
c 1-2
b 10-1, 2-6

a 8-10
c 13-1.5
b 10-1, 2-6

both fail
a 8-10
b 1-1:30
c 10-12
d 6-9

"""
