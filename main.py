#! /usr/bin/env python3

from flask import Flask, render_template, request

from hour_calculator import HourCalculator
from v2.app import v2_bp

app = Flask(__name__)
app.register_blueprint(v2_bp, url_prefix='/v2')


@app.route('/')
def index(background=False):
    return render_template('index.html', bkgrnd=background, show_banner=True)


@app.route('/', methods=['POST'])
def index_post(background=False):

    time_input = request.form['time_input'].replace('\\n', '\n')
    time_input_print = time_input.replace('\r\n', '\n')
    print(f'V1 time_input:\n{time_input_print}')

    try:
        hours, breaks, metadata = HourCalculator(time_input).calculate(ordered=True)
        success = True
        total = hours['$total']
        del hours['$total']

        calculated_hours = []
        for chg, hrs in hours.items():
            calculated_hours.append([chg + ' =', hrs])

        calculated_hours.append(['total:', total])

    except RuntimeError as re:
        print(re)
        success, breaks = False, None
        calculated_hours = re
    except ValueError as ve:
        print(ve)
        success, breaks = False, None
        calculated_hours = ve
    except Exception as e:
        success, breaks = False, None
        calculated_hours = e

    try:
        hours_ord, breaks_ord, metadata = HourCalculator(time_input).calculate(ordered=False)
        success_ord = True
        total_ord = hours_ord['$total']
        del hours_ord['$total']

        calculated_hours_ord = []
        for chg, hrs in hours_ord.items():
            calculated_hours_ord.append([chg + ' =', hrs])

        calculated_hours_ord.append(['total:', total_ord])

        target_time = metadata['target_time']

    except RuntimeError as re:
        print(re)
        success_ord, breaks_ord, target_time = False, None, None
        calculated_hours_ord = re
    except ValueError as ve:
        print(ve)
        success_ord, breaks_ord, target_time = False, None, None
        calculated_hours_ord = ve
    except Exception as e:
        success_ord, breaks_ord, target_time = False, None, None
        calculated_hours_ord = e

    print('calculated_hours:    ', calculated_hours)
    print('calculated_hours_ord:', calculated_hours_ord)

    double_results = str(calculated_hours) != str(calculated_hours_ord)
    double_breaks = str(breaks) != str(breaks_ord)
    return render_template('index.html',
                           bkgrnd=background,
                           show_banner=False,
                           success=success,
                           time_input=time_input,
                           breaks=format_breaks(breaks),
                           calculated_hours=calculated_hours,
                           success_ord=success_ord,
                           breaks_ord=format_breaks(breaks_ord),
                           calculated_hours_ord=calculated_hours_ord,
                           double_results=double_results,
                           double_breaks=double_breaks,
                           target_time=target_time)


@app.route('/space')
def space():
    return index(background=True)


@app.route('/space', methods=['POST'])
def space_post():
    return index_post(background=True)


@app.route('/help')
def help():
    return render_template('help.html')


def format_breaks(breaks):
    if breaks is None:
        return breaks
    for brk in breaks:
        for i in range(2):
            hour = int(brk[i][:brk[i].find(':')])
            if hour < 12:
                brk[i] += 'a'
            elif hour == 12:
                brk[i] += 'p'
            else:
                brk[i] = str(int(brk[i][:brk[i].find(':')]) - 12) + brk[i][brk[i].find(':'):] + 'p'

    return breaks


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port='5001')
