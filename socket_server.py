import socket
import sys
from camera import VideoCamera
import cv2
import numpy as np

HOST, PORT = "", 80
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))

while(True):
    s.listen(0)
    print("The Web server for HW2 is running..")
    while(True):
        #try:
            client, address = s.accept()
            print(str(address)+" connected")
            try:
                resp = (client.recv(1000)).decode('ascii')
                print(resp)
                request = resp.split()[1].partition("/")[2]
                print(request)
                file_req = request.partition(".")
                try:
                    if(file_req[len(file_req)-1] == "png"):
                        image = open("./"+request, 'rb')
                        body = image.read();
                        http_req = bytes("HTTP/1.0 200 OK\nContent-Type: image/png\n\n", 'utf-8') + body
                        client.send(http_req)
                        image.close()
                    elif(file_req[len(file_req)-1] == "mp4"):
                        image = open("./"+request, 'rb')
                        body = image.read();
                        http_req = bytes("HTTP/1.0 200 OK\nContent-Type: video/mpeg4\n\n", 'utf-8') + body
                        client.send(http_req)
                        image.close()
                    elif(file_req[len(file_req)-1] == "html"):
                        html = open(request, 'r')
                        body = html.read()
                        http_req = bytes("HTTP/1.0 200 OK\nContent-Type: text/html\n\n"+body, 'ascii')
                        client.send(http_req)
                        html.close()
                    else:
                        html = open(request, 'r')
                except Exception as e:
                    print(e)
                    body = """
                        <html>
                        <body>
                        <h1>404 Not found</h1>
                        </body>
                        </html>
                        """
                    http_req = bytes("HTTP/1.0 404 Not found\nContent-Type: text/html\n\n"+body, 'ascii')
                    client.send(http_req)
            except:
                print("except")
            client.close()
            '''
        except KeyboardInterrupt:
            print("Exit")
            s.close()
            sys.exit()
            '''
