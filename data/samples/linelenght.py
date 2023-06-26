import cv2
import math

# Load the image
img = cv2.imread('line_image.jpg')

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Apply edge detection
edges = cv2.Canny(gray, 50, 150, apertureSize=3)

# Detect the line in the image
lines = cv2.HoughLinesP(edges, 1, math.pi/180, 100, minLineLength=100, maxLineGap=10)

# Calculate the length of the line
for line in lines:
    x1, y1, x2, y2 = line[0]
    length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    # Draw the line
    cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
    
    # Write the length and measurement units beside the line
    cv2.putText(img, f"{length:.2f} px", (int((x1 + x2) / 2), int((y1 + y2) / 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.putText(img, "mm", (int((x1 + x2) / 2) + 50, int((y1 + y2) / 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Display the image
cv2.imshow('Line Image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
