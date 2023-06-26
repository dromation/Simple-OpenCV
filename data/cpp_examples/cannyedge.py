import cv2
import ctypes
import numpy as np

# Load the shared library
lib = ctypes.cdll.LoadLibrary('./example.so')

# Define the function prototype
apply_canny_edge_detection = lib.applyCannyEdgeDetection
apply_canny_edge_detection.argtypes = [
    ctypes.c_void_p,  # inputImage: void pointer
    ctypes.c_void_p,  # outputImage: void pointer
    ctypes.c_double,  # threshold1: double
    ctypes.c_double   # threshold2: double
]

# Load and process an image using the C++ function
input_image = cv2.imread('input_image.jpg')
output_image = np.zeros_like(input_image)
threshold1 = 50
threshold2 = 100
apply_canny_edge_detection(
    input_image.ctypes.data, output_image.ctypes.data, threshold1, threshold2
)

# Display the results
cv2.imshow('Input Image', input_image)
cv2.imshow('Canny Edges', output_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
