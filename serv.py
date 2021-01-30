from hour_calculator import HourCalculator
from http.server import HTTPServer, BaseHTTPRequestHandler
from string import Template
from urllib.parse import urlparse, parse_qs


class Serv(BaseHTTPRequestHandler):

    def do_GET(self, data=None):
        if self.path != '/':
            print('init not index')
            self.send_response(404)
            self.end_headers()
            self.wfile.write('File not found'.encode())
            return

        elif data and 'time_input' in data and 'calculated_hours' in data:
            time_input = data['time_input']
            calculated_hours = data['calculated_hours'].replace('\n', '<br>')
        else:
            print('type data:', type(data))
            print('data:', data)
            time_input = ''
            calculated_hours = ''

        idx = open('index.html').read()
        template_idx = Template(idx)
        idx = template_idx.substitute(time_input=time_input, calculated_hours=calculated_hours)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(idx.encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data_input = bytes.decode(self.rfile.read(content_length))
        form_vals = parse_qs(urlparse(data_input).path)
        # print('form vals:', form_vals)

        time_input = form_vals['time_input'][0]
        try:
            hours = HourCalculator(time_input).calculate()

            total = hours['$total']
            del hours['$total']

            calculated_hours = ''
            for chg, hrs in hours.items():
                calculated_hours += str('<b>' + chg + '</b>' + ' ' + str(hrs) + '\n')
            calculated_hours += '<b>total</b> ' + str(total)
        except ValueError as e:
            print(e)
            calculated_hours = 'Invalid time input'

        # print('time_input:', time_input)
        # print('calculated_hours:', calculated_hours)

        form_vals['calculated_hours'] = calculated_hours
        html_data = {'time_input': time_input,
                     'calculated_hours': calculated_hours}

        self.do_GET(data=html_data)


httpd = HTTPServer(('localhost', 8080), Serv)
httpd.serve_forever()
