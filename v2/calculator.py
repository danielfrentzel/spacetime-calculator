import logging
import math
import re

log = logging.getLogger('STC')
log.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_handler.setLevel(logging.DEBUG)
_handler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d %(message)s', datefmt='%H:%M:%S'))
log.addHandler(_handler)
log.propagate = False


def _parse_time(t_str):
    """Parse a time string to decimal hours.
    Supports H, H.H, H:MM with optional a/am/p/pm suffix."""
    t_str = t_str.strip()
    am = False
    pm = False

    if t_str.endswith('am'):
        t_str = t_str[:-2]
        am = True
    elif t_str.endswith('pm'):
        t_str = t_str[:-2]
        pm = True
    elif t_str.endswith('a'):
        t_str = t_str[:-1]
        am = True
    elif t_str.endswith('p'):
        t_str = t_str[:-1]
        pm = True

    if ':' in t_str:
        parts = t_str.split(':')
        hours = float(parts[0])
        raw_minutes = float(parts[1])
        if raw_minutes < 0 or raw_minutes > 59:
            raise ValueError(f"Invalid minutes '{int(raw_minutes)}' in time '{t_str.strip()}'. Minutes must be 0–59.")
        minutes = round(raw_minutes / 60, 3)
    else:
        hours = float(t_str)
        minutes = 0

    if am and int(hours) == 12:
        hours = 0
    elif pm and int(hours) != 12:
        hours += 12

    return hours + minutes


def _frac_to_hhmm(frac):
    """Decimal hours → 'H:MM' (24h). e.g. 13.5 → '13:30'"""
    h = math.floor(frac)
    m = round((frac % 1) * 60)
    if m == 60:
        h += 1
        m = 0
    return f"{h}:{m:02d}"


def _frac_to_12h(frac):
    """Decimal hours → 'H:MMam/pm'. e.g. 13.567 → '1:34pm'"""
    h = math.floor(frac)
    m = round((frac % 1) * 60)
    if m == 60:
        h += 1
        m = 0
    if h > 12:
        return f"{h % 12}:{m:02d}pm"
    elif h == 12:
        return f"12:{m:02d}pm"
    elif h == 0:
        return f"12:{m:02d}am"
    else:
        return f"{h}:{m:02d}am"


def _strip_inline_comments(lines):
    result = []
    for line in lines:
        if '#' in line:
            line = line[:line.find('#')].strip()
        if '//' in line:
            line = line[:line.find('//')].strip()
        if '<' in line:
            line = line[:line.find('<')].strip()
        result.append(line)
    return result


def _parse_encoding(lines):
    """Extract \\= target-hours lines. Returns (remaining_lines, target_hours)."""
    target_hours = 0
    remaining = []
    for line in lines:
        if line[:3] == '\\==':
            try:
                target_hours = float(line[3:])
            except ValueError:
                pass
        elif line[:2] == '\\=':
            try:
                target_hours = float(line[2:])
            except ValueError:
                pass
        else:
            remaining.append(line)
    return remaining, target_hours


def _format_ranges(ranges_list):
    """Parse ['start-end', ...] into [[start_dec, end_dec], ...]."""
    result = []
    for rng in ranges_list:
        parts = rng.split('-')
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise ValueError(f"Invalid time range '{rng.strip()}'. Expected format: start-end (e.g. 8-5, 8:30-12).")
        start = _parse_time(parts[0])
        end = _parse_time(parts[1])
        result.append([start, end])
    return result


def _split_line(line):
    """Split a line into (id, ranges_str) by finding the first digit-dash pattern.
    Returns (None, None) if no time range is found."""
    match = re.search(r'\s+(?=\d[\d.:]*(am?|pm?)?-)', line)
    if not match:
        return None, None
    return line[:match.start()], line[match.end():]


def _explicit_start_ids(lines):
    """Return the set of IDs whose first start time has an explicit AM/PM suffix.
    These IDs are already unambiguous and should not have +12 inferred."""
    explicit = set()
    for line in lines:
        if not line:
            continue
        str_id, ranges_str = _split_line(line)
        if str_id is None:
            continue
        first_time = ranges_str.split(',')[0].strip().split('-')[0].strip()
        if re.search(r'\d(am|pm|a|p)$', first_time, re.IGNORECASE) or re.match(r'^0\d', first_time):
            explicit.add(str_id)
    return explicit


def _convert_ordered_starts(hours_dict, explicit_ids=None):
    """If any line's start < first line's start, mark afternoon and add 12 to its first interval.
    IDs in explicit_ids already have unambiguous AM/PM — skip the +12 offset for those."""
    explicit_ids = explicit_ids or set()
    log.debug('  [ordered] converting ordered starts  (explicit AM/PM IDs skipped: %s)',
              sorted(explicit_ids) if explicit_ids else 'none')
    afternoon = False
    last_start = None
    for code, data in hours_dict.items():
        if last_start is None:
            last_start = data[0][0]
        if last_start > data[0][0]:
            afternoon = True
        if afternoon and code not in explicit_ids:
            log.debug('  [ordered]   %s: start %.3f → %.3f (+12 inferred PM)', code, data[0][0], data[0][0] + 12)
            data[0] = [data[0][0] + 12, data[0][1]]


def _convert_mil_times(hours_dict):
    """Convert each ID's intervals to monotonic 24h times in place."""
    for code, data in hours_dict.items():
        mil_data = []
        afternoon = False
        for time in data:
            if mil_data and time[0] < mil_data[-1][1]:
                afternoon = True
            elif time[1] < time[0]:
                afternoon = True

            if not afternoon:
                new_time = time
            else:
                if time[1] < time[0] and time[1] <= 12:
                    new_time = [time[0], time[1] + 12]
                else:
                    new_time = [
                        time[0] + 12 if time[0] < 12 else time[0],
                        time[1] + 12 if time[1] <= 12 else time[1],
                    ]

            if new_time[0] > 24 or new_time[1] > 24:
                raise ValueError(f"Interval for '{code}' exceeds 24 hours after conversion. "
                                 f"Hours can only be calculated within a single day.")
            if new_time[1] < new_time[0]:
                raise ValueError(f"Interval for '{code}' spans past midnight after conversion "
                                 f"({_frac_to_hhmm(new_time[0])}–{_frac_to_hhmm(new_time[1])} next day). "
                                 f"Hours can only be calculated within a single day.")
            if mil_data and new_time[0] < mil_data[-1][1]:
                raise ValueError(f"Interval for '{code}' overlaps a previous interval after conversion "
                                 f"({_frac_to_hhmm(new_time[0])}–{_frac_to_hhmm(new_time[1])} starts before "
                                 f"{_frac_to_hhmm(mil_data[-1][0])}–{_frac_to_hhmm(mil_data[-1][1])} ends). "
                                 f"Time entries may cross midnight — hours can only be calculated within a single day.")
            mil_data.append(new_time)
        hours_dict[code] = mil_data


def _next_charge(hours_dict):
    """Return the ID whose next interval starts earliest (ties: last one wins)."""
    nxt = None
    nxt_start = None
    for code, data in hours_dict.items():
        start = data[0][0]
        if not nxt:
            nxt = code
            nxt_start = start
        elif start <= nxt_start:
            nxt = code
            nxt_start = start
    return nxt


def _format_break_display(b):
    """Format a break triple ['H:MM','H:MM','dur'] for HTML display."""
    start_str, end_str, dur_str = b
    sh, sm = map(int, start_str.split(':'))
    eh, em = map(int, end_str.split(':'))
    dur = float(dur_str)
    dur_min = round(dur * 60)

    def to_12h(h, m):
        period = 'AM' if h < 12 else 'PM'
        h12 = h % 12 or 12
        return f"{h12}:{m:02d} {period}"

    return f"{to_12h(sh, sm)} \u2013 {to_12h(eh, em)}  ({dur_min} min / {dur:.2f} hrs)"


def process_input(text, ordered=False):
    """Parse time entries and return (results_dict, breaks_list, metadata_dict).

    results_dict : {'id': hours, ..., '$total': total}
    breaks_list  : [['H:MM', 'H:MM', 'dur_str'], ...]   (24h start/end, decimal dur)
    metadata_dict: {'target_time': 'H:MMam/pm' or None}
    """
    text = text.replace('\\n', '\n')
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    lines = _strip_inline_comments(lines)
    lines, target_hours = _parse_encoding(lines)

    # Build hours dict: id → [[start_dec, end_dec], ...]
    hours = {}
    charges = {}
    detected_ids = []
    for line in lines:
        if not line:
            continue
        line = line.rstrip(',')
        str_id, ranges_str = _split_line(line)
        if str_id is None:
            raise ValueError(f"Invalid line (missing time ranges): '{line}'")
        if ' ' in str_id and str_id not in detected_ids:
            detected_ids.append(str_id)
        ranges_list = [r.strip() for r in ranges_str.split(',')]
        ranges = _format_ranges(ranges_list)
        if str_id in hours:
            hours[str_id] += ranges  # combine duplicate IDs
        else:
            hours[str_id] = ranges
            charges[str_id] = 0

    mode = 'ordered' if ordered else 'unordered'
    log.debug('  [%s] starting calculation', mode)

    if ordered:
        _convert_ordered_starts(hours, explicit_ids=_explicit_start_ids(lines))
    _convert_mil_times(hours)

    # Snapshot the latest end time across all IDs (used for target time calc)
    last_time_snapshot = -1
    for code, data in hours.items():
        end_time = data[-1][1]
        if end_time > last_time_snapshot:
            last_time_snapshot = end_time

    # Walk all intervals in chronological order, charge durations, record breaks
    hours_copy = {code: [list(t) for t in data] for code, data in hours.items()}
    breaks = []
    last_time = None

    while hours_copy:
        nxt_chg = _next_charge(hours_copy)
        time = hours_copy[nxt_chg][0]
        duration = round(abs(time[1] - time[0]), 3)

        if last_time and time[0] < last_time:
            raise RuntimeError(f'Double charging or invalid range: {_frac_to_hhmm(time[0])}-{_frac_to_hhmm(last_time)}. '
                               f'Ensure lines starting with a PM time are written in 24 hour format.')

        if last_time and last_time != time[0]:
            breaks.append([
                _frac_to_hhmm(round(last_time, 3)),
                _frac_to_hhmm(round(time[0], 3)),
                str(round(abs(time[0] - last_time), 2)),
            ])

        if len(hours_copy[nxt_chg]) > 1:
            hours_copy[nxt_chg] = hours_copy[nxt_chg][1:]
        else:
            del hours_copy[nxt_chg]

        last_time = time[1]
        charges[nxt_chg] += duration

    log.debug('  [%s] breaks: %s', mode, breaks if breaks else 'none')

    # Compute exact vs rounded totals for rounding adjustment
    total_exact = 0
    total_round = 0
    diffs = []
    for chg, duration in charges.items():
        total_exact += duration
        total_round += round(duration, 1)
        diff = round(duration - round(duration, 1), 4)
        diffs.append([chg, diff])

    # Target time: how much longer until target_hours is met
    target_time = None
    target_achieved_at = None
    if target_hours:
        unfulfilled = target_hours - total_exact - 0.05 + 0.01
        if unfulfilled > 0:
            target_time = _frac_to_12h(last_time_snapshot + unfulfilled)
        else:
            target_achieved_at = _frac_to_12h(last_time_snapshot + unfulfilled)

    # Distribute rounding error so per-ID values stay consistent with global total
    diffs = sorted(diffs, key=lambda d: charges[d[0]], reverse=True)
    total_diff = round(round(total_exact, 1) - total_round, 4)

    while abs(total_diff) >= 0.1:
        diffs = sorted(diffs, key=lambda d: abs(d[1]), reverse=True)
        adjusted = False
        for diff in diffs:
            if total_diff > 0:
                if diff[1] > 0:
                    charges[diff[0]] = round(charges[diff[0]] + 0.05, 2)
                    diff[1] = 0
                    total_diff -= 0.1
                    adjusted = True
                    break
                else:
                    continue
            else:
                if diff[1] < 0:
                    charges[diff[0]] = round(charges[diff[0]] - 0.05, 2)
                    diff[1] = 0
                    total_diff += 0.1
                    adjusted = True
                    break
                else:
                    continue
        if not adjusted:
            break

    results = {}
    total = 0
    for chg, duration in charges.items():
        results[chg] = round(duration, 1)
        total += round(duration, 1)
    results['$total'] = round(total, 1)

    log.debug('  [%s] exact, rounded, final total:   %.2f, %.2f, %.2f', mode, total_exact, total_round, total)
    log.debug('  [%s] per-ID results: %s', mode, {k: v for k, v in results.items() if k != '$total'})

    return results, breaks, {
        'target_time': target_time,
        'target_achieved_at': target_achieved_at,
        'detected_ids': detected_ids
    }
