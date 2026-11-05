import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt


fast = cv.FastFeatureDetector_create()

orb = cv.ORB_create(nfeatures=2000)
cap = cv.VideoCapture(0)
while(cap.isOpened()):
      
    while True:
        ret, img = cap.read()
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
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
        op = orb.detect(gray, None)
        kp, des = orb.compute(gray, op)
        img4 = cv.drawKeypoints(gray, op, None, color=(0,255,0), flags=0)
        res = img2 + img3 + img4

        cv.imshow('Detector', res)
    

        if cv.waitKey(30) & 0xff == ord('q'):
            break
              
    cap.release()
    cv.destroyAllWindows()
else:
    print("Alert ! Camera disconnected")