import open3d as o3d
import numpy as np

# Load the STL file
mesh = o3d.io.read_triangle_mesh("object.stl")

# Convert the mesh to a point cloud
pcd = mesh.sample_points_poisson_disk(number_of_points=10000)

# Perform feature extraction on the point cloud
radius_normal = 0.1
pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))

radius_feature = 0.2
pcd_fpfh = o3d.pipelines.registration.compute_fpfh_feature(pcd, o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100))

# Load the target object
target_mesh = o3d.io.read_triangle_mesh("target.stl")
target_pcd = target_mesh.sample_points_poisson_disk(number_of_points=10000)

# Perform feature extraction on the target object
target_pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))
target_pcd_fpfh = o3d.pipelines.registration.compute_fpfh_feature(target_pcd, o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100))

# Perform point cloud registration to find the object in the scene
threshold = 0.5
result = o3d.pipelines.registration.registration_fast_based_on_feature_matching(
    pcd, target_pcd,
    pcd_fpfh, target_pcd_fpfh,
    o3d.pipelines.registration.FastGlobalRegistrationOption(
        maximum_correspondence_distance=threshold))
    
# Get the transformation matrix and apply it to the target object
transformation_matrix = result.transformation
target_mesh.transform(transformation_matrix)

# Visualize the result
o3d.visualization.draw_geometries([pcd, target_mesh])
