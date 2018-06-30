from server2 import Server
import sys

if __name__ == '__main__':
    HOST, PORT = "172.20.10.4", int(sys.argv[1])
    ser = Server(HOST, PORT)
    ser.run()
