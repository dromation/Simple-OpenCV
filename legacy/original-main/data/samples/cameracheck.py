import numpy as np
import cv2
  
orb = cv2.ORB_create()
cap = cv2.VideoCapture(2)
while(cap.isOpened()):
      
    while True:
          
        ret, img = cap.read()
     
        cv2.imshow('img', img)
        if cv2.waitKey(30) & 0xff == ord('q'):
            break
              
    cap.release()
    cv2.destroyAllWindows()
else:
    print("Alert ! Camera disconnected")