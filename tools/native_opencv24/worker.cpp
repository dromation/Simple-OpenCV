// SimpleMotocam native OpenCV 2.4 worker. Project MIT license applies.
#include <opencv2/core/core.hpp>
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
    try {
        if (argc!=2) throw std::runtime_error("Expected request.yml");
        cv::FileStorage config(argv[1],cv::FileStorage::READ);
        if (!config.isOpened()) throw std::runtime_error("Cannot read request");
        int rows=(int)config["rows"], cols=(int)config["cols"];
        if (rows<1 || cols<1 || (double)rows*cols>100000000) throw std::runtime_error("Invalid shape");
        std::string kind; config["kind"] >> kind;
        cv::Mat input=readPlane("input.bin",rows,cols,CV_32F), output;
        int size=(int)config["size"];
        if(kind=="gaussian") cv::GaussianBlur(input,output,cv::Size(size,size),(double)config["sigma"],0,cv::BORDER_REFLECT_101);
        else if(kind=="median") cv::medianBlur(input,output,size);
        else if(kind=="box") cv::blur(input,output,cv::Size(size,size));
        else if(kind=="bilateral") cv::bilateralFilter(input,output,size,(double)config["colorSigma"],(double)config["sigma"]);
        else if(kind=="kernel") {cv::Mat kernel;config["kernel"]>>kernel;cv::filter2D(input,output,-1,kernel,cv::Point(-1,-1),0,cv::BORDER_REFLECT_101);}
        else if(kind=="laplacian") cv::Laplacian(input,output,CV_32F,1);
        else if(kind=="threshold") cv::threshold(input,output,(double)config["threshold"],1,cv::THRESH_BINARY);
        else if(kind=="sobel" || kind=="scharr") {
            cv::Mat dx,dy,kx,ky;
            if(kind=="scharr") { cv::Scharr(input,dx,CV_32F,1,0,1.0/32);cv::Scharr(input,dy,CV_32F,0,1,1.0/32); }
            else { cv::getDerivKernels(kx,ky,1,0,size,true,CV_32F);cv::sepFilter2D(input,dx,-1,kx,ky);cv::getDerivKernels(kx,ky,0,1,size,true,CV_32F);cv::sepFilter2D(input,dy,-1,kx,ky); }
            cv::magnitude(dx,dy,output);
        }
        else if(kind=="erode" || kind=="dilate" || kind=="opening" || kind=="closing" || kind=="morph_gradient") {
            int op=kind=="erode"?cv::MORPH_ERODE:kind=="dilate"?cv::MORPH_DILATE:kind=="opening"?cv::MORPH_OPEN:kind=="closing"?cv::MORPH_CLOSE:cv::MORPH_GRADIENT;
            cv::morphologyEx(input,output,op,cv::Mat::ones(size,size,CV_8U),cv::Point(-1,-1),(int)config["iterations"]);
        }
        else if(kind=="canny" || kind=="otsu" || kind=="adaptive") {
            cv::Mat bytes=readPlane("byte.bin",rows,cols,CV_8U),mask;
            if(kind=="canny") cv::Canny(bytes,mask,(double)config["low"],(double)config["high"],3,true);
            else if(kind=="otsu") cv::threshold(bytes,mask,0,255,cv::THRESH_BINARY|cv::THRESH_OTSU);
            else cv::adaptiveThreshold(bytes,mask,255,cv::ADAPTIVE_THRESH_GAUSSIAN_C,cv::THRESH_BINARY,size,(double)config["offset"]);
            mask.convertTo(output,CV_32F,1.0/255);
        }
        else if(kind=="hough") {
            cv::Mat mask=input>0;
            std::vector<cv::Vec4i> lines;
            cv::HoughLinesP(mask,lines,1,CV_PI/180,(int)config["votes"],(double)config["minLength"],(double)config["maxGap"]);
            output=cv::Mat::zeros(rows,cols,CV_32F);
            for(size_t i=0;i<lines.size();++i) cv::line(output,cv::Point(lines[i][0],lines[i][1]),cv::Point(lines[i][2],lines[i][3]),cv::Scalar(1),1);
        }
        else throw std::runtime_error("Unsupported OpenCV 2.4 operation");
        if(output.type()!=CV_32F || output.rows!=rows || output.cols!=cols || !cv::checkRange(output)) throw std::runtime_error("Invalid result");
        if(!output.isContinuous()) output=output.clone();
        std::ofstream stream("out.bin",std::ios::binary);
        stream.write(reinterpret_cast<const char*>(output.data),output.total()*sizeof(float));
        if(!stream) throw std::runtime_error("Cannot write result");
        return 0;
    } catch(const std::exception& error) { std::ofstream("error.txt") << error.what(); return 1; }
}
