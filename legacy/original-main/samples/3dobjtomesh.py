import cv2
import open3d as o3d
import numpy as np

# Read images
img1 = cv2.imread('image1.jpg')
img2 = cv2.imread('image2.jpg')

# Extract keypoints and compute descriptors
sift = cv2.SIFT_create()
kp1, des1 = sift.detectAndCompute(img1, None)
kp2, des2 = sift.detectAndCompute(img2, None)

# Match keypoints between images
bf = cv2.BFMatcher()
matches = bf.knnMatch(des1, des2, k=2)
good_matches = []
for m,n in matches:
    if m.distance < 0.75*n.distance:
        good_matches.append(m)

# Estimate fundamental matrix from matches
src_pts = np.float32([ kp1[m.queryIdx].pt for m in good_matches ]).reshape(-1,1,2)
dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good_matches ]).reshape(-1,1,2)
F, mask = cv2.findFundamentalMat(src_pts, dst_pts, cv2.FM_RANSAC)

# Rectify images based on fundamental matrix
h1, w1 = img1.shape[:2]
h2, w2 = img2.shape[:2]
_, H1, H2 = cv2.stereoRectifyUncalibrated(src_pts, dst_pts, F, imgSize=(w1,h1))

# Triangulate points to get 3D coordinates
points4D = cv2.triangulatePoints(H1, H2, src_pts, dst_pts)
points3D = cv2.convertPointsFromHomogeneous(points4D.T)

# Create point cloud from 3D coordinates using Open3D
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points3D.squeeze())

# Create mesh from point cloud using Open3D
mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd)

# Export mesh as STL file using Open3D
o3d.io.write_triangle_mesh("mesh.stl", mesh)
