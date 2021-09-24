import airsim
import sys
import threading
import logging
import time
import pprint
import math
from scipy.spatial import distance
from enum import Enum, unique


sys.path.insert(0, '../DAA')
import daa_opticalflow as daa


RES_FILE='daares.csv'

#
# Core script for running collisions
#
# Run collision scenario and evaluate performance
# 
# Options: 
#   -SITL_ALL (Default) 
#   -HITL_PX4 Use PX4 hardware
#   -HITL_DAA Use DAA hardware
#   -HITL_ALL
#
#
# TODO:
#   * Logging
#
#   * Support scenarios, 0 a flight - reject FP, 1 single collision, 2 multiple
#
#   * PAwn to seek drone, not just assume its at waypoint - important for smaller pawns
#
#
#
#
# Future Features:
#
# * Support threadpool of instances across multiple networked sim hardware
#
# * Log each DAA result, screenshot and any output metrics
#
#

class Detection(Enum):
    MISSED = 0
    TRUE = 1
    FALSE = -1

class Pos:
    def __init__(self,x,y,z):
        self.x=x
        self.y=y
        self.z=z   

class WayPoint:
    def __init__(self,s,e,v):
        self.start=s
        self.end=e
        self.v=v
        #self.pos3darray=[x,y,z]


# Check for a collision event and hold value
class Collision:
    def __init__(self,r,e):
        self.detection_range = r
        self.detection_hit = e
        self.distance = math.inf
        self.hascollided = False
        self.inrange = False

    def setDrone(self,d):
        self.drone = d

    def setPawn(self,p):
        self.pawn = p


    def update(self,d,p):

        if self.hascollided:
            return False

        self.distance = distance.euclidean(d,p)

        self.hascollided = True if self.distance < self.detection_hit else False

        if not self.inrange:
            self.inrange = True if self.distance < self.detection_range else False
            #print("Comapre: ",self.distance," to ",self.detection_range)
   


    # Other distance metrics are available https://docs.scipy.org/doc/scipy/reference/spatial.html
    #def collision(self,d,p,r):
    #    print ("Distance: %f.1" % (distance.euclidean(p,self.start.pos3darray)))
    #    if distance.euclidean(d,p) < r:
     #       return True
     #   else:
     #       return False



def start(collision):

    #drone,pawn=args

    #collision=Collision(20,5)

    try:
       client = airsim.MultirotorClient()
       client.confirmConnection()
    except Exception:
        print("Could not connect to AirSim, is it running?")
        return

    #if len(client.simListSceneObjects('Pawn'))==0:
    #    if not client.simAddVehicle("Pawn","simpleflight",airsim.Pose(),"SmallBalloon"):
    #        print('Error crearting Pawn')   
    #client.simDestroyObject("Pawn") # leasds to segfault

    drone=collision.drone
    pawn=collision.pawn

    client.enableApiControl(True, "Drone")
    client.enableApiControl(True, "Pawn")

    # Arm, takeoff and move to position, would be better to teleport but they just fall to the ground
    client.armDisarm(True, "Drone") 
    client.armDisarm(True, "Pawn")

    # Take off
    dt = client.takeoffAsync(vehicle_name="Drone")
    pt = client.takeoffAsync(vehicle_name="Pawn")
    dt.join()
    pt.join()

    # Shift to start positions
    dt = client.moveToPositionAsync(drone.start.x, drone.start.y, drone.start.z, drone.v, vehicle_name="Drone")
    pt = client.moveToPositionAsync(pawn.start.x, pawn.start.y, pawn.start.z, pawn.v, vehicle_name="Pawn")
    dt.join()
    pt.join()

    # Let drone settle as global motion from terrain is throwing false positive with optical flow first round
    print("Sleeping")
    time.sleep(10)
    # Debug
    #airsim.wait_key('Press any key to collide')



    # Two approaches, we either:
    # A. Move the pawn to collide with the drone (same position and check) for collision, 
    #    assuming another script is responsible for a DAA manoeuvre, but airsim doesn't like
    #    two threads accessing the client api and UE4 crashes. Or
    # B. Move the pawn to nearly collide with the drone, run DAA on a thread and listen for a collision warning
    #    we can record this along with the distance and mark as a fair true detection, false alarm or missed 


    # For HITL DAA use simGetCollision
    # Confirm collision? Old way - not alway reliable
    #try:
    #    collision = client.simGetCollisionInfo(vehicle_name="Drone2")
    #    if collision.has_collided:
    #        printunrealengine NewMap is generated
  

    # DAA run, break if detected, deem as fair detection or false alarm
    dt=daa.start()
    # Try catch here ???????
    print("DAA started...")


    # Instead of using moveToPosition is may be better to update target position to deal with drift of drone
    pt = client.moveToPositionAsync(pawn.end.x, pawn.end.y, pawn.end.z, pawn.v, vehicle_name="Pawn")
   
    # TODO - add enum to collision class!!!
    detection=Detection.MISSED
    while True:
        dronepos = client.getMultirotorState(vehicle_name="Drone").kinematics_estimated.position
        pawnpos = client.getMultirotorState(vehicle_name="Pawn").kinematics_estimated.position
        #print("Pos: ",dronepos.x_val)
        # Has Pawn reached collision position within radius?
        # WARNING! : Take care as two meshes can be touching but their centers still far appart!
       
        # Better inside the class as it uses ditance
        #can call update(x,y,z) then do collision.distanceto, hascollided=false
        
        collision.update([dronepos.x_val,dronepos.y_val,dronepos.z_val],[pawnpos.x_val,pawnpos.y_val,pawnpos.z_val])

        if collision.hascollided:  
            # Missed detection,det=MISSED set above 
            print("Pawn ended, killing DAA") 
            # Stop DAA thread gracefully
            daa.stop()
            break
        # Has DAA thread exited?
        if not dt.is_alive():
            # Stop pawn and reset, break and reset below
            if collision.inrange:
                print("DAA ended, killing pawn- - in range")
            else:
                print("DAA ended, killing pawn - out")
            
            print("Dist: ",collision.distance)
            detection = Detection.TRUE if collision.inrange else Detection.FALSE
            break

        # Debug only as the delay skews the daa result
        #time.sleep(1)



    # Record result, det: 1, miss 0, fa    def pos3d_array():
    #    return [self.x,self.y,self.z]lse alarm -1

    # Todo: Python 3.10> has match-case to make this more C like
    if Detection.MISSED == detection:
        print("Missed Detection")
    elif Detection.TRUE == detection:
        print("True Detection")
    else: #Detection.FALSE == detection:
        print("False Detection")


    drone=collision.drone
    pawn=collision.pawn

    #print("disarming and resetting...")

    client.armDisarm(False, "Drone")
    client.armDisarm(False, "Pawn")
    client.reset()

    # that's enough fun for now. let's quit cleanly
    client.enableApiControl(False, "Drone")
    client.enableApiControl(False, "Pawn")


    return 


# Main Setup
if __name__ == '__main__':
    
    # Collision range 50 > x > 5
    collision = Collision(50,5)
    collision.setDrone(WayPoint(Pos(-10,0, -20), Pos(-10, 0, -20),10))
    collision.setPawn( WayPoint(Pos(50, 0, -20), Pos(-10, 0, -20),10))
    start(collision)

