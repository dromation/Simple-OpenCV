import cv2
import numpy as np
import open3d as o3d

# Set up OpenCV camera object
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Define intrinsic matrix (this should be calibrated for your specific camera)
intrinsic_matrix = np.array([[528.77, 0, 318.27], [0, 527.51, 238.24], [0, 0, 1]])

# Define parameters for depth calculation
depth_scale = 0.001  # Depth is in millimeters, so we need to scale it
depth_clipping_distance = 1000  # Maximum distance to track in millimeters

# Create Open3D point cloud object
pcd = o3d.geometry.PointCloud()

while True:
    # Capture and process each frame
    ret, frame = cap.read()
    if not ret:
        break

    # Convert color image to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Calculate depth map from grayscale image
    depth = cv2.convertScaleAbs(cv2.Laplacian(gray, cv2.CV_16S, ksize=3))
    depth = cv2.normalize(depth, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    depth = cv2.medianBlur(depth, 5)

    # Convert depth map to 3D point cloud using intrinsic matrix and depth scaling
    points = cv2.reprojectImageTo3D(depth, intrinsic_matrix)
    points = points.reshape(-1, 3)
    points = points[points[:, 2] < depth_clipping_distance]
    pcd.points = o3d.utility.Vector3dVector(points)

    # Visualize point cloud and wait for key press to exit
    o3d.visualization.draw_geometries([pcd])
    if cv2.waitKey(1) == ord('q'):
        break

# Release camera and destroy OpenCV window
cap.release()
cv2.destroyAllWindows()
