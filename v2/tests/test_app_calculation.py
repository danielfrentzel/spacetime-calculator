import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from calculator import process_input


class AppCalculator:

    def __init__(self, text):
        self.text = text

    def calculate(self, ordered=True, cli=False):
        return process_input(self.text, ordered=ordered)


@pytest.fixture
def hour_calculator():
    return AppCalculator


def meta(target_time=None, target_achieved_at=None, detected_ids=None):
    return {'target_time': target_time, 'target_achieved_at': target_achieved_at, 'detected_ids': detected_ids or []}


general_calcs = [
    ('oh 1-2', ({
        'oh': 1.0,
        '$total': 1.0
    }, [], meta())),
    ('a 8-8:30, 9-9:30, 11-1, 1:42-3:12, 4:12-6\n b 8:30-9, 9:30-11, 1-1:42, 3:12-4:12', ({
        'a': 6.3,
        'b': 3.7,
        '$total': 10.0
    }, [], meta())),
    ('a 8-8.5, 9-9.5, 11-1, 1.7-3.2, 4.2-6\n b 8.5-9, 9.5-11, 1-1.7, 3.2-4.2', ({
        'a': 6.3,
        'b': 3.7,
        '$total': 10.0
    }, [], meta())),
    ('a 4:30-20:30', ({
        'a': 16.0,
        '$total': 16.0
    }, [], meta())),
    ('a 7:15-8p, 10-12', ({
        'a': 14.8,
        '$total': 14.8
    }, [['20:00', '22:00', '2.0']], meta())),
    ('a 12am-2:30, 8-8pm', ({
        'a': 14.5,
        '$total': 14.5
    }, [['2:30', '8:00', '5.5']], meta())),
    ('a 4:30-20:30', ({
        'a': 16.0,
        '$total': 16.0
    }, [], meta())),
    ('a 0-0:34, 7:10-6p', ({
        'a': 11.4,
        '$total': 11.4
    }, [['0:34', '7:10', '6.6']], meta())),
    ('a 12a-2:30, 7:30-8p, 9:30-12', ({
        'a': 17.5,
        '$total': 17.5
    }, [['2:30', '7:30', '5.0'], ['20:00', '21:30', '1.5']], meta())),
    ('a 12a-1:30a\n b 11a-12:30p', ({
        'a': 1.5,
        'b': 1.5,
        '$total': 3.0
    }, [['1:30', '11:00', '9.5']], meta())),
]

subtime_rounding_calcs = [
    ('id1 7-8:26\n id2 9-10:27\n id3 11-11:26', ({
        'id1': 1.4,
        'id2': 1.5,
        'id3': 0.4,
        '$total': 3.3
    })),
    ('id1 7-8:26\n id2 9-10:27\n id3 11-11:26\n id4 12-1:27\n id5 2-3:27\n id6 4-4:27', ({
        'id1': 1.4,
        'id2': 1.5,
        'id3': 0.4,
        'id4': 1.5,
        'id5': 1.4,
        'id6': 0.5,
        '$total': 6.7
    })),
    ('id1 7-8:26\n id2 9-11:27\n id3 12-12:26', ({
        'id1': 1.4,
        'id2': 2.5,
        'id3': 0.4,
        '$total': 4.3
    })),
    ('id1 6-8:27\n id2 9-11:27\n id3 12-12:26', ({
        'id1': 2.4,
        'id2': 2.5,
        'id3': 0.4,
        '$total': 5.3
    })),
    ('id1 6-8:27\n id2 9-11:27\n id3 12-12:27\n id4 1-3:27', ({
        'id1': 2.4,
        'id2': 2.4,
        'id3': 0.5,
        'id4': 2.5,
        '$total': 7.8
    })),
]

invalid_calcs = [('a 7-8\n b 7-8',
                  'Double charging or invalid range: 7:00-8:00. Ensure lines starting with a PM time are written in 24 hour format.')]

target_time_calcs = [
    ('id1 6-8\n id2 8-10\n id3 10-11:33\n \\=5.6', ({
        'id1': 2.0,
        'id2': 2.0,
        'id3': 1.5,
        '$total': 5.5
    }, [], meta(target_time='11:34am'))),
    ('id1 6-8\n id2 8-10\n id3 1-1:30\n \\=4.6', ({
        'id1': 2.0,
        'id2': 2.0,
        'id3': 0.5,
        '$total': 4.5
    }, [['10:00', '13:00', '3.0']], meta(target_time='1:34pm'))),
    ('id1 6-8\n id2 8-10\n id3 10-11:34\n \\=5.6', ({
        'id1': 2.0,
        'id2': 2.0,
        'id3': 1.6,
        '$total': 5.6
    }, [], meta(target_achieved_at='11:34am'))),
]

ignore_inline_comments = [
    ('id1 6-8#comment\n id2 8-10\n id3 10-11:33\n', ({
        'id1': 2.0,
        'id2': 2.0,
        'id3': 1.5,
        '$total': 5.5
    }, [], meta())),
    ('id1 6-8//comment\n id2 8-10\n id3 10-11:33\n', ({
        'id1': 2.0,
        'id2': 2.0,
        'id3': 1.5,
        '$total': 5.5
    }, [], meta())),
    ('id1 6-8<comment>\n id2 8-10\n id3 10-11:33\n', ({
        'id1': 2.0,
        'id2': 2.0,
        'id3': 1.5,
        '$total': 5.5
    }, [], meta())),
]


@pytest.mark.parametrize('hours, expected', general_calcs)
def test_general_calcs(hour_calculator, hours, expected):
    assert hour_calculator(hours).calculate() == expected


@pytest.mark.parametrize('hours, expected', subtime_rounding_calcs)
def test_subtime_rounding_calcs(hour_calculator, hours, expected):
    assert hour_calculator(hours).calculate()[0] == expected


@pytest.mark.parametrize('hours, exception', invalid_calcs)
def test_invalid_calcs(hour_calculator, hours, exception):
    try:
        hour_calculator(hours).calculate()
        assert False, "Expected an exception but none was raised"
    except Exception as e:
        assert str(e) == exception


def test_valid_calc_break(hour_calculator):
    hours = 'c 8-12, 4-5\n oh 12-4\n other 18-9'
    output = hour_calculator(hours).calculate()
    assert output == ({'c': 5.0, 'oh': 4.0, 'other': 3.0, '$total': 12.0}, [['17:00', '18:00', '1.0']], meta())


def test_valid_calc_breaks(hour_calculator):
    hours = 'c 8-11, 4-5\n oh 12-4\n other 18-9'
    output = hour_calculator(hours).calculate()
    assert output == ({
        'c': 4.0,
        'oh': 4.0,
        'other': 3.0,
        '$total': 11.0
    }, [['11:00', '12:00', '1.0'], ['17:00', '18:00', '1.0']], meta())


@pytest.mark.parametrize('ordered', [True, False])
def test_unordered_only(ordered, hour_calculator):
    hours = 'b 9-8\n a 7-8'
    try:
        output = hour_calculator(hours).calculate(ordered=ordered)
        assert output == ({'$total': 12.0, 'a': 1.0, 'b': 11.0}, [['8:00', '9:00', '1.0']], meta())
    except RuntimeError:
        assert ordered


@pytest.mark.parametrize('ordered', [True, False])
def test_ordered_only(ordered, hour_calculator):
    hours = 'a 7-12\n b 1-8'
    try:
        output = hour_calculator(hours).calculate(ordered=ordered)
        assert output == ({'$total': 12.0, 'a': 5.0, 'b': 7.0}, [['12:00', '13:00', '1.0']], meta())
    except RuntimeError:
        assert not ordered


@pytest.mark.parametrize('ordered', [True, False])
def test_break_disagree(ordered, hour_calculator):
    hours = 'a 8-10\n b 10-1, 2-6\n c 7-8'
    output = hour_calculator(hours).calculate(ordered=ordered)
    if ordered:
        assert output == ({
            'a': 2.0,
            'b': 7.0,
            'c': 1.0,
            '$total': 10.0
        }, [['13:00', '14:00', '1.0'], ['18:00', '19:00', '1.0']], meta())
    else:
        assert output == ({'a': 2.0, 'b': 7.0, 'c': 1.0, '$total': 10.0}, [['13:00', '14:00', '1.0']], meta())


@pytest.mark.parametrize('ordered', [True, False])
def test_disagree(ordered, hour_calculator):
    hours = 'a 8-10\n c 1-2\n b 10-1, 2-6'
    if ordered:
        # ordered=True pushes b's interval past midnight — should raise ValueError
        try:
            hour_calculator(hours).calculate(ordered=ordered)
            assert False, "Expected ValueError for past-midnight interval"
        except ValueError:
            pass
    else:
        output = hour_calculator(hours).calculate(ordered=ordered)
        assert output == ({
            'a': 2.0,
            'c': 1.0,
            'b': 7.0,
            '$total': 10.0
        }, [['2:00', '8:00', '6.0'], ['13:00', '14:00', '1.0']], meta())


def test_valid_overlapping_ids(hour_calculator):
    hours = 'id1 6-8\n id2 8-10\n id1 10-11'
    output = hour_calculator(hours).calculate()
    assert output == ({'id1': 3.0, 'id2': 2.0, '$total': 5.0}, [], meta())


@pytest.mark.parametrize('hours, expected', target_time_calcs)
def test_target_hours(hour_calculator, hours, expected):
    assert hour_calculator(hours).calculate(ordered=True) == expected


@pytest.mark.parametrize('hours, expected', ignore_inline_comments)
def test_inline_comments(hour_calculator, hours, expected):
    assert hour_calculator(hours).calculate() == expected


def test_leading_zero_ordered(hour_calculator):
    """Leading zero (e.g. 09) marks a time as 24h/military — ordered mode must not infer +12 for it."""
    hours = 'id1 11-14, 15:30-17:55\nid2 09-11, 14-15:30'
    output = hour_calculator(hours).calculate(ordered=True)
    assert output == ({'id1': 5.4, 'id2': 3.5, '$total': 8.9}, [], meta())


def test_multiword_id(hour_calculator):
    """IDs containing spaces (e.g. 'test: capsa:') are parsed correctly and reported in detected_ids."""
    hours = 'test: capsa: 2-3'
    output = hour_calculator(hours).calculate(ordered=True)
    assert output == ({'test: capsa:': 1.0, '$total': 1.0}, [], meta(detected_ids=['test: capsa:']))
