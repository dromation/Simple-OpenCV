#include <opencv2/opencv.hpp>
#include <open3d/Open3D.h>

int main() {
    // capture depth image using OpenCV
    cv::Mat depth_image = cv::imread("depth_image.png", cv::IMREAD_UNCHANGED);

    // convert depth image to point cloud using Open3D
    auto depth = open3d::geometry::Image::CreateDepthImageFromNumpy(depth_image);
    open3d::camera::PinholeCameraIntrinsic intrinsic(depth_image.cols, depth_image.rows, 525, 525, 319.5, 239.5);
    auto pcd = open3d::geometry::PointCloud::CreateFromDepthImage(depth, intrinsic);

    // create mesh from point cloud using Open3D
    auto mesh = open3d::geometry::TriangleMesh::CreateFromPointCloudPoisson(*pcd);

    // export mesh as STL file using Open3D
    open3d::io::WriteTriangleMesh("mesh.stl", *mesh);
}
