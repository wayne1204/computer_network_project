import socket
import sys
from camera import VideoCamera
import cv2
import numpy as np
from PIL import Image
HOST, PORT = "", int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
camera = VideoCamera()
shape = (480, 640, 3)
points_perMove = 2.9

def frame_transform2bytes(frame, quality):
    ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return jpeg.tobytes()

def get_points(q):
    if(q >= 100):
        return 100
    elif(q <= 1):
        return 1
    return q

def gen(camera):
    last_frame = np.zeros(shape)
    last_intense = 0
    count = 0
    threshold = 0.03
    bias = np.zeros(shape)
    q = 50
    while True:
        t_frame = np.zeros(shape)
        frame = None
        frame = camera.get_frame()
        t_frame = frame
        d_frame = (frame) - (last_frame)
        intense_per_pix = (d_frame/255.)**2
        intense = (np.mean(intense_per_pix))
        d_intense = intense - last_intense
        #print(intense_per_pix)
        #print("Current quality: ", q)
        q -= 1
        if d_intense > 0.01:
            bias = np.where(intense_per_pix < 0.1, intense_per_pix, 25)
            bias = np.where(bias > 24, bias, 0)
            q += points_perMove
            #print("something moving: ", intense-last_intense)
        q = get_points(q)
        yield b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n'+ frame_transform2bytes(t_frame, int(q))+ b'\r\n\r\n'
        last_frame = frame
        last_intense = intense

def get_client_data(c):
    resp = (client.recv(1000)).decode('utf-8')
    print(resp)
    request = resp.split()[1].partition("/")[-1]
    return request

while(True):
    s.listen(0)
    print("Stream Server Running on http://{}:{}/".format(HOST, PORT))
    while(True):
        client, address = s.accept()
        print(str(address)+" connected")
        try:
            request = get_client_data(client)
            print("Get request: ",request)
            try:
                if(request == "png"):
                    body = frame_transform2bytes(camera.get_frame(), 100)
                    http_req = bytes("HTTP/1.0 200 OK\nContent-Type: image/png\n\n", 'utf-8') + body
                    client.send(http_req)
                elif(request == "stream"):
                    http_req = bytes("HTTP/1.0 200 OK\nContent-Type: multipart/x-mixed-replace; boundary=frame\n\n", 'utf-8')
                    client.send(http_req)
                    for frame_rep in gen(camera):
                        client.send(frame_rep)
                elif(request == ""):
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
        except Exception as e:
            print(e)
            print("except")
        client.close()
