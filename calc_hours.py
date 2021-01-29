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

Passing minutes in has not been thoroughly tested

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
        self.time_input = time_input
        self.hours = {}
        self.charges = {}

    def _format_ranges(self, ranges):
        formatted_ranges = []
        for rng in ranges:
            formatted_range = []
            for time in rng.split('-'):
                if ':' in time:
                    tmp = time.split(':')
                    tmp[1] = round(float(tmp[1]) / 60, 3)
                    formatted_range.append(str(float(tmp[0]) + tmp[1]))
                else:
                    formatted_range.append(time)
            formatted_ranges.append('-'.join(formatted_range))

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
                space = charge_data.find(' ')
                ranges = [hr.strip() for hr in charge_data[space + 1:].split(',')]
                ranges = self._format_ranges(ranges)
                times = [[float(rng.split('-')[0]), float(rng.split('-')[1])] for rng in ranges]
                # hours[charge_data[:space]] = [hr.strip() for hr in charge_data[space + 1:].split(',')]
                self.hours[charge_data[:space]] = times
            except ValueError as e:
                raise e

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
                    if time[1] < time[0]:
                        mil_data.append([time[0], time[1] + 12])
                    else:
                        mil_data.append([time[0] + 12, time[1] + 12])

            self.hours[code] = mil_data

        # print('mil times ' + str(hours))

    def _calculate_charges(self):
        last_time = None
        while self.hours:
            nxt_chg = self._next_charge(self.hours)
            time = self.hours[nxt_chg][0]
            duration = round(time[1] - time[0], 3)

            if last_time and time[0] < last_time:
                raise RuntimeError('Double charging or invalid range: ' + str(time[0]) + '-' + str(last_time))

            if last_time and last_time != time[0]:
                print('break: ' + str(round(last_time % 12, 3)) + '-' + str(round(time[0] % 12, 3)) + ' == ' + str(round(time[0] - last_time, 3)))

            if len(self.hours[nxt_chg]) > 1:
                self.hours[nxt_chg] = self.hours[nxt_chg][1:]
            else:
                del self.hours[nxt_chg]

            last_time = time[1]

            if nxt_chg in self.charges:
                self.charges[nxt_chg] += duration
            else:
                self.charges[nxt_chg] = duration

    def calculate(self, cli=False):
        self._parse_hour_input()
        self._convert_mil_times()
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
        return hours


if __name__ == '__main__':
    try:
        raw = sys.argv[1]
        calc = HourCalculator(raw)
        calc.calculate(cli=True)
    except IndexError as e:
        print('Example usage:\n    python calc_hours.py "oh 8-8.5, 9-9.5, 11-1, 1.7-3.2, 4.2-6\n    c 8.5-9, 9.5-11, 1-1.7, 3.2-4.2"\n')
        raise e
