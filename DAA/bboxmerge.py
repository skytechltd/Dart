import numpy as np

from itertools import product,combinations


# Taken from https://answers.opencv.org/question/194536/python-merge-overlapping-bounding-boxes-replace-by-surrounding-bounding-box/




''' Not working as expected!
def non_max_suppression_fast(boxes, overlapThresh):
   # if there are no boxes, return an empty list
   if len(boxes) == 0:
      return []

   # if the bounding boxes integers, convert them to floats --
   # this is important since we'll be doing a bunch of divisions
   if boxes.dtype.kind == "i":
      boxes = boxes.astype("float")
#  
   # initialize the list of picked indexes   
   pick = []

   # grab the coordinates of the bounding boxes
   x1 = boxes[:,0]
   y1 = boxes[:,1]
   x2 = boxes[:,2]
   y2 = boxes[:,3]

   # compute the area of the bounding boxes and sort the bounding
   # boxes by the bottom-right y-coordinate of the bounding box
   area = (x2 - x1 + 1) * (y2 - y1 + 1)
   idxs = np.argsort(y2)

   # keep looping while some indexes still remain in the indexes
   # list
   while len(idxs) > 0:
      # grab the last index in the indexes list and add the
      # index value to the list of picked indexes
      last = len(idxs) - 1
      i = idxs[last]
      pick.append(i)

      # find the largest (x, y) coordinates for the start of
      # the bounding box and the smallest (x, y) coordinates
      # for the end of the bounding box
      xx1 = np.maximum(x1[i], x1[idxs[:last]])
      yy1 = np.maximum(y1[i], y1[idxs[:last]])
      xx2 = np.minimum(x2[i], x2[idxs[:last]])
      yy2 = np.minimum(y2[i], y2[idxs[:last]])

      # compute the width and height of the bounding box
      w = np.maximum(0, xx2 - xx1 + 1)
      h = np.maximum(0, yy2 - yy1 + 1)

      # compute the ratio of overlap
      overlap = (w * h) / area[idxs[:last]]
      print("Overlap: ",overlap)

      # delete all indexes from the index list that have
      idxs = np.delete(idxs, np.concatenate(([last],
         np.where(overlap > overlapThresh)[0])))

   # return only the bounding boxes that were picked using the
   # integer data type
   return boxes[pick].astype("int")





close_dist = 0

# common version
def should_merge(box1, box2):
    for i in range(2):
        for j in range(2):
            for k in range(2):
                if abs(box1[j * 2 + i] - box2[k * 2 + i]) <= close_dist:
                    return True, [min(box1[0], box2[0]), min(box1[1], box2[1]), max(box1[2], box2[2]),
                                  max(box1[3], box2[3])]
    return False, None


# use product, more concise
def should_merge2(box1, box2):
    a = (box1[0], box1[1]), (box1[2], box1[3])
    b = (box2[0], box2[1]), (box2[2], box2[3])

    if any(abs(a_v - b_v) <= close_dist for i in range(2) for a_v, b_v in product(a[i], b[i])):
        return True, [min(*a[0], *b[0]), min(*a[1], *b[1]), max(*a[0], *b[0]), max(*a[1], *b[1])]

    return False, None

def merge_box(boxes):
    for i, box1 in enumerate(boxes):
        for j, box2 in enumerate(boxes[i + 1:]):
            is_merge, new_box = should_merge2(box1, box2)
            if is_merge:
                boxes[i] = None
                boxes[j] = new_box
                break

    return [b for b in boxes if b]
'''

# Product above may be faster but isn't working!
def IOU(b1,b2):

    offset = 40
    x1,y1,x2,y2=b1
    x3,y3,x4,y4=b2
    x_inter1 = max(x1,x3)
    y_inter1 = max(y1,y3)
    x_inter2 = min(x2,x4)
    y_inter2 = min(y2,y4)
    w=(x_inter2 - x_inter1)+offset
    h=(y_inter2 - y_inter1)+offset
    if w<=0 or h<=0:
        return False, None
    else:
        return True, [min(x1,x3),min(y1,y3),max(x2,x4),max(y2,y4)]

    #print("Area: ",(w*h))

    #print("Merge: (%d,%d) (%d,%d)"%(min(x1,x3),min(y1,y3),max(x2,x4),max(y2,y4)))



# Method
# A. Drop smaller boxes within larger ones
# Merge overlapping
# Merge close by
# Reiterate until no more are changed

class Break(Exception): pass
def merge_bboxes(bboxes):

    if len(bboxes) < 2:
        return bboxes

    # Covert to coordinates

    #print(bboxes)
    #if should_merge2([0,0,4,4],[5,5,10,10]):
    #    print("Should merge")

    #IOU([0,0,10,10],[5,5,10,10])


    while True:
        nc=len(bboxes)
        for b1,b2 in combinations(bboxes, r=2):
            is_merge, new_box = IOU(b1,b2)
            if is_merge:
                bboxes.remove(b1)
                bboxes.remove(b2)
                bboxes.append(new_box)
                break
        if nc == len(bboxes):
            break

    return bboxes



    # Take first box, does it overlap with anything else
        #if 
         #   print("Overlap")
    # If it does remove the two boxes

    # Add new combined box and repeat




    #return bboxes
        


