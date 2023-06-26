import cv2
import numpy as np
from skimage import measure
from stl import mesh

# Load the technical drawing image
img = cv2.imread('technical_drawing.png')

# Pre-process the image
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
blur = cv2.GaussianBlur(thresh, (3, 3), 0)
edges = cv2.Canny(blur, 50, 150)

# Identify the objects in the image
contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Extract the relevant features from the objects
for contour in contours:
    approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
    if len(approx) == 4:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

# Use the extracted features to create a 3D model of the technical drawing
verts, faces, _, _ = measure.marching_cubes(edges)

# Export the 3D model as an STL file
mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        mesh.vectors[i][j] = verts[f[j], :]
mesh.save('technical_drawing.stl')
