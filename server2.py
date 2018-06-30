import socket
import _thread
import numpy as np
import cv2
import multiprocessing as mp
import threading as td
from camera import VideoCamera
from PIL import Image

CAMERA = VideoCamera()
SHAPE = (480, 640, 3)
POINTS = 2.9
QUALITY = 100


def get_points(q):
    if(q >= 100):
        return 100
    elif(q <= 1):
        return 1
    return q


def frame_transform2bytes(frame, quality):
    ret, jpeg = cv2.imencode(
        '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return jpeg.tobytes()


def gen(CAMERA):
    last_frame = np.zeros(SHAPE)
    t_frame = np.zeros(SHAPE)
    bias = np.zeros(SHAPE)
    last_intense = 0

    q = 50
    while True:
        t_frame = CAMERA.get_frame()
        d_frame = (t_frame) - (last_frame)
        intense_per_pix = (d_frame/255.)**2
        intense = (np.mean(intense_per_pix))

        d_intense = intense - last_intense
        #print(intense_per_pix)
        #print("Current quality: ", q)
        q -= 1
        if d_intense > 0.01:
            q += POINTS
            bias = np.where(intense_per_pix < 0.1, intense_per_pix, 25)
            bias = np.where(bias > 24, bias, 0)
            #print("something moving: ", intense-last_intense)
        q = get_points(q)
        yield b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + frame_transform2bytes(t_frame, int(QUALITY)) + b'\r\n\r\n'

        last_frame = t_frame
        last_intense = intense

class ClientHandler():#td.Thread):
    def __init__(self, socket, id):
        self.normal_sock = socket
        self.stream_sock = None
        self.id = id
        self.QUALITY = 100
        #td.Thread.__init__(self)

    def set_StreamSock(self, socket):
        self.stream_sock = socket

    def gen(self, CAMERA):
        last_frame = np.zeros(SHAPE)
        t_frame = np.zeros(SHAPE)
        bias = np.zeros(SHAPE)
        last_intense = 0

        q = 50
        while True:
            t_frame = CAMERA.get_frame()
            d_frame = (t_frame) - (last_frame)
            intense_per_pix = (d_frame/255.)**2
            intense = (np.mean(intense_per_pix))

            d_intense = intense - last_intense
            #print(intense_per_pix)
            #print("Current quality: ", q)
            q -= 1
            if d_intense > 0.01:
                q += POINTS
                bias = np.where(intense_per_pix < 0.1, intense_per_pix, 25)
                bias = np.where(bias > 24, bias, 0)
                #print("something moving: ", intense-last_intense)
            q = get_points(q)
            yield b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + frame_transform2bytes(t_frame, int(self.QUALITY)) + b'\r\n\r\n'

            last_frame = t_frame
            last_intense = intense
    
    
    def get_client_data(self):
        print("Getting client data")
        req = (self.client.recv(1000)).decode('utf-8')
        #print(req)
        req_type = req.split()[0]
        #request = req.split()[1].partition("/")[-1]
        return req_type, req

    def run(self, req_type, req_content):
        try:
            #req_type, req_content = self.get_client_data()
            print("REQUEST TYPE: ", req_type)

            if(req_type == "GET"):
                new_thread = td.Thread(target=self.get_handler, args=(req_content,))
                new_thread.start()
            
            elif(req_type == "POST"):
                new_thread = td.Thread(target=self.post_handler, args=(req_content,))
                new_thread.start()
        except Exception as e:
            print("=== except ===")
            print(e)

    def get_handler(self, content):
        try:
            content = content.split()[1].partition("/")[-1]
            
            if(content == "stream"):
                http_req = bytes(
                    "HTTP/1.0 200 OK\nContent-Type: multipart/x-mixed-replace; boundary=frame\n\n", 'utf-8')
                self.stream_sock.send(http_req)
                gen_obj = self.gen(CAMERA)
                print(id(gen_obj))
                for frame_rep in gen_obj:
                    # print("Sent BYTES: ", len(frame_rep))
                    self.stream_sock.send(frame_rep)
            
            elif(content == ""):
                html = open("index.html", 'r')
                body = html.read()
                http_req = bytes(
                    "HTTP/1.0 200 OK\nContent-Type: text/html\n\n"+body, 'utf-8')
                self.normal_sock.send(http_req)
                html.close()
        except Exception as e:
            print(e)
            body = """
                <html>
                <body>
                <h1>404 Not found</h1>
                </body>
                </html>
                """
            http_req = bytes(
                "HTTP/1.0 404 Not found\nContent-Type: text/html\n\n"+body, 'utf-8')
            self.normal_sock.send(http_req)

    def post_handler(self, content): 
        print(content)
        content = (content.split("\r\n\r\n")[1])
        print(content)
        content = content.split("=")[-1]
        if(content == "HIGH"):
            self.QUALITY = 100
        elif(content == "MEDIUM"):
            self.QUALITY = 10
        elif(content == "LOW"):
            self.QUALITY = 1
        print("POST CONTENT: ", content)
 


class Server(object):
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((host, port))
        self.client_list = []
        print("Stream Server Running on http://{}:{}/".format(host, port))

    def get_client_data(self, client):
        req = (client.recv(1000)).decode('utf-8')
        #print(req)
        req_type = req.split()[0]
        #request = req.split()[1].partition("/")[-1]
        return req_type, req

    def run(self):
        self.s.listen(20)
        while(True):
            print("Waiting...")
            client, address = self.s.accept()
            address = (address[0])
            req_type, content = self.get_client_data(client)
            try:
                if(content.split()[1].partition("/")[-1] == 'stream'):
                    for i, c in enumerate(self.client_list):
                        if(c.id == address):
                            print("Stream req")
                            c.set_StreamSock(client)
                            c.run(req_type, content)
                            break
                else:
                    for i, c in enumerate(self.client_list):
                        if(c.id == address):
                            print("Found address")
                            tmp = c.normal_sock
                            c.normal_sock = client
                            c.run(req_type, content)
                            tmp.close()
                            break
                    else:
                        c = ClientHandler(client, address)
                        print("Client not found")
                        self.client_list.append(c)
                        c.run(req_type, content)
            except Exception as e:
                print(e)
