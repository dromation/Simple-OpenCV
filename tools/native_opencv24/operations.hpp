// Shared genuine OpenCV 2.4 operations for native and WebAssembly adapters. MIT.
#pragma once
#include <opencv2/core/core.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <stdexcept>
#include <vector>
#include <string>

static cv::Mat motocamOperation(const cv::FileStorage& config, const cv::Mat& input,
                               const cv::Mat& bytes) {
    const int rows=input.rows, cols=input.cols, size=(int)config["size"];
    std::string kind; config["kind"] >> kind;
    cv::Mat output;
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
            cv::Mat mask;
            if(kind=="canny") cv::Canny(bytes,mask,(double)config["low"],(double)config["high"],3,true);
            else if(kind=="otsu") cv::threshold(bytes,mask,0,255,cv::THRESH_BINARY|cv::THRESH_OTSU);
            else cv::adaptiveThreshold(bytes,mask,255,cv::ADAPTIVE_THRESH_GAUSSIAN_C,cv::THRESH_BINARY,size,(double)config["offset"]);
            mask.convertTo(output,CV_32F,1.0/255);
        }
        else if(kind=="components") {
            // Exact foreground pixel count, including holes, with 8-connectivity.
            cv::Mat remaining; cv::compare(input,0,remaining,CV_CMP_GT);
            output=cv::Mat::zeros(rows,cols,CV_32F);
            for(int y=0;y<rows;++y) for(int x=0;x<cols;++x) {
                if(remaining.at<unsigned char>(y,x)!=255) continue;
                cv::Rect bounds;
                int area=cv::floodFill(remaining,cv::Point(x,y),cv::Scalar(128),&bounds,cv::Scalar(),cv::Scalar(),8);
                cv::Mat region=remaining(bounds), selected=region==128;
                if(area >= (int)config["minArea"]) output(bounds).setTo(1,selected);
                region.setTo(0,selected);
            }
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
    return output;
}
