import numpy as np
import cv2 as cv

#### NOT INCLUDED IN OPENCV FRAMEWORKS ANYMORE!!!!!!
star = cv.xfeatures2d.StarDetector_create()
brief = cv.xfeatures2d.BriefDescriptorExtractor_create()

cap = cv.VideoCapture(0)


while(cap.isOpened()):
      
    while True:
          
        ret, img = cap.read()
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)


        # find the keypoints with STAR
        kp = star.detect(gray,None)
        # compute the descriptors with BRIEF
        kp, des = brief.compute(gray, kp)
        print( brief.descriptorSize() )
        print( des.shape )

        img3 = cv.drawKeypoints(gray, kp, None, color=(255,0,0))
        cv.imshow('img', img3)
        if cv.waitKey(30) & 0xff == ord('q'):
            break
              
    cap.release()
    cv.destroyAllWindows()
else:
    print("Alert ! Camera disconnected")
