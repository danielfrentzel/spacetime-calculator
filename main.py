from flask import Flask, render_template, request
from hour_calculator import HourCalculator

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def index_post():
    time_input = request.form['time_input']
    try:
        hours, breaks = HourCalculator(time_input).calculate()
        total = hours['$total']
        del hours['$total']

        # todo
        # keep order
        # display breaks (in minutes)

        calculated_hours = []
        for chg, hrs in hours.items():
            calculated_hours.append([chg + ' ==', hrs])

        calculated_hours.append(['total:', total])
        print(calculated_hours)

    except ValueError as e:
        print(e)
        calculated_hours = [['Invalid time input', '']]
    return render_template('index.html', time_input=time_input, breaks=breaks, calculated_hours=calculated_hours)


@app.route('/help')
def help():
    return render_template('help.html')


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port='5000')
