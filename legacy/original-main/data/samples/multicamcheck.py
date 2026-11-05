import numpy as np
import cv2

captures = [
    cv2.VideoCapture(0, cv2.CAP_DSHOW),
    cv2.VideoCapture(1, cv2.CAP_DSHOW),
    #cv2.VideoCapture("http://192.168.0.11:8080/video", cv2.CAP_DSHOW),  # ipwebcam address
]


while True:  # while true, read the camera
    frames = []
    for cap in captures:
        ret, frame = cap.read()
        frames.append((frame if ret else None))

    for i, frame in enumerate(frames):
        if frame is not None:  # None if not captured
            cv2.imshow(f"cam{i}", frame)

    # to break the loop and terminate the program
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

for cap in captures:
    cap.release()