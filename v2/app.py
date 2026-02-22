#!/usr/bin/env python3
import os as _os
import sys as _sys

from flask import Blueprint, Flask, render_template, request

# Make the project root importable so HourCalculator can be found whether
# v2/app.py is run standalone or imported from the parent app.
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)
from hour_calculator import HourCalculator

# Make v2 dir importable so calculator can be found in both standalone and blueprint modes.
_V2_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _V2_DIR not in _sys.path:
    _sys.path.insert(0, _V2_DIR)
from calculator import _format_break_display, log, process_input

app = Flask(__name__)
v2_bp = Blueprint('v2', __name__, template_folder='templates')


@v2_bp.route("/help")
def help():
    return render_template('v2/help.html')


@v2_bp.route("/", methods=["GET", "POST"])
def index():
    input_text = ""
    results = None
    total = 0
    breaks = []
    target_time = None
    target_achieved_at = None
    detected_ids = []
    error = None
    order_warning = None
    order_error = None
    v1_ordered = None
    v1_ordered_total = 0
    v1_ordered_breaks = []
    v1_ordered_error = None
    v1_unordered = None
    v1_unordered_total = 0
    v1_unordered_breaks = []
    v1_unordered_error = None
    v2_unordered = None
    v2_unordered_total = 0
    v2_unordered_breaks = []
    v2_unordered_error = None
    methods_differ = False
    target_input = ""

    if request.method == "POST":
        input_text = request.form.get("input", "")
        target_input = request.form.get("target", "").strip()
        calc_text = input_text
        if target_input:
            try:
                float(target_input)
                calc_text = input_text.rstrip() + f"\n\\={target_input}"
            except ValueError:
                pass  # ignore non-numeric target input
        try:
            log.debug('=' * 72)
            log.debug('NEW REQUEST')
            log.debug('Raw input:\n%s', calc_text)
            log.debug('-' * 72)

            raw, raw_breaks, metadata = process_input(calc_text, ordered=True)

            total = raw.pop('$total', 0)
            results = raw
            target_time = metadata.get('target_time')
            target_achieved_at = metadata.get('target_achieved_at')
            detected_ids = metadata.get('detected_ids', [])
            breaks = [_format_break_display(b) for b in raw_breaks]

        except (ValueError, RuntimeError) as e:
            error = str(e)
            log.debug('ERROR: %s', e)

        # v2 unordered — runs independently so a primary failure doesn't block it
        try:
            raw_ord, raw_ord_breaks, unordered_meta = process_input(calc_text, ordered=False)
            v2_unordered = {k: v for k, v in raw_ord.items() if k != '$total'}
            v2_unordered_total = raw_ord.get('$total', 0)
            v2_unordered_breaks = [_format_break_display(b) for b in raw_ord_breaks]
            if not detected_ids:
                detected_ids = unordered_meta.get('detected_ids', [])
            if results is not None and (v2_unordered != results or v2_unordered_total != total):
                order_warning = dict(v2_unordered)
                order_warning['Total'] = v2_unordered_total
        except RuntimeError as e:
            v2_unordered_error = str(e)
        except ValueError as e:
            order_error = str(e)
            v2_unordered_error = str(e)

        # Run v1 (HourCalculator) calculations on the same input
        v1_input = calc_text.replace('\\n', '\n')
        try:
            h, b, _ = HourCalculator(v1_input).calculate(ordered=True)
            v1_ordered_total = h.pop('$total', 0)
            v1_ordered = h
            v1_ordered_breaks = [_format_break_display(brk) for brk in b]
        except Exception as e:
            v1_ordered_error = str(e)
        try:
            h, b, _ = HourCalculator(v1_input).calculate(ordered=False)
            v1_unordered_total = h.pop('$total', 0)
            v1_unordered = h
            v1_unordered_breaks = [_format_break_display(brk) for brk in b]
        except Exception as e:
            v1_unordered_error = str(e)

        # 4-method comparison summary log
        all_ids_set = set()
        for _m in [results, v2_unordered, v1_unordered, v1_ordered]:
            if _m is not None:
                all_ids_set.update(_m.keys())
        all_ids = list(all_ids_set)

        if all_ids or any([error, v2_unordered_error, v1_ordered_error, v1_unordered_error]):
            log.debug('-' * 72)
            log.debug('SUMMARY')
            col_w = max([len(k) for k in all_ids] + [len('Total')], default=4) + 2
            col_v = 12
            sep = '-' * (col_w + col_v * 3 + 18)
            log.debug('  %-*s  %-*s  %-*s  %-*s  %s', col_w, 'ID', col_v, 'V2 Ord', col_v, 'V2 Unord', col_v,
                      'V1 Unord', 'V1 Ord')
            log.debug('  %s', sep)
            for id_ in all_ids:
                v2u = f'{results[id_]:.1f}' if results and id_ in results else ('ERR' if error else 'n/a')
                v2o = f'{v2_unordered[id_]:.1f}' if v2_unordered and id_ in v2_unordered else (
                    'ERR' if v2_unordered_error else 'n/a')
                v1u = f'{v1_unordered[id_]:.1f}' if v1_unordered and id_ in v1_unordered else (
                    'ERR' if v1_unordered_error else 'n/a')
                v1o = f'{v1_ordered[id_]:.1f}' if v1_ordered and id_ in v1_ordered else (
                    'ERR' if v1_ordered_error else 'n/a')
                numeric = [float(v) for v in [v2u, v2o, v1u, v1o] if v not in ('ERR', 'n/a')]
                row_differs = len(set(numeric)) > 1
                log.debug('  %-*s  %-*s  %-*s  %-*s  %s%s', col_w, id_, col_v, v2u, col_v, v2o, col_v, v1u, v1o,
                          '  ← differs' if row_differs else '')
            log.debug('  %s', sep)
            v2u_t = f'{total:.1f}' if results is not None else ('ERR' if error else 'n/a')
            v2o_t = f'{v2_unordered_total:.1f}' if v2_unordered is not None else (
                'ERR' if v2_unordered_error else 'n/a')
            v1u_t = f'{v1_unordered_total:.1f}' if v1_unordered is not None else (
                'ERR' if v1_unordered_error else 'n/a')
            v1o_t = f'{v1_ordered_total:.1f}' if v1_ordered is not None else ('ERR' if v1_ordered_error else 'n/a')
            log.debug('  %-*s  %-*s  %-*s  %-*s  %s', col_w, 'Total', col_v, v2u_t, col_v, v2o_t, col_v, v1u_t, v1o_t)
            log.debug('  %s', sep)

            # Compute methods_differ for auto-expand
            id_differs = False
            for id_ in all_ids:
                vals = [m[id_] for m in [results, v2_unordered, v1_unordered, v1_ordered] if m is not None and id_ in m]
                if len(set(vals)) > 1:
                    id_differs = True
            total_vals = [
                t for m, t in [(results,
                                total), (v2_unordered,
                                         v2_unordered_total), (v1_unordered,
                                                               v1_unordered_total), (v1_ordered, v1_ordered_total)]
                if m is not None
            ]
            total_differs = len(set(total_vals)) > 1
            any_error = bool(error or v2_unordered_error or v1_ordered_error or v1_unordered_error)
            methods_differ = id_differs or total_differs or any_error

            if not methods_differ:
                log.debug('  All 4 methods agree.')
            else:
                parts = []
                disagree_ids = [
                    id_ for id_ in all_ids if len(
                        set(m[id_] for m in [results, v2_unordered, v1_unordered, v1_ordered]
                            if m is not None and id_ in m)) > 1
                ]
                if disagree_ids:
                    parts.append('IDs differ: ' + ', '.join(disagree_ids))
                if total_differs:
                    parts.append(f'totals differ ({v2u_t} / {v2o_t} / {v1u_t} / {v1o_t})')
                if any_error:
                    err_methods = [
                        name for name, err in [('V2 Ord', error), (
                            'V2 Unord', v2_unordered_error), ('V1 Unord',
                                                              v1_unordered_error), ('V1 Ord', v1_ordered_error)] if err
                    ]
                    parts.append('errors in: ' + ', '.join(err_methods))
                log.debug('  Methods disagree — %s', '; '.join(parts))
        log.debug('=' * 72)

    return render_template(
        'v2/index.html',
        input_text=input_text,
        target_input=target_input,
        results=results,
        total=total,
        breaks=breaks,
        target_time=target_time,
        target_achieved_at=target_achieved_at,
        detected_ids=detected_ids,
        error=error,
        order_warning=order_warning,
        order_error=order_error,
        v1_ordered=v1_ordered,
        v1_ordered_total=v1_ordered_total,
        v1_ordered_breaks=v1_ordered_breaks,
        v1_ordered_error=v1_ordered_error,
        v1_unordered=v1_unordered,
        v1_unordered_total=v1_unordered_total,
        v1_unordered_breaks=v1_unordered_breaks,
        v2_unordered=v2_unordered,
        v2_unordered_total=v2_unordered_total,
        v2_unordered_breaks=v2_unordered_breaks,
        v2_unordered_error=v2_unordered_error,
        methods_differ=methods_differ,
        v1_unordered_error=v1_unordered_error,
    )


if __name__ == "__main__":
    app.register_blueprint(v2_bp)
    app.run(debug=True, host="0.0.0.0", port=5001)
