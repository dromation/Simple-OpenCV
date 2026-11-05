import numpy as np
import cv2 as cv

#this method will display one image
cap = cv.VideoCapture(0)
stereo = cv.StereoBM_create(numDisparities=16, blockSize=15)

while(cap.isOpened()):
      
    while True:
          
        ret, img1 = cap.read()
        ret, img2 = cap.read()
        ret, img3 = cap.read()
        #gray1 = cv.cvtColor(img1, cv.COLOR_BGR2GRAY)
        #gray2 = cv.cvtColor(img2, cv.COLOR_BGR2GRAY)
        #gray3 = cv.cvtColor(img3, cv.COLOR_BGR2GRAY)
        diff1 = img2 - img1
        diff2 = img3 - img1
        dray1 = cv.cvtColor(diff1, cv.COLOR_BGR2GRAY)
        dray2 = cv.cvtColor(diff1, cv.COLOR_BGR2GRAY)

        #diff3 = diff2 - diff1
        imgL = diff1
        imgR = diff2
        #disparity = stereo.compute(imgL,imgR)
        #plt.imshow(disparity,'gray')
        #plt.show()
        cv.imshow('img', diff2)
        if cv.waitKey(30) & 0xff == ord('q'):
            break
              
    cap.release()
    cv.destroyAllWindows()
else:
    print("Alert ! Camera disconnected")




#standard code
"""
import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
imgL = cv.imread('tsukuba_l.png', cv.IMREAD_GRAYSCALE)
imgR = cv.imread('tsukuba_r.png', cv.IMREAD_GRAYSCALE)
stereo = cv.StereoBM_create(numDisparities=16, blockSize=15)
disparity = stereo.compute(imgL,imgR)
plt.imshow(disparity,'gray')
plt.show()
"""