import airsim
import sys
import threading
import logging
import time
import pprint
import math
import json
import copy
from scipy.spatial import distance
from enum import Enum, unique


sys.path.insert(0, '../DAA')
import daa_opticalflow as daa


DEFAULT_SETUPS='setups.json'
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
#   * Pawn to seek drone, not just assume its at waypoint - important for smaller pawns
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


#class WayPoint:
    #def __init__(self,s,e,v):
        #self.start=aims)
       # self.end=Pos(e)
        #self.v=v
        #self.pos3darray=[x,y,z]

class AirVehicle:
    ACC_DELAY = 2 # Small delay until vehicle gets up to speed then assume t=d*s
    def __init__(self,n,s,distance=0):
        self.name = n
        # UE4 global position
        self.origin = airsim.Vector3r(s['X'],s['Y'],s['Z'])
        # Offsets from origin
        self.offset = airsim.Vector3r(s['X'],s['Y'],s['Z'])
        self.timeout = 3e+38 # Default, timeout to prevent vehicles getting stuck on terrain
        self.distance = distance
        self.approach = [0,0]

    def setTrajectory(self,a,b,v,yaw=0):
        self.start = airsim.Vector3r(a[0],a[1],a[2]) - self.offset
        self.end =   airsim.Vector3r(b[0],b[1],b[2]) - self.offset
        self.v = v
        self.yaw = -(yaw-90)
        if self.distance>0:
            self.timeout = (self.distance*v) + AirVehicle.ACC_DELAY


# Check for a collision event and hold value
class Collision:
    def __init__(self,s):
        #self.pawnName = pn
        #self.approach = a
        self.setup=s
        self.detection_range = s['pawn_sdist']
        self.detection_hit = s['coll_dist']
        self.distance = math.inf
        self.hascollided = False
        self.inrange = False


    def update(self,d,p):

        if self.hascollided:
            return False

        self.distance = distance.euclidean(d,p)

        self.hascollided = True if self.distance < self.detection_hit else False

        if not self.inrange:
            self.inrange = True if self.distance < self.detection_range else False
   


    # Collide the drone and pawn
    def start(self,cl,drone,pawn):

       
        cl.enableApiControl(True, "Drone")
        cl.enableApiControl(True, pawn.name)
 
        # Arm, takeoff and move to position, would be better to teleport but they just fall to the ground
        cl.armDisarm(True, "Drone") 
        cl.armDisarm(True, pawn.name)

        # Take off
        dt = cl.takeoffAsync(vehicle_name="Drone")
        pt = cl.takeoffAsync(vehicle_name=pawn.name)
        dt.join()
        pt.join()


        # Shift to start positions
        #print("Drone SPos(%.1f,%.1f,%.1f), V:%d"%(drone.start.x_val, drone.start.y_val, drone.start.z_val,drone.v))
        #print("Pawn  SPos(%.1f,%.1f,%.1f), V:%d, Y:%d"%(pawn.start.x_val, pawn.start.y_val, pawn.start.z_val,pawn.v,pawn.yaw))
        dt = cl.moveToPositionAsync(drone.start.x_val, drone.start.y_val, drone.start.z_val, drone.v, \
                                            vehicle_name="Drone", timeout_sec=drone.timeout)
        pt = cl.moveToPositionAsync(pawn.start.x_val, pawn.start.y_val, pawn.start.z_val, pawn.v,  \
                                            vehicle_name=pawn.name, timeout_sec=pawn.timeout)
        dt.join()
        pt.join()

        # Let drone settle as global motion from terrain is throwing false positive with optical flow first round
        print("Sleeping")
        #time.sleep(10)
        # Debug
        #airsim.wait_key('Press any key to collide')



        # Two approaches, we either:
        # A. Move the pawn to collide with the drone (same position and check) for collision, 
        #    assuming another script is responsible for a DAA manoeuvre, but airsim doesn't like
        #    two threads accessing the client api and UE4 crashes. Or
        # B. Move the pawn to nearly collide with the drone, run DAA on a thread and listen for a collision warning
        #    we can record this along with t print("Running simulation for %s %d of %d..."%(pawn.name,i,len(self.collision)))
                #Collision(sel
        #    collision = client.simGetCollisionInfo(vehicle_name="Drone2")
        #    if collision.has_collided:
        #        printunrealengine NewMap is generated
  

        # DAA run, break if detected, deem as fair detection or false alarm
        daa_thr=daa.start()
        # Try catch here ???????
        print("DAA started...")

        # Set pawn pose approach pitch and yaw,0
        # client.simSetObjectPose("Pawn",pose,teleport=True)
        #pt = client.moveToPositionAsync(20, 2, -10, 5, vehicle_name="Pawn",yaw_mode={'is_rate':False,'yaw_or_rate':45})

        # Instead of using moveToPosition is may be better to update target position to deal with drift of drone
        
        # Drone doesn't move yet?
        #dt = cl.moveToPositionAsync(drone.start.x_val, drone.start.y_val, drone.start.z_val, drone.v, vehicle_name="Drone")    
        pt = cl.moveToPositionAsync(pawn.end.x_val, pawn.end.y_val, pawn.end.z_val, pawn.v, vehicle_name=pawn.name, \
                                  timeout_sec=pawn.timeout, yaw_mode={'is_rate':False,'yaw_or_rate':pawn.yaw})
        #pt.join()



        # TODO - add enum to collision class!!!
        detection=Detection.MISSED
        while True:
            dronepos = cl.getMultirotorState(vehicle_name="Drone").kinematics_estimated.position
            pawnpos = cl.getMultirotorState(vehicle_name=pawn.name).kinematics_estimated.position
            #print("Pos: ",dronepos.x_val)
            # Has Pawn reached collision position within radius?
            # WARNING! : Take care as two meshes can be touching but their centers still far appart!
       
            # Better inside the class as it uses distance?
            #can call update(x,y,z) then do collision.distanceto, hascollided=false
            self.update([dronepos.x_val,dronepos.y_val,dronepos.z_val],[pawnpos.x_val,pawnpos.y_val,pawnpos.z_val])

            # Missed detection,det=MISSED set above 
            if self.hascollided:                
                print("Pawn ended, killing DAA") 
                # Stop DAA thread gracefully
                daa.stop()
                break

            # Has DAA thread exited?
            if not daa_thr.is_alive():
                # Stop pawn and reset, break and reset below
                if self.inrange:
                    print("DAA ended, killing pawn- - in range")
                else:
                    print("DAA ended, killing pawn - out")
            
                print("Dist: ",self.distance)
                detection = Detection.TRUE if self.inrange else Detection.FALSE
                break

            # Debug only as the delay skews the daa result
            #time.sleep(1)



        # Record result, det: 1, miss 0, fa 
        # Todo: Python 3.10> has match-case to make this more C like
        if Detection.MISSED == detection:
            print("Missed Detection")
        elif Detection.TRUE == detection:
            print("True Detection")
        else: #Detection.FALSE == detection:
           print("False Detection")

        with open(RES_FILE,'a') as f:
            f.write("%d %.2f {apr_ang=[%d,%d]}\n"%(detection.value, self.distance, pawn.approach[0], pawn.approach[1]))
            #f.write("(%.1f,%.1f,%.1f) %d %.2f\n"%(pawn.end.x, pawn.end.y, pawn.end.z, detection.value, collision.distance))

   
        # Tidy up
        cl.armDisarm(False, "Drone")
        cl.armDisarm(False, pawn.name)
        cl.enableApiControl(False, "Drone")
        cl.enableApiControl(False, pawn.name)
        cl.reset()

        return 






# The collisions class holds the setup details and will step through different vehicle collisions
class Collisions:

    def __init__(self):

        try:
            self.client = airsim.MultirotorClient()
            self.client.confirmConnection()
        except Exception:
            print("Could not connect to AirSim, is it running?")
            raise Exception

        # Load vehicle names and offsets from aimsim config file
        # Create a inital dict of AirVehicle()
        settings = json.loads(self.client.getSettingsString())
        self.vehicle_settings={}
        for k,v in settings['Vehicles'].items():
            self.vehicle_settings[k] = v

        # Load our simulation setup (not the airsim ones)
        f = open(DEFAULT_SETUPS)
        self.setup = json.load(f)['scenarios'] # Just scenario 1 for now
        f.close()

        # Good practice to deep copy settings as we delete it below!
        self.drone = AirVehicle('Drone',copy.deepcopy(self.vehicle_settings['Drone'])) #,self.setup)

        # Set drone trajectory from setup file
        self.drone.setTrajectory(self.setup['dron_spos'],self.setup['dron_epos'],self.setup['dron_velc'])

        # Set drone and drop 'Drone' from the dict as we can't avoid ourselves looping through in start()
        del self.vehicle_settings['Drone']
    

        # Create a list of pawn vehicles with start and end points
        self.collisions=[]

        # TODO - Support for scenarios has not been included yet, do so here in the future
        for name,settings in self.vehicle_settings.items():

            for ang in self.setup['pawn_apr_ang']:
                #print(self.setup['pawn_sdist'])
                v=AirVehicle(name,settings,distance=self.setup['pawn_sdist'])
                v.setTrajectory(self.get_appr_spos(ang,self.setup['pawn_sdist'],self.setup['pawn_epos']), \
                            self.setup['pawn_epos'],self.setup['pawn_velc'],yaw=ang[0])
                self.collisions.append(v)
            break # DEBUG - REMOVE


    # Seems best to have this here rather than overcomplicate AirVehicle
    def get_appr_spos(self,a,r,e):
      
        # We are using the ISO 3D spherical coordinate system
        # https://en.wikipedia.org/wiki/Spherical_coordinate_system
        #
        # looking ahead will be (90,90)
        # to the right (0,90)
        # Straight up (0,0)
        # For PX4 we need to do an axis rotation swap x,y, invert z
        # x,y swapped below to convert to PX4 coord system!
        # Offsets WRT to (0,0,0)
        azm,zen = a
        yy =  r * math.cos(math.radians(azm)) * math.sin(math.radians(zen))
        xx =  r * math.sin(math.radians(azm)) * math.sin(math.radians(zen))
        zz = -r * math.cos(math.radians(zen))
        # Shift WRT to global
        x,y,z = e

        return [round(x+xx,2),round(y+yy,2),round(z+zz,2)]


    def start(self):

            i=1
            for pawn in self.collisions:
                print("Running simulation for %s %d of %d..."%(pawn.name,i,len(self.collisions)))
                c=Collision(self.setup)
                c.start(self.client,self.drone,pawn)
                i+=1
                break
        
    # Collision range 50 > x > 5
    #collision = Collision([90,90],setup['scenarios'])
    #start(collision)
    # put start in class then collis.start()

        # Collide to air vehicles
        #Collision()
        #i=1
        #for spos in pawn_spos:
        #for apr_ang in setup['scenarios']['pawn_apr_ang']:
        #    print("Running simulation %d of %d..."%(i,len(setup['scenarios']['pawn_apr_ang'])))
        #    start(Collision(apr_ang,setup['scenarios']))
        #    i+=1

     






# Main Setup
if __name__ == '__main__':
    
    c=Collisions()
    c.start()
    
  



