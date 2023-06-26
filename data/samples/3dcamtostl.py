import cv2
import numpy as np
import open3d as o3d

# Initialize camera capture
cap = cv2.VideoCapture(0)

# Define intrinsic camera parameters
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fx = fy = 500  # example values, adjust according to your camera
cx = width / 2
cy = height / 2
intrinsic = o3d.camera.PinholeCameraIntrinsic(width, height, fx, fy, cx, cy)

# Define parameters for creating the point cloud
depth_scale = 0.001  # adjust this value according to your camera
depth_trunc = 5.0  # adjust this value according to your scene
block_size = 2
disparity_multiplier = 64
num_disparities = 128

# Create Open3D visualizer
vis = o3d.visualization.Visualizer()
vis.create_window()

# Start capturing frames from the camera
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Compute depth map using stereo matching
    stereo = cv2.StereoSGBM_create(minDisparity=-1, numDisparities=num_disparities, blockSize=block_size,
                                    P1=8 * 3 * block_size ** 2, P2=32 * 3 * block_size ** 2, disp12MaxDiff=1,
                                    preFilterCap=63, uniquenessRatio=10, speckleWindowSize=100, speckleRange=32)
    disparity = stereo.compute(gray[:, :width // 2], gray[:, width // 2:])
    depth = depth_scale * fx * disparity / disparity_multiplier
    depth[depth > depth_trunc] = 0

    # Create Open3D point cloud from depth map
    pcd = o3d.geometry.PointCloud.create_from_depth_image(o3d.geometry.Image(depth), intrinsic)

    # Remove NaN values from the point cloud
    pcd = pcd.select_by_index(np.where(~np.isnan(pcd.points[:, 0]))[0])

    # Create mesh from the point cloud
    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd)

    # Update Open3D visualizer with the point cloud and mesh
    vis.clear_geometries()
    vis.add_geometry(pcd)
    vis.add_geometry(mesh)
    vis.update_geometry()
    vis.poll_events()
    vis.update_renderer()

    # Check for key presses to quit the program
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the Open3D visualizer
cap.release()
vis.destroy_window()

# Save mesh as STL file
o3d.io.write_triangle_mesh("mesh.stl", mesh)
