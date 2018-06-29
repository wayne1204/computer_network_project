import socket
import threading
import numpy as np
import cv2
from camera import VideoCamera
from PIL import Image

CAMERA = VideoCamera()
SHAPE = (480, 640, 3)
POINTS = 2.9

def get_points(q):
    if(q >= 100):
        return 100
    elif(q <= 1):
        return 1
    return q

def frame_transform2bytes(frame, quality):
    ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return jpeg.tobytes()

def gen(CAMERA):
    last_frame = np.zeros(SHAPE)
    t_frame = np.zeros(SHAPE)
    bias = np.zeros(SHAPE)
    last_intense = 0

    q = 50
    while True:
        t_frame = CAMERA.get_frame()
        intense_per_pix = (d_frame/255.)**2
        intense = (np.mean(intense_per_pix))

        d_frame = (t_frame) - (last_frame)
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
        yield b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n'+ frame_transform2bytes(t_frame, int(q))+ b'\r\n\r\n'

        last_frame = t_frame
        last_intense = intense

class Server(object):
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((host, port))
        print("Stream Server Running on http://{}:{}/".format(host, port))
    
    def run(self):
        while(True):
            client, address = self.s.accept()
            print(str(address)+" connected")
            try:
                req_type, req_content = get_client_data(client)
                print("REQUEST TYPE: ",req_type)
                if(req_type == "GET"):
                    threading.start_new_thread(self.get_handler, (req_content))
                elif(req_type == "POST"):
                    threading.start_new_thread(self.post_handler, (req_content))

            except Exception as e:
                print(e)
                print("except")
            client.close()

    def get_handler(self, content):
        try:
            if(content== "stream"):
                http_req = bytes("HTTP/1.0 200 OK\nContent-Type: multipart/x-mixed-replace; boundary=frame\n\n", 'utf-8')
                client.send(http_req)
                for frame_rep in gen(CAMERA):
                    client.send(frame_rep)
            elif(content == ""):
                html = open("index.html", 'r')
                body = html.read()
                http_req = bytes("HTTP/1.0 200 OK\nContent-Type: text/html\n\n"+body, 'utf-8')
                client.send(http_req)
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
            http_req = bytes("HTTP/1.0 404 Not found\nContent-Type: text/html\n\n"+body, 'utf-8')
            client.send(http_req)
    
    def post_handler(self, content):
        pass



