

import airsim
import json
from argparse import ArgumentParser
import math
import time

from runsim import *

DEFAULT_SETUPS='setups.json'


#
# Core script to call runsim
#
# Start and monitor:
# * UE4 Editor
# * AirSim
# * Streaming
#
#
#



# Main Setup
if __name__ == '__main__':
    ap = ArgumentParser()
    #ap.add_argument('-rec', '--record', default=False, action='store_true', help='Record?')
    



    # Read settings
    f = open(DEFAULT_SETUPS)
    setup = json.load(f)
    f.close()

    # Check everything is running - and still running (thread)

    # ?????

    # Check UE4 is running and responding, thread?


    # Start streaming for DAA input, thread?


    
    #print(json.dumps(setup, indent=4, sort_keys=True))

    #print(setup["settings"]["setting1"])
    #   "dron_spos": [-10,0,-20],
    #    "dron_epos": [-10,0,-20],
    #    "dron_velc": 0, 
    #    "pawn_epos": [-10,0,-20],
    #    "pawn_velc": 10,

     #   "coll_dist": 5,

    # Calc start positions
    r=setup['scenarios']['pawn_sdist']
    pawn_spos=[]

    x,y,z = setup['scenarios']['pawn_epos']

    for azm,zen in setup['scenarios']['pawn_apr_ang']:

        # We are using the ISO 3D spherical coordinate system
        # https://en.wikipedia.org/wiki/Spherical_coordinate_system
        #
        # looking ahead will be (90,90)
        # to the right (0,90)
        # Straight up (0,0)
        # For PX4 we need to do an axis rotation swap x,y, invert z
        # x,y swapped below to convert to PX4 coord system!
        yy = r * math.cos(math.radians(azm)) * math.sin(math.radians(zen))
        xx = r * math.sin(math.radians(azm)) * math.sin(math.radians(zen))
        zz = -r * math.cos(math.radians(zen))

        # print("Start position %d,%d (%.2f,%.2f,%.2f)"%(azm,zen,xx,yy,zz))

        pawn_spos.append(Pos(round(x+xx,2),round(y+yy,2),round(z+zz,2)))


    #print(pawn_spos)

    #pawn_spos = [Pos(20,0,-20)]

    i=1
    for spos in pawn_spos:
        print("Running simulation %d of %d..."%(i,len(pawn_spos)))
        collision = Collision(50,5)
        collision.setDrone(WayPoint(Pos(-10,0, -20), Pos(-10, 0, -20),10))
        collision.setPawn( WayPoint(spos, Pos(-10, 0, -20),10))
        start(collision)
        i+=1











