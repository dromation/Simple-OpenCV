import cv2

# Load the template image and the main image
template = cv2.imread('template.png', cv2.IMREAD_GRAYSCALE)
image = cv2.imread('image.png', cv2.IMREAD_GRAYSCALE)

# Get the width and height of the template image
w, h = template.shape[::-1]

# Apply template matching
res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
threshold = 0.8
loc = np.where(res >= threshold)

# Draw a rectangle around the detected objects
for pt in zip(*loc[::-1]):
    cv2.rectangle(image, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)

# Display the image with the detected objects
cv2.imshow('Detected Objects', image)
cv2.waitKey(0)
cv2.destroyAllWindows()

"""In this example, we first load the template image and the main image, then get the width and height of the template image. We then apply template matching using cv2.matchTemplate()
and a chosen matching method. In this case, we're using cv2.TM_CCOEFF_NORMED which is one of the more robust methods. We set a threshold for the matching score, and use np.where() 
to get the coordinates of the locations where the score is greater than or equal to the threshold. Finally, we draw a rectangle around each detected object using cv2.rectangle()
and display the image with the detected objects using cv2.imshow()."""