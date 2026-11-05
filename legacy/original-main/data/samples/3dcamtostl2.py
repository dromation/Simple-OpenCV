import cv2
import open3d as o3d
import numpy as np

# Set up camera capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Define intrinsic matrix for camera
intrinsic_matrix = np.array([[525.0, 0.0, 319.5],
                             [0.0, 525.0, 239.5],
                             [0.0, 0.0, 1.0]])

# Define Poisson reconstruction parameters
depth_scale = 0.001
depth_trunc = 0.03
voxel_size = 0.005

# Create Open3D visualization window
vis = o3d.visualization.Visualizer()
vis.create_window()

while True:
    # Capture a frame from the camera
    ret, color_frame = cap.read()

    # Convert color frame to grayscale for better performance
    gray_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2GRAY)

    # Threshold grayscale frame to extract object
    _, thresh = cv2.threshold(gray_frame, 50, 255, cv2.THRESH_BINARY)

    # Find contours in thresholded frame
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Select largest contour as object
    object_contour = max(contours, key=cv2.contourArea)

    # Convert object contour to point cloud
    object_depth = np.zeros_like(gray_frame)
    cv2.fillPoly(object_depth, [object_contour], color=(255, 255, 255))
    object_depth = object_depth.astype(np.uint16)
    object_depth = object_depth * depth_scale
    object_point_cloud = o3d.geometry.PointCloud.create_from_depth_image(o3d.geometry.Image(object_depth),
                                                                           intrinsic_matrix)

    # Create mesh from object point cloud using Poisson reconstruction
    object_mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(object_point_cloud,
                                                                               depth_trunc=depth_trunc,
                                                                               voxel_size=voxel_size)

    # Transform mesh to center at origin
    object_mesh.translate(-object_mesh.get_center())

    # Update Open3D visualization window with object mesh
    vis.clear_geometries()
    vis.add_geometry(object_mesh)
    vis.update_geometry()
    vis.poll_events()
    vis.update_renderer()

    # Save object mesh as STL file
    o3d.io.write_triangle_mesh("object_mesh.stl", object_mesh)

    # Check for user input to exit program
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release camera capture and close Open3D visualization window
cap.release()
vis.destroy_window()
