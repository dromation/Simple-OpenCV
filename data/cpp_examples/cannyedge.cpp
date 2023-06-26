#include <opencv2/core/core.hpp>
#include <opencv2/imgproc/imgproc.hpp>

extern "C" {
    void applyCannyEdgeDetection(const cv::Mat& inputImage, cv::Mat& outputImage, double threshold1, double threshold2) {
        cv::Canny(inputImage, outputImage, threshold1, threshold2);
    }
}

#g++ -shared -o example.so example.cpp `pkg-config --cflags --libs opencv`
