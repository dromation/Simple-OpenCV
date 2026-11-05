import numpy as np
import cv2

#this method will display one image
orb = cv2.ORB_create(nfeatures=2000)
cap = cv2.VideoCapture(0)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

while(cap.isOpened()):
      
    while True:
          
        ret, img = cap.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        kp, des = orb.detectAndCompute(gray,None)

        matches = bf.match(des, des)
        matches = sorted(matches, key = lambda x:x.distance)
        img2 = cv2.drawMatches(gray,kp,gray, kp,matches[:10],None,flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

        cv2.imshow('img', img2)
        if cv2.waitKey(30) & 0xff == ord('q'):
            break
              
    cap.release()
    cv2.destroyAllWindows()
else:
    print("Alert ! Camera disconnected")
#this method will display two images
"""
orb = cv2.ORB_create(nfeatures=2000)
cap = cv2.VideoCapture(0)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

while(cap.isOpened()):
      
    while True:
          
        ret, img = cap.read()
        gray1 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        kp1, des1 = orb.detectAndCompute(gray1,None)
        kp2, des2 = orb.detectAndCompute(gray2,None)

        matches = bf.match(des1, des2)
        matches = sorted(matches, key = lambda x:x.distance)
        img3 = cv2.drawMatches(gray1,kp1,gray2,kp2,matches[:10],None,flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

        cv2.imshow('img', img3)
        if cv2.waitKey(30) & 0xff == ord('q'):
            break
              
    cap.release()
    cv2.destroyAllWindows()
else:
    print("Alert ! Camera disconnected")
"""