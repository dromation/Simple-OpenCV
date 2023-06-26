import numpy as np
import cv2
  
orb = cv2.ORB_create(nfeatures=2000)
cap = cv2.VideoCapture(0)
while(cap.isOpened()):
      
    while True:
          
        ret, img = cap.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kp = orb.detect(gray, None)
        kp, des = orb.compute(gray, kp)
        img2 = cv2.drawKeypoints(gray, kp, None, color=(0,255,0), flags=0)

        cv2.imshow('img', img2)
        if cv2.waitKey(30) & 0xff == ord('q'):
            break
              
    cap.release()
    cv2.destroyAllWindows()
else:
    print("Alert ! Camera disconnected")