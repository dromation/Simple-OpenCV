import cv2
import numpy as np
import open3d as o3d

# load images
img1 = cv2.imread('image1.jpg')
img2 = cv2.imread('image2.jpg')

# convert images to grayscale
gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

# perform feature matching
orb = cv2.ORB_create()
kp1, des1 = orb.detectAndCompute(gray1, None)
kp2, des2 = orb.detectAndCompute(gray2, None)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
matches = bf.match(des1, des2)
matches = sorted(matches, key=lambda x: x.distance)

# filter out non-matching points
good_matches = []
for m in matches:
    if m.distance < 50:
        good_matches.append(m)

# extract matching keypoints
src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

# compute fundamental matrix
F, mask = cv2.findFundamentalMat(src_pts, dst_pts, cv2.FM_RANSAC)

# perform stereo rectification
h1, w1 = gray1.shape
h2, w2 = gray2.shape
_, H1, H2 = cv2.stereoRectifyUncalibrated(src_pts, dst_pts, F, (w1, h1))

# compute disparity map
window_size = 3
min_disp = 16
num_disp = 112 - min_disp
stereo = cv2.StereoSGBM_create(minDisparity=min_disp, numDisparities=num_disp, blockSize=window_size)
gray1r = cv2.warpPerspective(gray1, H1, (w1, h1))
gray2r = cv2.warpPerspective(gray2, H2, (w2, h2))
disparity = stereo.compute(gray1r, gray2r)

# create point cloud from disparity map
h, w = disparity.shape[:2]
focal_length = 0.8 * w
Q = np.float32([[1, 0, 0, -0.5 * w],
                [0, -1, 0, 0.5 * h],
                [0, 0, 0, -focal_length],
                [0, 0, 1, 0]])
points = cv2.reprojectImageTo3D(disparity, Q)
colors = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
mask = disparity > disparity.min()
output_points = points[mask]
output_colors = colors[mask]

# create point cloud object using Open3D
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(output_points)
pcd.colors = o3d.utility.Vector3dVector(output_colors)

# create mesh object using Open3D
mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd)

# write mesh to STL file
o3d.io.write_triangle_mesh("output.stl", mesh)
