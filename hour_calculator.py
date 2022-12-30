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
        self.time_input = [line.strip() for line in time_input.strip().splitlines()]
        self.hours = {}
        self.charges = {}
        self.breaks = []

        self._target_hours = 0

        self._last_time = -1
        self._target_time = None
        self.metadata = {}

        self._strip_inline_comments()
        self._parse_encoding()

    def _strip_inline_comments(self):
        """
        Remove inline comments from time inputs.
        Inline comment delimiters: #, //, <
        ie
            id1 6-8  # comment
            id1 6-8 //comment
            id1 6-8 <comment>
        """
        self.time_input = [line[:line.find('#')].strip() if '#' in line else line for line in self.time_input]
        self.time_input = [line[:line.find('//')].strip() if '//' in line else line for line in self.time_input]
        self.time_input = [line[:line.find('<')].strip() if '<' in line else line for line in self.time_input]

    def _parse_encoding(self):
        """
        Parse encoded time input lines.

        Encoded target hours (with single backslash)
            \\=10.0
            or
            \\==10.0
        """
        non_encoded_lines = []

        # target hours
        for line in self.time_input:
            if line[:3] == '\\==':
                try:
                    self._target_hours = float(line[3:])
                except ValueError:
                    print('Unable to parse target hours.')
            elif line[:2] == '\\=':
                try:
                    self._target_hours = float(line[2:])
                except ValueError:
                    print('Unable to parse target hours.')
            else:
                non_encoded_lines.append(line)

        self.time_input = non_encoded_lines

    def _format_ranges(self, ranges):
        """
        Convert time ranges within a line of the time entry to required format for calculations.
        """
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
        """
        Find the next ordered charge id to evaluate.
        """
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
        """
        Parse the hour input lines and populate the hours attribute. Charge ids are determined by the string up until
        the first inline space.HHour ranges are collected from comma delimited, dashed seperated hour values.
        ie
            charge_id 9-10, 11-12
        """
        for charge_data in self.time_input:
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
                    print('combining duplicated id:', str_id)
                    self.hours[str_id] += times
                else:
                    self.hours[str_id] = times
                self.charges[str_id] = 0
            except ValueError as e:
                raise e

    def _convert_ordered_starts(self):
        """
        Determine unspecified switch from AM to PM for ordered data.
        """
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
        """
        Convert hours attribute to 24 hour format.
        """
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

    def _determine_last_time(self):
        """
        Determine last time interval entry. This is used from calculating the target goal time.
        """
        last_time = -1
        for code, data in self.hours.items():
            end_time = data[-1][1]
            if end_time > last_time:
                last_time = end_time

        self._last_time = last_time

    def _calculate_charges(self):
        """
        Populate the charges attribute with summations of the input hour intervals.

        Warning: This method is destructive to the hours attribute (pls fix).
        """
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
                print('break: ' + break_start + '-' + break_end + ' == ' + break_dur)

            if len(self.hours[nxt_chg]) > 1:
                self.hours[nxt_chg] = self.hours[nxt_chg][1:]
            else:
                del self.hours[nxt_chg]

            last_time = time[1]

            self.charges[nxt_chg] += duration

    def _frac_hours_to_minutes(self, frac_hours):
        """
        Convert decimal hours to nearest hour:minute format.
        ie
            4:28
        """
        return str(math.floor(frac_hours)) + ':' + str(format(round((frac_hours % 1) * 60), '02d'))

    def _frac_hours_to_12h_format(self, frac_hours):
        """
        Convert decimal hours to nearest 12h hour:minute format.
        ie
            4:28pm
        """
        am_pm = 'am'
        if math.floor(frac_hours) > 12:
            hours = str(math.floor(frac_hours) % 12)
            am_pm = 'pm'
        elif math.floor(frac_hours) == 12:
            hours = str(math.floor(frac_hours))
            am_pm = 'pm'
        else:
            hours = str(math.floor(frac_hours))

        return hours + ':' + str(format(round((frac_hours % 1) * 60), '02d')) + am_pm

    def __str__(self):
        """
        Print useful attributes of the hour calculator object.
        """
        return '\n'.join(['hours: ' + str(self.hours), 'charges: ' + str(self.charges), 'breaks: ' + str(self.breaks)])

    def _eval_target_time(self, exact_hours, last_charge_time):
        """
        Return the 12 hour format time required to fulfill target hours.
        """
        print('(_eval_target_time)')

        if not self._target_hours:
            return
        if exact_hours > self._target_hours:
            print('Target hours fulfilled.')
            return

        # +0.01 bunk since python3 rounds half to even
        # adding 0.01 is not breaking since it is less than minute accuracy (1/60)
        # https://stackoverflow.com/questions/10825926/python-3-x-rounding-behavior
        unfulfilled_hours = self._target_hours - exact_hours - 0.05 + 0.01
        if unfulfilled_hours > 0:
            target_time = last_charge_time + unfulfilled_hours
            target_time_h_m = self._frac_hours_to_12h_format(target_time)
            print('Target time: ', target_time_h_m)
            return target_time_h_m
        return None

    def calculate(self, ordered=True, cli=False):
        """
        Calculate hours worked from time input.
        """
        if ordered:
            print('Calculating ordered')
            if cli:
                print('Calculating ordered.')
            self._parse_hour_input()
            self._convert_ordered_starts()
            self._convert_mil_times()
            # print('ordered:', self)
            self._determine_last_time()
            self._calculate_charges()
        else:
            print('Calculating unordered')
            self._parse_hour_input()
            self._convert_mil_times()
            # print('unordered:', self)
            self._determine_last_time()
            self._calculate_charges()

        # print('charges:', self.charges)

        total_exact = 0
        total_round = 0
        diffs = []
        for chg, duration in self.charges.items():
            total_exact += duration
            total_round += round(duration, 1)
            diff = round(duration - round(duration, 1), 4)
            diffs.append([chg, diff])

        self._target_time = self._eval_target_time(total_exact, self._last_time)

        # prefer to adjust numbers with more time worked (least proportional rounding adjustment)
        diffs = sorted(diffs, key=lambda diff: self.charges[diff[0]], reverse=True)
        total_diff = round(round(total_exact, 1) - total_round, 4)

        # find furthest actual from rounded, ie closest to rounding
        while abs(total_diff) >= 0.1:
            # adjust those that are the closest to rounding
            diffs = sorted(diffs, key=lambda diff: abs(diff[1]), reverse=True)
            for diff in diffs:
                if total_diff > 0:  # need to increase subtimes
                    if diff[1] > 0:  # was rounded down
                        # print('rounding up', diff[0])
                        self.charges[diff[0]] = round(self.charges[diff[0]] + 0.05, 2)
                        diff[1] = 0
                        total_diff -= 0.1
                        break
                    else:
                        continue
                else:  # need to decrease subtimes
                    if diff[1] < 0:  # was rounded up
                        # print('rounding down', diff[0])
                        self.charges[diff[0]] = round(self.charges[diff[0]] - 0.05, 2)
                        diff[1] = 0
                        total_diff += 0.1
                        break
                    else:
                        continue

        # print('charges:', self.charges)

        hours = {}

        if cli:
            print('\nCHARGES')
        total = 0
        for chg, duration in self.charges.items():
            if cli:
                print(chg + ' == ' + str(round(duration, 1)) + ' hrs')
            hours[chg] = round(duration, 1)
            total += round(duration, 1)
        if cli:
            print('total: ' + str(round(total, 1)))

        hours['$total'] = round(total, 1)

        # review subtime adjustments
        print('exact total, new total, total round:', total_exact, round(total, 1), round(total_exact, 1))
        if round(total, 1) != round(total_exact, 1):
            sys.exit('Round error occurred. Please contact maintainer with the input.')

        self.metadata['target_time'] = self._target_time

        print()
        return hours, self.breaks, self.metadata


if __name__ == '__main__':
    try:
        raw = sys.argv[1]
        HourCalculator(raw).calculate(ordered=True, cli=True)
        print()
        HourCalculator(raw).calculate(ordered=False, cli=True)
    except IndexError as e:
        print('Example usage:\n    python3 calc_hours.py "oh 8-8.5, 9-9.5, 11-1, 1.7-3.2, 4.2-6\n    c 8.5-9, 9.5-11, \
               1-1.7, 3.2-4.2"\n')
        raise e
