import math
import sys
"""
This script can be used to sum up intervals of time worked on different
charge numbers. This tool will notify of breaks taken though out the
day and invalid time entries (overlapping entries or non ordered entries).
The time ranges are required to be dashed intervals, comma separated and
sorted. An identifier, followed by a space is required, at the beginning
of each time entry line.

Time can also be passed in with minutes rather than tenths of hours.  The
fractional hours will be calculated with percision through the summation,
but rounded to the nearest tenth for the total. Each charge number will be
displayed with percision as to not short the employee any hours by pre rounding
(ie. 0.04 + 0.04 = .08 ~= 0.1)

    Example time entries:
        oh 8-8.5, 9-9.5, 11-1, 1.7-3.2, 4.2-6
        c 8.5-9, 9.5-11, 1-1.7, 3.2-4.2

    Example usage:
         python calc_hours.py "oh 8-8.5, 9-9.5, 11-1, 1.7-3.2, 4.2-6
         c 8.5-9, 9.5-11, 1-1.7, 3.2-4.2"'

    Example output:
        CHARGES
        c == 3.7 hrs
        oh == 6.3 hrs
        total: 10.0

"""


class HourCalculator(object):
    def __init__(self, time_input):
        self.time_input = time_input.strip()
        self.hours = {}
        self.charges = {}
        self.breaks = []

    def _format_ranges(self, ranges):
        formatted_ranges = []
        for rng in ranges:
            formatted_range = []
            for time in rng.split('-'):
                am = False
                pm = False
                if time[-1] == 'a':
                    time = time[:-1]
                    am = True
                elif time[-2:] == 'am':
                    time = time[:-2]
                    am = True
                elif time[-1] == 'p':
                    time = time[:-1]
                    pm = True
                elif time[-2:] == 'pm':
                    time = time[:-2]
                    pm = True

                if ':' in time:
                    times = time.split(':')
                    hours = float(times[0])
                    minutes = round(float(times[1]) / 60, 3)
                else:
                    hours, minutes = float(time), 0

                hours = float(hours) - 12 if am and int(hours) == 12 else float(hours)
                hours = float(hours) + 12 if pm else float(hours)

                formatted_range.append(str(hours + minutes))

            formatted_ranges.append('-'.join(formatted_range))

        # print('formatted_ranges:', formatted_ranges)
        return formatted_ranges

    def _next_charge(self, hours):
        nxt = None
        nex_start = None
        for code, data in hours.items():
            start = data[0][0]
            if not nxt:
                nxt = code
                nex_start = start
            elif start <= nex_start:
                nxt = code
                nex_start = start
        return nxt

    def _parse_hour_input(self):
        # for charge_data in raw.split('\n'):
        for charge_data in self.time_input.splitlines():
            try:
                if not charge_data:
                    continue
                charge_data = charge_data.strip().rstrip(',')
                space = charge_data.find(' ')
                ranges = [hr.strip() for hr in charge_data[space + 1:].split(',')]
                ranges = self._format_ranges(ranges)
                times = [[float(rng.split('-')[0]), float(rng.split('-')[1])] for rng in ranges]
                # print('times', times)
                str_id = charge_data[:space]
                if str_id in self.hours:
                    raise ValueError('Repeated identifier: ' + str_id + '. Combine hours or use unique identifiers.')
                self.hours[str_id] = times
                self.charges[str_id] = 0
            except ValueError as e:
                raise e

    def _convert_ordered_starts(self):
        afternoon = False
        last_start = None
        for code, data in self.hours.items():
            if not last_start:
                last_start = data[0][0]
            if last_start > data[0][0]:
                afternoon = True
            if afternoon:
                data[0] = [data[0][0] + 12, data[0][1]]

        # print('ordered starts:', self.hours)

    def _convert_mil_times(self):
        for code, data in self.hours.items():
            mil_data = []
            afternoon = False
            for time in data:
                if mil_data and time[0] < mil_data[-1][1]:
                    afternoon = True
                elif time[1] < time[0]:
                    afternoon = True

                if not afternoon:
                    mil_data.append(time)
                else:
                    if time[1] < time[0] and time[1] <= 12:
                        mil_data.append([time[0], time[1] + 12])
                    else:
                        mil_data.append(
                            [time[0] + 12 if time[0] <= 12 else time[0], time[1] + 12 if time[1] <= 12 else time[1]])

            self.hours[code] = mil_data

        # print('mil times ' + str(self.hours))

    def _calculate_charges(self):
        last_time = None
        while self.hours:
            nxt_chg = self._next_charge(self.hours)
            time = self.hours[nxt_chg][0]
            duration = round(abs(time[1] - time[0]), 3)

            if last_time and time[0] < last_time:
                raise RuntimeError('Double charging or invalid range: ' + str(time[0]) + '-' + str(last_time)
                                   + '. Ensure lines starting with a PM time are written in 24 hour format.')

            if last_time and last_time != time[0]:
                break_start = self._frac_hours_to_minutes(round(last_time, 3))
                break_end = self._frac_hours_to_minutes(round(time[0], 3))
                break_dur = str(round(abs(time[0] - last_time), 2))
                self.breaks.append([break_start, break_end, break_dur])
                # print('break: ' + break_start + '-' + break_end + ' == ' + break_dur)

            if len(self.hours[nxt_chg]) > 1:
                self.hours[nxt_chg] = self.hours[nxt_chg][1:]
            else:
                del self.hours[nxt_chg]

            last_time = time[1]

            self.charges[nxt_chg] += duration

    def _frac_hours_to_minutes(self, frac_hours):
        return str(math.floor(frac_hours)) + ':' + str(format(round((frac_hours % 1) * 60), '02d'))

    def __str__(self):
        return '\n'.join(['hours: ' + str(self.hours), 'charges: ' + str(self.charges), 'breaks: ' + str(self.breaks)])

    def calculate(self, ordered=False, cli=False):
        if ordered:
            if cli:
                print('Calculating ordered.')
            self._parse_hour_input()
            self._convert_ordered_starts()
            self._convert_mil_times()
            # print('ordered:', self)
            self._calculate_charges()
        else:
            self._parse_hour_input()
            self._convert_mil_times()
            # print('unordered:', self)
            self._calculate_charges()

        hours = {}

        if cli:
            print('\nCHARGES')
        total = 0
        for chg, duration in self.charges.items():
            if cli:
                print(chg + ' == ' + str(round(duration, 2)) + ' hrs')
            hours[chg] = round(duration, 2)
            total += duration
        if cli:
            print('total: ' + str(round(total, 1)))

        hours['$total'] = round(total, 1)
        return hours, self.breaks


if __name__ == '__main__':
    try:
        raw = sys.argv[1]
        HourCalculator(raw).calculate(ordered=True, cli=True)
        print()
        HourCalculator(raw).calculate(ordered=False, cli=True)
    except IndexError as e:
        print('Example usage:\n    python calc_hours.py "oh 8-8.5, 9-9.5, 11-1, 1.7-3.2, 4.2-6\n    c 8.5-9, 9.5-11, \
               1-1.7, 3.2-4.2"\n')
        raise e
