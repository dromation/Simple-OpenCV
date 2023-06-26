import cv2
import math

# Load the image
image = cv2.imread('image.jpg')

# Define the start and end points of the line
start_point = (100, 100)
end_point = (300, 300)

# Draw the line on the image
cv2.line(image, start_point, end_point, (0, 0, 255), 2)

# Calculate the length of the line
length = math.sqrt((end_point[0] - start_point[0]) ** 2 + (end_point[1] - start_point[1]) ** 2)

# Write the length value on the image
cv2.putText(image, '{:.2f} px'.format(length), (int((start_point[0] + end_point[0])/2), int((start_point[1] + end_point[1])/2)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

# Display the image
cv2.imshow('image', image)
cv2.waitKey(0)
