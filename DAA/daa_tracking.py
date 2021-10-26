
import asyncio
from mavsdk import System
from mavsdk.offboard import (OffboardError, PositionNedYaw)

import threading
import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import mode
from argparse import ArgumentParser
import time
import imutils
import queue
import copy
from bboxmerge import merge_bboxes, IOU, inside_bbox, bbox_to_rect
import threading
import logging
logging.basicConfig(level=logging.DEBUG,
                    filename="daa.log",
                    format='(%(threadName)-9s) %(message)s',)



TRACKER_DELTA_THRESHHOLD=1.05
TRACKER_OVERWRITE_THRESH=10

DETECT_THRESHOLD_MAX=100
BBOX_MERGE_OFFSET=50
DETECT_REJECT_THRESH = 100

#(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

#print(major_ver,".",minor_ver)


class HQueue(queue.Queue):
    def show_value(self, i):
        print(self.queue[i])

    def sum(self):
        if len(self.queue)>0:
            return sum(self.queue)
        else:
            return 0

    def ave(self):
        if len(self.queue)>0:
            return self.sum() / self.qsize()
        else:
            return 0

class DAA_Tracking:


    class UFO:
        def __init__(self,bbox):

            self.bbox = bbox # bbox in format x,y,w,h
            self.tracker = cv2.legacy.TrackerMedianFlow_create()
            self.area = self.bbox[2]*self.bbox[3]
            self.history = HQueue(25)
            self.ok = True


    def __init__(self,stop_event):

        self.UFOS=[]
        self.UFO_Count=0
        self.frames=0
        self.stop_event=stop_event


    def addUFO(self,frame,bbox):

        ufo = self.UFO(bbox)
        ufo.ok = ufo.tracker.init(frame,bbox) # tracker accepts x1,y1,x2,y2 format not x,y,w,h as docs say?
        # Only add if tracking successful
        if ufo.ok:
            self.UFOS.append(ufo)
      
    def delUFO(self,ufo):
        self.UFOS.remove(ufo)
        self.UFO_Count=self.UFO_Count-1
        


    # Determine avoid action
    def avoid_action(self,bbox,frame):

        # Based on horz/vert centers issue avoid up,down,left,right
        (x,y,w,h)=bbox
        # Move Up
        if y+(h/2) < self.half_height:
            text="Move down"
        # Move Up
        elif y+(h/2) > self.half_height:
            text="Move up"
        # Move Up
        elif x+(w/2) < self.half_width:
            text="Move right"
        # Move Up
        elif x+(w/2) > self.half_width:
            text="Move left"

        #print(text)

        #cv2.putText(frame, "Detection {}".format(text), (10, 20),
		                    #cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

   

    # Update all the trackers
    def object_tracking(self,currframe,frame):

        flag=False

        print("Tracking %d objects"%(len(self.UFOS)))

        for i,ufo in enumerate(self.UFOS):


            # Update tracker
            ok, bbox = ufo.tracker.update(currframe)


            # Draw bounding box for debug
            if ok:
        
                # TODO - these values are questionable? The bbox format in the docs is x,y,w,h
                # But x,y,x1,y1 seems to print correctly
                # So is the tracker just dodgy that it makes such a big change?
                # See end of function
               
                # If area is above threshold object approaching!
                area = (bbox[2]-bbox[0])*(bbox[3]-bbox[1])
          
                if area > self.UFOS[i].area*TRACKER_DELTA_THRESHHOLD:
         

                    #self.avoid_action(bbox,frame)

                    logging.info("Collision detection")
                    flag=True
                else:
                    #print("Waiting")
                    #logging.info("Waiting")
                    pass


                self.UFOS[i].area = area


            else:
                # Tracking failure
                #cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
                #print("Tracking failed for ID, deleting")
                logging.info("Tracking failed for ID, deleting")
                self.UFOS[i]=None
            

        # Remove deleted marked None
        self.UFOS = [i for i in self.UFOS if i is not None]

        return flag

        #input("Press return to terminate the program")

            # If history is moving away then remove
           # if ufo.history.ave() < 0:
            #    print("Moving away - Remove tracking")
        #    input("Press return to terminate the program")
        #    return True




    def object_detection(self,lastframe,currframe,frame):


        # Run every x seconds   
        #if self.frames < 25*5:
        #    return  
        #selfframes=0  

        frameDelta = cv2.absdiff(lastframe, currframe)
        frameDelta = cv2.GaussianBlur(frameDelta, (21, 21), 0)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

	    # dilate the thresholded image to fill in holes, then find contours
	    # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        rects=[]
	    # loop over the contours and assign rects
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < DETECT_THRESHOLD_MAX: #self.args["min_area"]:
                continue
		    # compute the bounding box for the contour, draw it on the frame,
		    # and update the text
            (x, y, w, h) = cv2.boundingRect(c)

            # Don't include large rects from global motion
            #if(w<200,h<200):
            rects.append([x,y,x+w,y+h])
            
           


        # Merge overlapping ROI from detection
        rects = merge_bboxes(rects)


        # Reject new rect if partially overlapping existing tracker 
        for ufo in self.UFOS:
            for r in rects[:]: # TODO Any copy weirdness if we are deleting this way?
                t,f = IOU(ufo.bbox,r,DETECT_REJECT_THRESH)
                if t:
                    rects.remove(r)
                

        # If an old tracker is within a new ddet rect by a wide margin then delete the tracker
        for i,ufo in enumerate(self.UFOS):
            for r in rects:
                if inside_bbox(r,ufo.rect,TRACKER_OVERWRITE_THRESH):
                    #print("Deleting tracker bounded by new detection rect")
                    self.UFOS[i]=None
        
        # Remove deleted marked None
        self.UFOS = [i for i in self.UFOS if i is not None]
        
            

        # Finally, add tracker
        for r in rects:
            #print("Creating new tracker: ",r)
            self.addUFO(currframe,(r[0],r[1],(r[2]-r[0]),(r[3]-r[1])))
     


    def run(self):


        logging.info("Running")


        ap = ArgumentParser()
        ap.add_argument('--HITL_PX4',action="store_true", default=False, dest='HITL_PX4')
        ap.add_argument('--HITL_DAA',action="store_true", default=False, dest='HITL_DAA')
        args = vars(ap.parse_args())

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
            cap = cv2.VideoCapture('http://192.168.1.148:5000/video_feed') # Stream remotely

        else:

            #cap = cv2.VideoCapture(0) # RaspPi default camera
            cap = cv2.VideoCapture('http://0.0.0.0:5000/video_feed') # Stream
            #cap = cv2.VideoCapture('dronedirecthit.avi')

        # Video meta
        self.half_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH )/2
        self.half_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT )/2
        self.fps =  cap.get(cv2.CAP_PROP_FPS)

        #print("Info: %dx%d %d FPS"%(self.half_width,self.half_height,self.fps))


        grabbed, frame = cap.read()
        if not grabbed:
            exit(0)
        #frame = imutils.resize(frame, width=500)
        lastframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

   
        # Loop over frames
        while True:


            # Grab next frame
            grabbed, frame = cap.read()
            if not grabbed:
                break
            #frame = imutils.resize(frame, width=500)
            currframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

  
            # Object Tracking - break if collision for simulator needs
            if self.object_tracking(currframe,frame):
                break
  

            # Object Detection
            self.object_detection(lastframe,currframe,frame)


            # Reiterate
            lastframe = currframe

            # Counter
            self.frames=self.frames+1
   
            # Thread kill
            if self.stop_event.is_set():
                break


        print("End >")
        cap.release()
        cv2.destroyAllWindows()



# Use offboard control to move the drone 5 to the right
# Great - but we will dangerously lose control of the drone due to global motion false positives
#
# 
'''
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
'''


def daa_tracking(stop_event):

    daa=DAA_Tracking(stop_event)
    daa.run()



stop_event=threading.Event()

def start():

    t = threading.Thread(target=daa_tracking, args=(stop_event,), daemon=True)
    #t = threading.Thread(target=test, args=(stop_event,), daemon=True)
    t.start()
    return t

def stop():
    stop_event.set()
    #pass



# Test
def test():
    t=start()
    #t.is_alive()
    time.sleep(30)
    stop()
    t.join()


if __name__ == '__main__':
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(daa_tracking(stop_event))



    #test()