#!/home/david/anaconda3/bin/python


import cv2 
import numpy as np
import matplotlib.pyplot as plt
import argparse
import time
import imutils
import queue
import copy
from bboxmerge import merge_bboxes, IOU

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

            self.bbox = bbox
            self.tracker = cv2.legacy.TrackerMedianFlow_create()
            self.area = self.bbox[2]*self.bbox[3]
            self.history = HQueue(25)
            self.ok = True


    def __init__(self):

        self.UFOS=[]
        self.UFO_Count=0
        self.frames=0


    def addUFO(self,frame,bbox):

        ufo = self.UFO(bbox)
        ufo.ok = ufo.tracker.init(frame,bbox)
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
        if y+(h/2) < self.cheight:
            text="Move down"
        # Move Up
        elif y+(h/2) > self.cheight:
            text="Move up"
        # Move Up
        elif x+(w/2) < self.cwidth:
            text="Move right"
        # Move Up
        elif x+(w/2) > self.cwidth:
            text="Move left"

        print(text)

        cv2.putText(frame, "Detection {}".format(text), (10, 20),
		                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

   

    # Update all the trackers
    def object_tracking(self,currframe,frame):


        print("Tracking %d objects"%(len(self.UFOS)))

        for i,ufo in enumerate(self.UFOS):


            # Update tracker
            ok, bbox = ufo.tracker.update(currframe)


            # Draw bounding box for debug
            if ok:
                # Tracking success, draw box
                print("Tracking bbox (%d,%d,%d,%d)"%(bbox[0],bbox[1],bbox[2],bbox[3]))
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[2]), int(bbox[3]))
                cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)

                #input("Press return to terminate the program")


               
                # If area is above threshold object approaching!
                area = (bbox[2]-bbox[0])*(bbox[3]-bbox[1])
                #self.UFOS[i].history.put(ufo.area-area)
                #print("Ave: ",self.history.ave())
                print("Area:",int(area))
                if area > self.UFOS[i].area*1.1:
                    print("Change: ",area/self.UFOS[i].area)

                    cv2.rectangle(frame, p1, p2, (0,0,255), 2, 1)
                    cv2.putText(frame, "Collision risk!", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)

                    self.avoid_action(bbox,frame)
                else:
                    cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)


                self.UFOS[i].area = area




            else:
                # Tracking failure
                #cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
                print("Tracking failed for ID, deleting")
                #self.delUFO(ufo)
                self.UFOS[i]=None
            



        # Remove deleted marked None
        self.UFOS = [i for i in self.UFOS if i is not None]


            # If history is moving away then remove
           # if ufo.history.ave() < 0:
            #    print("Moving away - Remove tracking")
        #    input("Press return to terminate the program")
        #    return True




    def object_detection(self,lastframe,currframe,frame):


        # Run every x seconds   
        #if self.frames < 25*5:
        #    return  
        selfframes=0  

        framec=copy.copy(frame)

        frameDelta = cv2.absdiff(lastframe, currframe)
        #frameDelta = cv2.GaussianBlur(frameDelta, (21, 21), 0)
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
            if cv2.contourArea(c) < 50: #self.args["min_area"]:
                continue
		    # compute the bounding box for the contour, draw it on the frame,
		    # and update the text
            (x, y, w, h) = cv2.boundingRect(c)

            rects.append([x,y,x+w,y+h])
            
            #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)


        #cv2.imshow('tracking', frame)

        #return

        # Merge overlapping ROI from detection
        rects = merge_bboxes(rects)


        # Reject if overlapping existing roi's, don't do any more merging!
        for r in rects[:]:
            for ufo in self.UFOS:
                if IOU(ufo.bbox,r):
                    rects.remove(r)


                    


        # Ok its new so add
        for r in rects:
            #print(r)
            self.addUFO(currframe,r)
            (x1, y1, x2, y2) = r
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            #cv2.rectangle(framec, (0, 0), (200, 200), (255, 0, 0), 2)
           

        #cv2.imshow('tracking2', frame)


        #cv2.waitKey(100)
        #input("Press return to terminate the program")

    def run(self):


        ap = argparse.ArgumentParser()

        #cap = cv.VideoCapture(0) # Camera Pi
        #cap = cv.VideoCapture('http://0.0.0.0:5000/video_feed') # Stream
        cap = cv2.VideoCapture('dronedirecthit.avi')
        #cap = cv2.VideoCapture('office2.avi')
        cap = cv2.VideoCapture('colideandshake4.avi')

        # Video meta
        self.cwidth = cap.get(cv2.CAP_PROP_FRAME_WIDTH )/2
        self.cheight = cap.get(cv2.CAP_PROP_FRAME_HEIGHT )/2
        self.fps =  cap.get(cv2.CAP_PROP_FPS)

        #print("Info: %dx%d %d FPS"%(self.cwidth,self.cheight,self.fps))


        grabbed, frame = cap.read()
        if not grabbed:
            exit(0)
        #frame = imutils.resize(frame, width=500)
        lastframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

   
        flag=False
       
        # Loop over frames
        while True:

            # Pause/Unpause if space is pressed
            key = cv2.waitKey(1) & 0xFF
            #if cv.waitKey(1) & 0xFF == ord(' '):
                #flag = not(flag)
            if key == ord("q"):
                break


            # Grab next frame
            grabbed, frame = cap.read()
            if not grabbed:
                break
            #frame = imutils.resize(frame, width=500)
            currframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

  
            # Object Tracking
            self.object_tracking(currframe,frame)
            #print("Tracking %d objects"%(len(self.UFOS)))

            # Object Detection
            self.object_detection(lastframe,currframe,frame)


            # Show Frame
            cv2.imshow('tracking', frame)
            time.sleep(0.1)
            if flag:
                flag=False
                #input("Press return to terminate the program")


            # Reiterate
            lastframe = currframe

            # Counter
            self.frames=self.frames+1
   


        cap.release()
        cv2.destroyAllWindows()



def unittest_boxmerge():

    # BBox as x,y,w,h
    #rects=[[50,50,200,200],[100,100,200,200],[70,70,50,50]]

    #rects=[[20,20,40,40],[1,1,25,25],[0,0,3,3],[39,39,50,50]]

    rects=[[0,0,100,100],[10,10,50,50]]

    img = cv2.imread('testgrid.png')
    img2 = cv2.imread('testgrid.png')

    for r in rects:
        (x,y,w,h) = r
        cv2.rectangle(img, (x, y), (w, h), (255, 0, 0), 2)

    cv2.imshow('test', img)
    #rects = non_max_suppression_fast(np.array(rects),0.1)
    #rects = merge_box(rects)
    
   
    rects = merge_bboxes(rects)

    for r in rects:
        (x,y,w,h) = r
        cv2.rectangle(img2, (x, y), (w, h), (0, 0, 255), 2)



    cv2.imshow('test1', img2)

    # waitKey() waits for a key press to close the window and 0 specifies indefinite loop
    cv2.waitKey(0)



if __name__ == '__main__':

    daa=DAA_Tracking()
    daa.run()

    #unittest_boxmerge()




