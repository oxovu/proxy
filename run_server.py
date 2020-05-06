import sys
from http.server import HTTPServer
from handler import Handler


def main():
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        print("wrong number of arguments")
        sys.exit(1)
    server = HTTPServer(('', port), Handler)
    server.serve_forever()


if __name__ == '__main__':
    main()
