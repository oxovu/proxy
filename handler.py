from http.server import BaseHTTPRequestHandler
from io import BytesIO
import requests
from PIL import Image

IMG_X = 32
IMG_Y = 64


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        content = self.compress()
        if content is None:
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()
            self.wfile.write("<h1>No content<h1>".encode())
        else:
            self.wfile.write(content)

    def do_CONNECT(self):
        self.send_response(200)
        self.end_headers()

    def compress(self):
        compress = False
        response = requests.get(self.path)
        self.send_response(response.status_code)
        content = response.content
        new_len = 0

        for key, val in dict(response.headers).items():
            if key.lower() == 'content-type':
                self.send_header(key, val)
                if val.lower() in ('image/png', 'image/jpg'):
                    img = Image.open(BytesIO(response.content))
                    compress = True
                    if img.size[0] > IMG_X or img.size[1] > IMG_Y:
                        img.thumbnail((IMG_X, IMG_Y), Image.ANTIALIAS)
                        content = self.img_to_arr(img)
                        new_len = len(content)
            elif key.lower() in ('content-length', 'allow'):
                if compress:
                    self.send_header(key, str(new_len))
                else:
                    self.send_header(key, val)
        self.end_headers()
        return content

    def img_to_arr(self, img):
        arr = BytesIO()
        img.save(arr, format=img.format)
        return arr.getvalue()
