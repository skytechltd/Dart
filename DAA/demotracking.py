#!/home/david/anaconda3/bin/python


import cv2 
import numpy as np
import matplotlib.pyplot as plt
import argparse
import time
import imutils
import queue

(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

print(major_ver,".",minor_ver)


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
        def __init__(self,frame,roi):

            self.roi = roi
            self.tracker = cv2.legacy.TrackerMedianFlow_create()
            self.ok = self.tracker.init(frame, self.roi)
            self.area = self.roi[2]*self.roi[3]
            self.history = HQueue(25)

        def update(self,frame):
            # Update tracker
            self.ok, self.roi = self.tracker.update(frame)


            #input("Press return to terminate the program")

            
            # Draw bounding box
            if self.ok:
                # Tracking success
                p1 = (int(self.roi[0]), int(self.roi[1]))
                p2 = (int(self.roi[0] + self.roi[2]), int(self.roi[1] + self.roi[3]))
                cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)
            else:
                # Tracking failure
                cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
                return False

            #print("BB: ",self.roi)
            #print("Ave: ",self.history.ave())
            # If area is above threshold object approaching!
            area = self.roi[2]*self.roi[3]
            self.history.put(self.area-area)
            if area > self.area*1.2:
                print("Change: ",area/self.area)
                cv2.putText(frame, "Collision risk!", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)

                self.area = area

            # If history is moving away then remove
            if self.history.ave() < 0:
                print("Remove")
                input("Press return to terminate the program")
                return True



    def __init__(self):

        self.UFOS = []



    def find_moving_objects(self,lastframe,gray):


        frameDelta = cv2.absdiff(lastframe, gray)
        #frameDelta = cv2.GaussianBlur(frameDelta, (21, 21), 0)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

	    # dilate the thresholded image to fill in holes, then find contours
	    # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        rects=[]
	    # loop over the contours and assign rects
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < self.args["min_area"]:
                continue
		    # compute the bounding box for the contour, draw it on the frame,
		    # and update the text
            (x, y, w, h) = cv2.boundingRect(c)

            self.UFOS.append(self.UFO(gray,cv2.boundingRect(c)))


            #cv2.rectangle(gray, (x, y), (x + w, y + h), (0, 255, 0), 2)
            #cv.putText(frame)

            # Find last similar ROI?


            # Reject if inside or union of existing roi

            return [(x, y, w, h)]

            

        return []


        # Merge overlapping ROI
        #rects,weights = cv.groupRectangles(rects, 1, 1.5)
        #for r in rects:
        #    cv.rectangle(frame,(r[0],r[1]),(r[0]+r[2],r[1]+r[3]),(0,0,255),2)




    def run(self):


        ap = argparse.ArgumentParser()
        # construct the argument parser and parse the arguments
        ap.add_argument("-v", "--video", help="path to the video file")
        ap.add_argument("-a", "--min-area", type=int, default=50, help="minimum area size")
        self.args = vars(ap.parse_args())



        #cap = cv.VideoCapture(0) # Camera Pi
        #cap = cv.VideoCapture('http://0.0.0.0:5000/video_feed') # Stream
        cap = cv2.VideoCapture('dronedirecthit.avi')
        #cap = cv2.VideoCapture('office2.avi')


        cwidth = cap.get(cv2.CAP_PROP_FRAME_WIDTH )/2
        cheight = cap.get(cv2.CAP_PROP_FRAME_HEIGHT )/2
        fps =  cap.get(cv2.CAP_PROP_FPS)


        grabbed, frame = cap.read()
        if not grabbed:
            exit(0)
        #frame = imutils.resize(frame, width=500)
        lastframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

   
        flag=False
        frames=0
        # Loop over frames
        while True:


            # Pause/Unpause if space is pressed
            key = cv2.waitKey(1) & 0xFF
            #if cv.waitKey(1) & 0xFF == ord(' '):
                #flag = not(flag)
            if key == ord("q"):
                break
            # Capture frame-by-frame
            #if flag != True:
              #  continue


            grabbed, frame = cap.read()
            if not grabbed:
                break
            #frame = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

  

            #if flag:
            #    self.UFOS.append(self.UFO(frame,(0,0,100,100)))
            #    flag=False

            # Update tracking
            if len(self.UFOS) > 0:
                print("Run tracking: ",len(self.UFOS))
                if not self.UFOS[0].update(frame):
                    del self.UFOS[0]


            # Run every x seconds
            if frames > 25 and len(self.UFOS)==0:
                r=self.find_moving_objects(lastframe,gray)
                if r:
                    r=r[0] # test with first item
                    p1 = (int(r[0]), int(r[1]))
                    p2 = (int(r[0] + r[2]), int(r[1] + r[3]))
                    cv2.rectangle(frame, p1, p2, (0,255,0), 2, 1)
                    frames=0
                    cv2.imshow('tracking', frame)
                    flag=True
                    #print("Stop",r)
                    #input("Press return to terminate the program")
            

            # Show
            cv2.imshow('tracking', frame)
            time.sleep(0.05)
            if flag:
                flag=False
                #input("Press return to terminate the program")


            # Reiterate
            lastframe = gray
            #time.sleep(0.05)
            frames=frames+1
   


        cap.release()
        cv2.destroyAllWindows()







if __name__ == '__main__':
    daa = DAA_Tracking()
    daa.run()

