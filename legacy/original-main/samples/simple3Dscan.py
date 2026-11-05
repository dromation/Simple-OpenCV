#a simple 3d scan from an image

import cv2
import open3d as o3d

# capture depth image using OpenCV
depth_image = cv2.imread('depth_image.png', cv2.IMREAD_UNCHANGED)

# convert depth image to point cloud using Open3D
depth = o3d.geometry.Image(depth_image)
intrinsic = o3d.camera.PinholeCameraIntrinsic(
    depth_image.shape[1], depth_image.shape[0], fx=525, fy=525, cx=319.5, cy=239.5)
pcd = o3d.geometry.PointCloud.create_from_depth_image(depth, intrinsic)

# create mesh from point cloud using Open3D
mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd)

# export mesh as STL file using Open3D
o3d.io.write_triangle_mesh("mesh.stl", mesh)
