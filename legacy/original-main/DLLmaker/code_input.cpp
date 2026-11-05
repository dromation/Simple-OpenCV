#include <windows.h>

// Define the function to be exported
extern "C" __declspec(dllexport) int add(int a, int b)
{
    return a + b;
}

// Entry point for the DLL
BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved)
{
    return TRUE;
}
