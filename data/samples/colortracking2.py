import cv2
import numpy as np

# Define the range of the color to track in HSV format
lower_color = np.array([20, 100, 100])
upper_color = np.array([30, 255, 255])

# Initialize the video capture device
cap = cv2.VideoCapture(1)

while True:
    # Capture the current frame
    ret, frame = cap.read()

    if ret:
        # Convert the frame from BGR to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Threshold the HSV image to get only the specified color
        mask = cv2.inRange(hsv, lower_color, upper_color)

        # Apply a morphological opening to the mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Find the contours in the mask
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw the contours on the original frame
        cv2.drawContours(frame, contours, -1, (0, 255, 0), 3)

        # Display the resulting frame
        cv2.imshow('Color Tracker', frame)

        # Exit if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release the video capture device and close all windows
cap.release()
cv2.destroyAllWindows()
