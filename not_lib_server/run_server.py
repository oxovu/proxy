import sys
from not_lib_server.my_server import MyServer


def main():
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        print("wrong number of arguments")
        sys.exit(1)
    server = MyServer('', port)
    server.run()


if __name__ == '__main__':
    main()
