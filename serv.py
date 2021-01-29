from hour_calculator import HourCalculator
from http.server import HTTPServer, BaseHTTPRequestHandler
from string import Template
from urllib.parse import urlparse, parse_qs


class Serv(BaseHTTPRequestHandler):

    def do_GET(self, data=None):
        print('do_GET init')
        # if self.path == '/':
        #     self.path = '/index.html'
        # else:
        #     print(self.path)
        # print('data', data)
        # try:
        #     file_to_open = open(self.path[1:]).read()
        #     self.send_response(200)
        # except:
        #     file_to_open = "File not found"
        #     self.send_response(404)
        # self.end_headers()
        # self.wfile.write(bytes(file_to_open, 'utf-8'))

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
        # print(idx)
        template_idx = Template(idx)
        idx = template_idx.substitute(time_input=time_input, calculated_hours=calculated_hours)
        # print(idx)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(idx.encode())

    def do_POST(self):
        print('do_POST init')
        # print(self.__builtins__.__dict__)
        # for attr in dir(self):
            # print("self.%s = %r" % (attr, getattr(self, attr)))
        content_length = int(self.headers['Content-Length'])
        data_input = bytes.decode(self.rfile.read(content_length))
        # print(data_input)
        form_vals = parse_qs(urlparse(data_input).path)
        # print('form vals:', form_vals)

        # path = urlparse(data_input).path
        # print('path:', path)

        time_input = form_vals['time_input'][0]
        hours = HourCalculator(time_input).calculate()

        total = hours['$total']
        del hours['$total']

        calculated_hours = ''
        for chg, hrs in hours.items():
            calculated_hours += str('<b>' + chg + '</b>' + ' ' + str(hrs) + '\n')
        calculated_hours += '<b>total</b> ' + str(total)

        print('time_input:', time_input)
        print('calculated_hours:', calculated_hours)

        # form_vals['calculated_hours'] = ['CHARGES\noh == 4.933 hrs\nc == 5.834 hrs\ntotal: 10.8']
        form_vals['calculated_hours'] = calculated_hours

        html_data = {'time_input': time_input,
                     'calculated_hours': calculated_hours}

        # self.path = path
        self.do_GET(data=html_data)


httpd = HTTPServer(('localhost', 8080), Serv)
httpd.serve_forever()
