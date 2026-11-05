// SimpleMotocam native OpenCV 2.4 worker. Project MIT license applies.
#include "operations.hpp"
#include <opencv2/imgproc/imgproc.hpp>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <string>

static cv::Mat readPlane(const char* name, int rows, int cols, int type) {
    cv::Mat result(rows, cols, type);
    std::ifstream stream(name, std::ios::binary);
    if (!stream.read(reinterpret_cast<char*>(result.data), result.total()*result.elemSize()))
        throw std::runtime_error("Cannot read input plane");
    return result;
}
int main(int argc, char** argv) {
    if (argc==2 && std::string(argv[1])=="--version") { std::cout << CV_VERSION << std::endl; return 0; }
    if (argc==2 && std::string(argv[1])=="--protocol") { std::cout << 2 << std::endl; return 0; }
    try {
        if (argc!=2) throw std::runtime_error("Expected request.yml");
        cv::FileStorage config(argv[1],cv::FileStorage::READ);
        if (!config.isOpened()) throw std::runtime_error("Cannot read request");
        int rows=(int)config["rows"], cols=(int)config["cols"];
        if (rows<1 || cols<1 || (double)rows*cols>100000000) throw std::runtime_error("Invalid shape");
        std::string kind; config["kind"] >> kind;
        cv::Mat input=readPlane("input.bin",rows,cols,CV_32F), output;
        cv::Mat bytes;
        if(kind=="canny" || kind=="otsu" || kind=="adaptive")
            bytes=readPlane("byte.bin",rows,cols,CV_8U);
        output=motocamOperation(config,input,bytes);
        if(!output.isContinuous()) output=output.clone();
        std::ofstream stream("out.bin",std::ios::binary);
        stream.write(reinterpret_cast<const char*>(output.data),output.total()*sizeof(float));
        if(!stream) throw std::runtime_error("Cannot write result");
        return 0;
    } catch(const std::exception& error) { std::ofstream("error.txt") << error.what(); return 1; }
}
