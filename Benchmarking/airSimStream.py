
#Source: https://github.com/Microsoft/AirSim/issues/892

from flask import Flask, render_template_string, Response

import airsim
import cv2
import numpy as np
import threading
import time


CAMERA_NAME = 'DroneCamera'
IMAGE_TYPE = airsim.ImageType.Scene
DECODE_EXTENSION = '.jpg'

client=None
exit_event = threading.Event()
th=None

def frame_generator():
    while (True):
        response_image = client.simGetImage(CAMERA_NAME, IMAGE_TYPE,vehicle_name='Drone')
        np_response_image = np.asarray(bytearray(response_image), dtype="uint8")
        decoded_frame = cv2.imdecode(np_response_image, cv2.IMREAD_COLOR)
        ret, encoded_jpeg = cv2.imencode(DECODE_EXTENSION, decoded_frame)
        frame = encoded_jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type:image/jpeg\r\n'
               b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n'
               b'\r\n' + frame + b'\r\n')
               
        if exit_event.is_set():
            break

app = Flask(__name__)
@app.route('/')
def index():
    return render_template_string(
        """
            <html>
            <head>
                <title>AirSim Streamer</title>
            </head>
            <body>
                <h1>AirSim Streamer</h1>
                <hr />
                Please use the following link: <a href="/video_feed">http://localhost:5000/video_feed</a>
            </body>
            </html>
        """
        )

@app.route('/video_feed')
def video_feed():
    return Response(
            frame_generator(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )



def start_stream():
    global client
    global th
    #sys.stdout=None
    client = airsim.MultirotorClient()
    client.confirmConnection()
    th = threading.Thread(target=lambda: app.run(host='0.0.0.0', debug=False, port=5000, use_reloader=False), daemon=True).start()
    return th

def stop_stream():
    exit_event.set()



if __name__ == '__main__':
    start_stream()
    while True:
        time.sleep(5000)
    #stop_stream()


   