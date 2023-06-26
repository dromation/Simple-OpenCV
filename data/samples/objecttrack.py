"""This code initializes the KCF tracker, tracks the object in the video stream using a bounding box selected by the user, and 
draws a bounding box around the tracked object in each frame. If the object is lost, the user is prompted to select a new bounding box to re-initialize the tracker."""

import cv2

# Load the template image and the video stream
template = cv2.imread('template.jpg', 0)
cap = cv2.VideoCapture('video.mp4')

# Define the object tracking algorithm (KCF in this case)
tracker = cv2.TrackerKCF_create()

# Initialize the tracking by selecting a bounding box around the object
ret, frame = cap.read()
bbox = cv2.selectROI(frame, False)
tracker.init(frame, bbox)

while True:
    # Read a new frame from the video stream
    ret, frame = cap.read()

    if ret:
        # Track the object in the new frame
        success, bbox = tracker.update(frame)

        if success:
            # Draw a bounding box around the tracked object
            x, y, w, h = [int(i) for i in bbox]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2, 1)
        else:
            # Object lost, re-initialize the tracker
            bbox = cv2.selectROI(frame, False)
            tracker.init(frame, bbox)

        # Display the frame with the bounding box around the tracked object
        cv2.imshow('frame', frame)

        # Press 'q' to quit
        if cv2.waitKey(1) == ord('q'):
            break
    else:
        break

# Release the video capture and close the windows
cap.release()
cv2.destroyAllWindows()
