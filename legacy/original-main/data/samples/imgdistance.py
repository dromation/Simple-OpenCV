import cv2
import numpy as np

# Load the image
img = cv2.imread('f0_hazard_radiation_suit.jpg')

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Apply edge detection to extract object of interest
edges = cv2.Canny(gray, 50, 150)

# Find contours of object
contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Calculate perimeter of each contour and store in list
perimeters = []
for cnt in contours:
    perimeter = cv2.arcLength(cnt, True)
    perimeters.append(perimeter)

# Choose the contour with the largest perimeter as the object of interest
largest_contour_index = np.argmax(perimeters)
largest_contour = contours[largest_contour_index]

# Calculate the distance based on known object size and contour length
object_size = 10  # in centimeters
contour_length = perimeters[largest_contour_index]
pixels_per_centimeter = 10  # adjust this value based on image resolution
distance = (object_size * pixels_per_centimeter) / contour_length

# Print the calculated distance
print('Distance to object: {:.2f} cm'.format(distance))
