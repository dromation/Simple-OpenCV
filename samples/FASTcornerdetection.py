import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

fast = cv.FastFeatureDetector_create()
cap = cv.VideoCapture(0)

while(cap.isOpened()):
      
    while True:
          
        ret, img = cap.read()
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)


# find and draw the keypoints
        kp = fast.detect(gray,None)
        img2 = cv.drawKeypoints(gray, kp, None, color=(255,0,0))
# Print all default params
        print( "Threshold: {}".format(fast.getThreshold()) )
        print( "nonmaxSuppression:{}".format(fast.getNonmaxSuppression()) )
        print( "neighborhood: {}".format(fast.getType()) )
        print( "Total Keypoints with nonmaxSuppression: {}".format(len(kp)) )
# Disable nonmaxSuppression
        fast.setNonmaxSuppression(0)
        kp = fast.detect(gray, None)
        print( "Total Keypoints without nonmaxSuppression: {}".format(len(kp)) )
        img3 = cv.drawKeypoints(gray, kp, None, color=(255,0,0))
        cv.imshow('img', img3)
        if cv.waitKey(30) & 0xff == ord('q'):
            break
              
    cap.release()
    cv.destroyAllWindows()
else:
    print("Alert ! Camera disconnected")
