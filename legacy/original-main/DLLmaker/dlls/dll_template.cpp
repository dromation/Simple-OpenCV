#include <iostream>

using namespace std;

extern "C" __declspec(dllexport) void HelloWorld()
{
    cout << "Hello World!" << endl;
}
