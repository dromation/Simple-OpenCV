import cv2
import ctypes
import numpy as np

class ImageProcessor:
    def __init__(self):
        # Load the shared library
        self.lib = ctypes.cdll.LoadLibrary('./example.so')

        # Define the function prototype
        self.process_image = self.lib.processImage
        self.process_image.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte),  # imageData: unsigned char pointer
            ctypes.c_int,                    # width: int
            ctypes.c_int,                    # height: int
            ctypes.c_int,                    # channels: int
            ctypes.POINTER(ctypes.c_ubyte)   # processedData: unsigned char pointer
        ]
        self.process_image.restype = None

    def process(self, input_image):
        # Prepare the input image data
        height, width, channels = input_image.shape
        input_data = input_image.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))

        # Allocate memory for the processed data
        processed_data = np.zeros((height, width), dtype=np.uint8)
        processed_data_ptr = processed_data.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))

        # Process the image using the C++ function
        self.process_image(input_data, width, height, channels, processed_data_ptr)

        return processed_data


# Create an instance of the ImageProcessor class
processor = ImageProcessor()

# Load and process an image
input_image = cv2.imread('input_image.jpg')
processed_image = processor.process(input_image)

# Display the processed image
cv2.imshow('Processed Image', processed_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
