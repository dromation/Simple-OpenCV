import cv2
import numpy as np

# Load the reference image or template to detect
template = cv2.imread("template.png")

# Set up the video capture device (0 is the default camera)
cap = cv2.VideoCapture(0)

# Define the codec and create VideoWriter object for saving output video
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))

# Define the tracker function for object detection and tracking
def track_object(frame, template):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Match the template to the frame using correlation coefficient method
    res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    
    # Find the location of the template in the frame with maximum correlation coefficient
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    top_left = max_loc
    
    # Compute the bottom right corner of the template rectangle
    w, h = template.shape[:-1]
    bottom_right = (top_left[0] + w, top_left[1] + h)
    
    # Draw a rectangle around the template on the frame
    cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 2)
    
    # Calculate the distance of the object from the camera
    focal_length = 800 # Set the focal length of the camera in pixels
    object_width = w # Set the width of the object in mm
    image_width = frame.shape[1] # Get the width of the image in pixels
    distance = (focal_length * object_width) / (max_loc[0] + w/2 - image_width/2)
    
    # Write the distance on the frame
    cv2.putText(frame, "Distance: {:.2f} mm".format(distance), (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    
    return frame

# Main loop for object detection and tracking
while True:
    # Capture a frame from the video stream
    ret, frame = cap.read()
    
    if ret:
        # Call the tracker function to detect and track the object in the frame
        frame = track_object(frame, template)
        
        # Display the frame in a window
        cv2.imshow("Frame", frame)
        
        # Write the frame to the output video file
        out.write(frame)
        
        # Press 'q' to exit
        if cv2.waitKey(1) == ord('q'):
            break
    else:
        break

# Release the video capture device, close all windows, and release the output video
cap.release()
out.release()
cv2.destroyAllWindows()
