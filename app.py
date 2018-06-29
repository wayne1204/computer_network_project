from server import Server
import sys

if __name__ == '__main__':
    HOST, PORT = "", int(sys.argv[1])
    ser = Server(HOST, PORT)
    ser.run()
