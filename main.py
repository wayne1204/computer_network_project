#!/usr/bin/env python
#
# Project: Video Streaming with Flask
# Author: Log0 <im [dot] ckieric [at] gmail [dot] com>
# Date: 2014/12/21
# Website: http://www.chioka.in/
# Description:
# Modified to support streaming out with webcams, and not just raw JPEGs.
# Most of the code credits to Miguel Grinberg, except that I made a small tweak. Thanks!
# Credits: http://blog.miguelgrinberg.com/post/video-streaming-with-flask
#
# Usage:
# 1. Install Python dependencies: cv2, flask. (wish that pip install works like a charm)
# 2. Run "python main.py".
# 3. Navigate the browser to the local webpage.
from flask import Flask, render_template, Response
from camera import VideoCamera
import numpy as np
import cv2
from PIL import Image

shape = (480, 640, 3)

points_perMove = 2.9
app = Flask(__name__)

def frame_transform2bytes(frame, quality):
    ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return jpeg.tobytes()

def get_points(q):
    if( q >= 100):
        return 100
    elif( q <= 1):
        return 1
    return q

@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    last_frame = np.zeros(shape)
    last_intense = 0
    count = 0
    threshold = 0.03
    mask_arr = None
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
        print("Current quality: ", q)
        q-=1
        if d_intense > 0.01:
            bias = np.where(intense_per_pix < 0.1, intense_per_pix, 25)
            bias = np.where(bias > 24, bias, 0)
            q += points_perMove
            #print("something moving: ", intense-last_intense)
        q = get_points(q)

        yield( b'--frame\r\n'+ b'Content-Type: image/jpeg\r\n\r\n'+ frame_transform2bytes(t_frame, int(q)) + b'\r\n\r\n' )
        last_frame = frame
        last_intense = intense

@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
