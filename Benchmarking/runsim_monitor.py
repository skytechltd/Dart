


from airSimStream import start_stream,stop_stream
from argparse import ArgumentParser
#import time
import sys






#flask ngrok
# Core script to call runsim
#
# Start and monitor:
# * UE4 Editor
# * AirSim
# * Streaming
#
#
#
# TODO
#
# * Add options --NOTBELOW to so big objects arent considered from below as they get stuck in terrain when low
#
# * Add pitch and yaw (roll) to pawn based on atatch angle
#





class AirSimStreamException(Exception):
    pass

class RunSimsException(Exception):
    pass





def runSims():

    # Read settings
    #f = open(DEFAULT_SETUPS)
    #setup = json.load(f)
    #f.close()

    # Exception handling ?


# Main Setup
if __name__ == '__main__':

    ap = ArgumentParser()
    #ap.add_argument('-rec', '--record', default=False, action='store_true', help='Record?')
    

    try:


        # Check everything is running - and still running (thread)

        # Check UE4 is running and responding
        # Start streaming for DAA input
        try:
            #start_stream()
            pass
        except Exception as err:
            raise AirSimStreamException('Connection to AirSim Failed. Please start UE4 Editor Simulator')


        #try:
        runSims()
        #except Exception as err:
        #    raise RunSimsException('RunSims Exception ',err)

    except (AirSimStreamException,RunSimsException) as err:

        print ("Error: ",err)
    

    # Clean up
    finally:
        stop_stream()





