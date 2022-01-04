
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
# Read results file an calculate error, precision and recall
#
# Find any interesting trends in the results such as recurring failures
#
# Due to a set of inputs
#



import sys
import numpy as np
from numpy import genfromtxt


if len(sys.argv)<=1:
    print("No filepath entered")
    sys.exit()

rawres = genfromtxt(sys.argv[1], delimiter=' ')

#print(rawres)

r,c = rawres.shape

TP=np.count_nonzero(rawres[:,0] == 1)/r
FN=np.count_nonzero(rawres[:,0] == 0)/r
FP=np.count_nonzero(rawres[:,0] == -1)/r
P=TP/(TP+FP) if TP > 0 else 0
R=TP/(TP+FN)
ADD=np.average(rawres[:,1]) # Average det distance

#print("Accuracy: %.2f, FP: %.2f, ADD: %.2f, Precision: %.2f, Recall %.2f\n"%(TP,FP,ADD,P,R))

print("Accuracy: %.2f, MD: %.2f, FP: %.2f, AR: %.2f"%(TP,FN,FP,ADD))

# Any other info we can glean?

# ????



