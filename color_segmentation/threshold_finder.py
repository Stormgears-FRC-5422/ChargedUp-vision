import glob

import cv2
import numpy as np


def nothing():
    pass


stream = cv2.VideoCapture(2)
stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
stream.set(cv2.CAP_PROP_BRIGHTNESS, 0)

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
path = 'C:/Users/rajam/PycharmProjects/ChargedUpObjectDetectionData/EdgeImpulse/training/*.jpg'

images = glob.glob(path)

while True:

    ret, frame = stream.read()
    # frame = cv2.imread(images[265])
    # frame = cv2.resize(frame, (0, 0), fx=0.3, fy=0.3)

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
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
