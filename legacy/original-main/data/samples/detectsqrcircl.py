import cv2

# Read the image
img = cv2.imread('image.jpg')

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Apply Canny edge detection
edges = cv2.Canny(gray, 50, 150, apertureSize=3)

# Find contours in the binary edge image
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# For each contour, approximate its shape and classify it
for cnt in contours:
    approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
    if len(approx) == 4:
        cv2.drawContours(img, [approx], 0, (0, 255, 0), 3)  # Draw a green square
    else:
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        if radius > 10:
            cv2.circle(img, (int(x), int(y)), int(radius), (0, 0, 255), 3)  # Draw a red circle

# Show the image
cv2.imshow('image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
