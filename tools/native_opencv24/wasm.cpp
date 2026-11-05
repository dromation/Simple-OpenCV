// Memory-only browser adapter. Uses exactly the same operations as worker.cpp.
#include "operations.hpp"
#include <emscripten/emscripten.h>
#include <cstring>

static std::string lastError;
extern "C" {
EMSCRIPTEN_KEEPALIVE const char* sm_version() { return CV_VERSION; }
EMSCRIPTEN_KEEPALIVE const char* sm_error() { return lastError.c_str(); }
EMSCRIPTEN_KEEPALIVE int sm_process(const float* source, const unsigned char* bytes,
                                  int rows, int cols, const char* yaml, float* result) {
    try {
        lastError.clear();
        if(!source || !bytes || !yaml || !result || rows<1 || cols<1 ||
           (double)rows*cols>16000000) throw std::runtime_error("Invalid browser image");
        cv::FileStorage config(yaml, cv::FileStorage::READ | cv::FileStorage::MEMORY);
        if(!config.isOpened()) throw std::runtime_error("Invalid operation parameters");
        cv::Mat input(rows,cols,CV_32F,const_cast<float*>(source));
        cv::Mat byteInput(rows,cols,CV_8U,const_cast<unsigned char*>(bytes));
        cv::Mat output=motocamOperation(config,input,byteInput);
        if(!output.isContinuous()) output=output.clone();
        std::memcpy(result,output.data,output.total()*sizeof(float));
        return 0;
    } catch(const std::exception& error) { lastError=error.what(); return 1; }
      catch(...) { lastError="Unknown OpenCV 2.4 exception"; return 1; }
}
}
