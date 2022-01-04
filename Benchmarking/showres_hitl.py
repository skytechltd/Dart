#
# Copyright 2022 David Redpath - Sky Tech Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


#
# Read results file and calculate error, precision and recall
#
# Find any interesting trends in the results such as recurring failures
#
# Due to a set of inputs, this time from two raw log files
#
# Method:
#
# * Read DAA_HITL_REF.log from the sim looking for start tag, read the timestamps and distances
# * Search the DAA.log for detections, aircraft will either be detected or missed
#   
# 4/1/21 - No meaningful results could be obtained sadly as the lag reached 3 seconds on the Pi
#          meaning the detection nearly always occured after the test was logged as complete.
#          The main reason was the Pi wasn't fast enough for the algo and parameters we used.
#          A work around would be to account for the delay using a fixed offset but this isn't ideal


import sys
from datetime import datetime

if len(sys.argv)<=2:
    print("No filepaths entered")
    sys.exit()


reffile = open(sys.argv[1],"r")



class TestRun:
    def __init__(self,name,t1,t2):
        self.testname = name
        self.ts_start = t1
        self.ts_end = t2
        self.range = 0
        self.ts_det = None

    def setDet(self,t):
        self.ts_det = t

    def setRange(self,d):
        self.range = d
    

testruns=[]

# Find start and end timestamps
for l in reffile:
    
    if "StartTest:" in l:
        ts,p,tn = l.split(" ")
        print(tn+" Start: "+ts)

    if "EndTest" in l:
        te,p = l.split(" ")
        print("   End: "+te)
        testruns.append(TestRun(tn.rstrip(),datetime.strptime(ts.strip(),"%H:%M:%S,%f"),
                                            datetime.strptime(te.strip(),"%H:%M:%S,%f")))



# Check
#for l in testruns:
#    print(l.testname,l.ts_start,l.ts_end)


# Open DAA file and find if between start and end?
runfile = open(sys.argv[2],"r")

detections=[]

# Find detection and timestamps
for l in runfile:
   
    if "Collision detection" in l:
        ts = l.split(" ")[0]
        detections.append(datetime.strptime(ts.strip(),"%H:%M:%S,%f"))


# Check
#for l in detections:
 #   print(l)
 
TP=0
FN=0

for l in testruns:

    print(l)
    for dt in detections:
       
        if dt>l.ts_start and dt<=l.ts_end:
            #print("Matched "+dt.strftime('%H:%M:%S,%f')+" "+l.ts_start.strftime('%H:%M:%S,%f')+" and "+l.ts_end.strftime('%H:%M:%S,%f'))
            TP=TP+1 
            # Use timestamp to work out distance
            l.setDet(dt)
            break
        #else: # Don't need to log as FP not measured and TP+TN=1
            #print("Miss")
            #FN=FN+1


# Look between test run end, start timestamps to find false positives

# ***** There are too many from global motion as SITL start/stops DAA clean, 
#       HITL runs in the background logging loads of FP skewing results!



# Go back through ref file a last time and extract distances for detection, pop testruns as we go as it's cronological
reffile.seek(0)
i=0
for l in reffile:

    if i > len(testruns)-1:
        break

    if testruns[i].ts_det == None:
        i=i+1
        continue

    if not "StartTest:" in l and not "EndTest:" in l:
          
        t,r=l.split(" ")
        tf=datetime.strptime(t.strip(),"%H:%M:%S,%f")

        if testruns[i].ts_det <= tf:
            testruns[i].range = r.strip()
            print("Gotcha!"+t)
            i=i+1
        





# Write out detection distances to terminal for each test for reporting [90,90] 40 etc
for l in testruns:
    if l.ts_det == None:
        print(l.testname+" "+str(l.range))
    else:
        print(l.testname+" "+str(l.range)+" "+l.ts_det.strftime('%H:%M:%S,%f'))



reffile.close()
runfile.close()



r=len(testruns)

TP=TP/r
FN=1-TP#FN/r
FP=0#FP/r
P=TP/(TP+FP) if TP > 0 else 0
R=TP/(TP+FN)
ADD=0#np.average(rawres[:,1]) # Average det distance

#print("Accuracy: %.2f, FP: %.2f, ADD: %.2f, Precision: %.2f, Recall %.2f\n"%(TP,FP,ADD,P,R))

print("Accuracy: %.2f, MD: %.2f, FP: %.2f, AR: %.2f"%(TP,FN,FP,ADD))

# Any other relevent info?
