import cv2
import numpy as np

# Load image
img = cv2.imread('ellipse.png')

# Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Find contours
contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

# Fit ellipse to largest contour
if len(contours) > 0:
    c = max(contours, key=cv2.contourArea)
    ellipse = cv2.fitEllipse(c)
    cv2.ellipse(img, ellipse, (0, 255, 0), 2)
    
    # Calculate length of ellipse
    a = ellipse[1][0] / 2
    b = ellipse[1][1] / 2
    length = np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
    print("Length of ellipse: {:.2f}".format(length))
    
    # Draw length measurement on image
    cv2.putText(img, "{:.2f} px".format(length), (int(ellipse[0][0]), int(ellipse[0][1] + b)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
# Show image
cv2.imshow('Image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
