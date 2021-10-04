

#
# Read results file an calculate error, precision and recall
#
# Find any interesting trends in the results such as recurring failures
#
# Due to a set of inputs
#
#
#

RES_FILE='daares.csv'

import numpy as np
from numpy import genfromtxt
rawres = genfromtxt(RES_FILE, delimiter=' ')

#print(rawres)

r,c = rawres.shape

TP=np.count_nonzero(rawres[:,0] == 1)/r
FN=np.count_nonzero(rawres[:,0] == 0)/r
FP=np.count_nonzero(rawres[:,0] == -1)/r
P=TP/(TP+FP) if TP > 0 else 0
R=TP/(TP+FN)
print("Accuracy: %.2f, Precision: %.2f, Recall %.2f\n"%(TP,P,R))


# Any other info we can glean?

# ????



