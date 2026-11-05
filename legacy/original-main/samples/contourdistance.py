import cv2

# Load the image
img = cv2.imread('f0_hazard_radiation_suit.jpg')

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Apply thresholding to obtain binary image
_, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

# Find contours in the image
contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Iterate through each contour
for i, contour in enumerate(contours):
    # Calculate the length of the contour
    length = cv2.arcLength(contour, True)
    
    # Highlight the contour on the image
    cv2.drawContours(img, [contour], -1, (0, 0, 255), 2)
    
    # Add text indicating the length of the contour
    cv2.putText(img, f"Contour {i+1} length: {length}", (10, 20*(i+1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Show the image
cv2.imshow("Contours", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
