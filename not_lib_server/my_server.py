import socket
from PIL import Image
from io import BytesIO

IMG_X = 32
IMG_Y = 64
RETRY_NUM = 5
TIMEOUT = 3


class MyServer():
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(1)

    def run(self):
        while 1:
            self.connection, self.client_address = self.sock.accept()
            self.request = ''
            first_line, self.headers, self.data = HttpUtils.receive_all(self.connection, TIMEOUT)

            if self.headers is not None:
                print('CLIENT: ' + first_line)
                first_line_sp = first_line.split(' ')
                self.type = first_line_sp[0]
                self.domain = first_line_sp[1]
                self.version = first_line_sp[2]
                if self.type == 'GET':
                    self.do_GET()
                elif self.type == 'CONNECT':
                    self.do_CONNECT()

    def do_GET(self):
        self.compress_and_send()
        self.connection.close()

    def do_CONNECT(self):
        self.send_response(200)
        self.send_all(b'')

    def compress_and_send(self):
        compressed = False
        response = HttpUtils.my_get(self.domain)
        print("RESOURCE: " + response['path'])
        self.send_response(response['status_code'])
        content = response['content']
        new_len = 0

        for key, val in dict(response['headers']).items():
            if key.lower() == 'content-type':
                self.send_header(key, val)
                if val.lower() in ('image/png', 'image/jpg'):
                    print('image found')
                    img = Image.open(BytesIO(response['content']))
                    compressed = True
                    if img.size[0] > IMG_X or img.size[1] > IMG_Y:
                        print('compressing')
                        img.thumbnail((IMG_X, IMG_Y), Image.ANTIALIAS)
                        content = self.img_to_arr(img)
                        new_len = len(content)
            elif key.lower() in ('content-length', 'allow'):
                if compressed:
                    self.send_header(key, str(new_len))
                else:
                    self.send_header(key, val)
        self.send_all(content)

    def img_to_arr(self, img):
        arr = BytesIO()
        img.save(arr, format=img.format)
        return arr.getvalue()

    def send_response(self, code):
        self.request += ('%s %d %s\r\n' % ('HTTP/1.0', code, 'OK'))

    def send_header(self, key, val):
        self.request += ('%s: %s\r\n' % (key, val))

    def send_all(self, data):
        try:
            self.connection.send((self.request + '\r\n').encode() + data)
        except Exception as e:
            print(type(e))


class HttpUtils():
    @staticmethod
    def receive_all(sock, timeout):
        try:
            sock.settimeout(timeout)
            all_data = b''
            while 1:
                next_byte = sock.recv(1)
                all_data += next_byte
                if len(all_data) == 0:
                    break
                if chr(all_data[-1]) == '\n' \
                        and chr(all_data[-2]) == '\r' \
                        and chr(all_data[-3]) == '\n' \
                        and chr(all_data[-4]) == '\r':

                    path, headers = HttpUtils.parse_http(all_data.decode())
                    data = b''
                    if 'Content-Length' in headers.keys():
                        while int(headers['Content-Length']) > len(data):
                            data += sock.recv(int(headers['Content-Length']) - len(data))
                    return path, headers, data
            return None, None, None
        except socket.timeout:
            return None, None, None

    @staticmethod
    def parse_http(text):
        lines = text.split('\r\n')
        path = lines[0]
        headers = {}
        for line in lines[1:]:
            if line != '':
                line_args = line.split(': ')
                headers[line_args[0]] = line_args[1]
        return path, headers

    @staticmethod
    def my_get(url):
        for i in range(RETRY_NUM):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            req_url = '/'.join(url[7:].split('/')[1:])
            domain = url[7:].split('/')[0]
            sock.connect((domain, 80))

            plain_headers = 'Host: %s\r\n' \
                            'User-Agent: python\r\n' \
                            'Accept-Encoding: gzip, deflate\r\n' \
                            'Accept: */*\r\n' \
                            'Connection: keep-alive\r\n' % str(domain)

            sock.send(('GET /%s HTTP/1.0\r\n%s\r\n' % (req_url, plain_headers)).encode())

            path, headers, data = HttpUtils.receive_all(sock, TIMEOUT)

            if headers is None:
                continue

            return {
                'path': path,
                'headers': headers,
                'content': data,
                'version': path.split(' ')[0],
                'status_code': int(path.split(' ')[1]),
            }
