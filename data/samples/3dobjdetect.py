import cv2
import numpy as np

# Load the object 3D model
obj_model = cv2.imread('object_model.png', 0)
obj_keypoints, obj_descriptors = cv2.detectAndCompute(obj_model, None)

# Initialize the camera
cap = cv2.VideoCapture(0)

# Initialize the matcher
matcher = cv2.FlannBasedMatcher_create()

while True:
    # Read a frame from the camera
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect keypoints and descriptors in the frame
    keypoints, descriptors = cv2.detectAndCompute(gray, None)
    
    # Match the descriptors of the object model and the frame
    matches = matcher.match(obj_descriptors, descriptors)
    
    # Sort the matches by distance
    matches = sorted(matches, key=lambda x: x.distance)
    
    # Draw the top 10 matches on the frame
    img_matches = cv2.drawMatches(obj_model, obj_keypoints, gray, keypoints, matches[:10], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    
    # Display the resulting image
    cv2.imshow('Object Detection', img_matches)
    
    # Calculate the distance between the object and the camera
    focal_length = 500 # In pixels
    object_width = 10 # In centimeters
    object_pixel_width = obj_model.shape[1] # In pixels
    distance = (object_width * focal_length) / object_pixel_width
    
    # Print the distance
    print('Distance to object: {} cm'.format(distance))
    
    # Wait for a key press
    if cv2.waitKey(1) == ord('q'):
        break

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()
