import cv2
import numpy as np


def nothing():
    pass


stream = cv2.VideoCapture(0)
stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
stream.set(cv2.CAP_PROP_BRIGHTNESS, 130)

# Create a window
cv2.namedWindow('Frame')

# Create trackbars for color change
# Hue is from 0-179 for Opencv
cv2.createTrackbar('HMin', 'Frame', 0, 179, nothing)
cv2.createTrackbar('SMin', 'Frame', 0, 255, nothing)
cv2.createTrackbar('VMin', 'Frame', 0, 255, nothing)
cv2.createTrackbar('HMax', 'Frame', 0, 179, nothing)
cv2.createTrackbar('SMax', 'Frame', 0, 255, nothing)
cv2.createTrackbar('VMax', 'Frame', 0, 255, nothing)

# Set default value for Max HSV trackbars
cv2.setTrackbarPos('HMax', 'Frame', 179)
cv2.setTrackbarPos('SMax', 'Frame', 255)
cv2.setTrackbarPos('VMax', 'Frame', 255)

# Initialize HSV min/max values
hMin = sMin = vMin = hMax = sMax = vMax = 0
phMin = psMin = pvMin = phMax = psMax = pvMax = 0

while True:

    ret, frame = stream.read()

    # Get current positions of all trackbars
    hMin = cv2.getTrackbarPos('HMin', 'Frame')
    sMin = cv2.getTrackbarPos('SMin', 'Frame')
    vMin = cv2.getTrackbarPos('VMin', 'Frame')
    hMax = cv2.getTrackbarPos('HMax', 'Frame')
    sMax = cv2.getTrackbarPos('SMax', 'Frame')
    vMax = cv2.getTrackbarPos('VMax', 'Frame')

    # Set minimum and maximum HSV values to display
    lower = np.array([hMin, sMin, vMin])
    upper = np.array([hMax, sMax, vMax])

    # Convert to HSV format and color threshold
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Print if there is a change in HSV value
    if (phMin != hMin) | (psMin != sMin) | (pvMin != vMin) | (phMax != hMax) | (psMax != sMax) | (pvMax != vMax):
        print("(hMin = %d , sMin = %d, vMin = %d), (hMax = %d , sMax = %d, vMax = %d)" % (
            hMin, sMin, vMin, hMax, sMax, vMax))
        phMin = hMin
        psMin = sMin
        pvMin = vMin
        phMax = hMax
        psMax = sMax
        pvMax = vMax

    # Display result frame
    cv2.imshow('Frame', result)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
"""

import cv2


stream = cv2.VideoCapture(0)
stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# stream.set(cv2.CAP_PROP_BRIGHTNESS, 130)

while True:

    ret, frame = stream.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    
    (basic_T, basic_threshInv) = cv2.threshold(blurred, 230, 255,
	cv2.THRESH_BINARY_INV)
    
    (otsu_T, otsu_threshInv) = cv2.threshold(blurred, 0, 255,
	cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    adaptive_thresh_mean = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 10)
    adaptive_thresh_gaussian = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10)
    
    masked = cv2.bitwise_and(frame, frame, mask=adaptive_thresh_gaussian)
    
    
    cv2.imshow("Original", frame)
    cv2.imshow("Simple Thresholding", basic_threshInv)
    cv2.imshow("Otsu Thresholding", otsu_threshInv)
    cv2.imshow("Mean Adaptive Thresholding", adaptive_thresh_mean)
    cv2.imshow("Gaussian Adaptive Thresholding", adaptive_thresh_gaussian)
    cv2.imshow("Masked", masked)
    
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
"""