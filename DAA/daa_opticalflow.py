import asyncio
from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw)

import threading
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import mode
from argparse import ArgumentParser
import time
import threading
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s',)





stop_event=threading.Event()

def daa_opticalflow(stop_event):


# TODO pass cmd args here from runsim ???????



    ap = ArgumentParser()
    ap.add_argument('--HITL_PX4',action="store_true", default=False, dest='HITL_PX4')
    ap.add_argument('--HITL_DAA',action="store_true", default=False, dest='HITL_DAA')
    ap.add_argument('-pscale', '--pyr_scale', default=0.5, type=float,help='Image scale (<1) to build pyramids for each image')
    ap.add_argument('-l', '--levels', default=3, type=int, help='Number of pyramid layers')
    ap.add_argument('-w', '--winsize', default=15, type=int, help='Averaging window size')
    ap.add_argument('-i', '--iterations', default=3, type=int,help='Number of iterations the algorithm does at each pyramid level')
    ap.add_argument('-pn', '--poly_n', default=5, type=int,help='Size of the pixel neighborhood used to find polynomial expansion in each pixel')
    ap.add_argument('-psigma', '--poly_sigma', default=1.1, type=float,help='Standard deviation of the Gaussian that is used to smooth derivatives used as a basis for the polynomial exp')
    ap.add_argument('-th', '--threshold', default=10.0, type=float, help='Threshold value for magnitude')
    ap.add_argument('-s', '--size', default=10, type=int, help='Size of accumulator for directions map')
    args = vars(ap.parse_args())
    directions_map = np.zeros([args['size'], 5])



    HITL_PX4=args['HITL_PX4']
    HITL_DAA=args['HITL_DAA']


    # If HITL connect over mavlink
    if HITL_DAA:
        # Init the drone
        #drone = System()
        #drone.connect(system_address="udp://:14550") # Not picking up UDP for some reason
        #await drone.connect(system_address="serial:///dev/ttyACM0:115200") # Working, straight from USB
        #await drone.connect(system_address="serial:///dev/ttyACM0:115200") #57600,115200

        # TODO - add settings option for remote sim PC on network
        cap = cv.VideoCapture('http://192.168.1.148:5000/video_feed') # Stream remotely

    else:

        #cap = cv.VideoCapture(0) # RaspPi default camera
        cap = cv.VideoCapture('http://0.0.0.0:5000/video_feed') # Stream
        #cap = cv.VideoCapture('dronedirecthit.avi')



    frame_previous = cap.read()[1]
    
    gray_previous = cv.cvtColor(frame_previous, cv.COLOR_BGR2GRAY)
    hsv = np.zeros_like(frame_previous)
    hsv[:, :, 1] = 255
    param = {
        'pyr_scale': args['pyr_scale'],
        'levels': args['levels'],
        'winsize': args['winsize'],
        'iterations': args['iterations'],
        'poly_n': args['poly_n'],
        'poly_sigma': args['poly_sigma'],
        'flags': cv.OPTFLOW_LK_GET_MIN_EIGENVALS
    }

    while True:

        grabbed, frame = cap.read()
        if not grabbed:
            break
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        flow = cv.calcOpticalFlowFarneback(gray_previous, gray, None, **param)


        mag, ang = cv.cartToPolar(flow[:, :, 0], flow[:, :, 1], angleInDegrees=True)
        ang_180 = ang/2
        gray_previous = gray
        move_sense = ang[mag > args['threshold']]
        move_mode = mode(move_sense)[0]

        if move_mode.size > 0:
            if 10 < move_mode <= 100:
                directions_map[-1, 0] = 1
                directions_map[-1, 1:] = 0
                directions_map = np.roll(directions_map, -1, axis=0)
            elif 100 < move_mode <= 190:
                directions_map[-1, 1] = 1
                directions_map[-1, :1] = 0
                directions_map[-1, 2:] = 0
                directions_map = np.roll(directions_map, -1, axis=0)
            elif 190 < move_mode <= 280:
                directions_map[-1, 2] = 1
                directions_map[-1, :2] = 0
                directions_map[-1, 3:] = 0
                directions_map = np.roll(directions_map, -1, axis=0)
            elif 280 < move_mode or move_mode < 10:
                directions_map[-1, 3] = 1
                directions_map[-1, :3] = 0
                directions_map[-1, 4:] = 0
                directions_map = np.roll(directions_map, -1, axis=0)
            else:
                directions_map[-1, -1] = 1
                directions_map[-1, :-1] = 0
                directions_map = np.roll(directions_map, 1, axis=0)


        
            loc = directions_map.mean(axis=0).argmax()
            if loc == 0:
                text = 'Moving down'
            elif loc == 1:
                text = 'Moving to the right'
            elif loc == 2:
                text = 'Moving up'
            elif loc == 3:
                text = 'Moving to the left'

            else:
                text = 'WAITING'
        else:
            text = 'WAITING'

        #print(text)

        if not text=="WAITING":
            print('Detection!')
            # Using airsim drone
            #if not HITL_PX4:
            #    break
            # We're running on offboard computer
            if HITL_DAA:
                
                # Move 1m to the right
                # Not quite working, throws errors!
                #loop = asyncio.get_event_loop()
                #loop.run_until_complete(do_avoid())

                break
            else:
                break
        
        # Thread kill
        if stop_event.is_set():
            break
        


# Use offboard control to move the drone 5 to the right
# Great - but we will dangerously lose control of the drone due to global motion false positives
#
# 
async def do_avoid():

    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600")

    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))

    print("-- Starting offboard")
    try:
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error code: {error._result.result}")
        print("-- Disarming")
     #   await drone.action.disarm()
        return

    print("-- Emergency avoid")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 10.0, 0.0, 0.0))
    

    print("-- Stopping offboard")
    try:
        await drone.offboard.stop()
    except OffboardError as error:
        print(f"Stopping offboard mode failed with error code: {error._result.result}")



def start():
    t = threading.Thread(target=daa_opticalflow, args=(stop_event,), daemon=True)
    #t = threading.Thread(target=test, args=(stop_event,), daemon=True)
    t.start()
    return t

def stop():
    stop_event.set()



# Test
def test():
    t=start()
    #t.is_alive()
    time.sleep(30)
    stop()
    t.join()


if __name__ == '__main__':
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(daa_opticalflow(stop_event))


    #test()