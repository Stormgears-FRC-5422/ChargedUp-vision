import cv2
import numpy as np
from matplotlib import pyplot as plt
import glob
import time

# Constants
area_threshold = 1000
# lower_yellow = np.array([22, 93, 0])
# upper_yellow = np.array([45, 255, 255])
lower_yellow = np.array([25, 35, 100])
upper_yellow = np.array([45, 255, 255])

# lower_purple = np.array([120, 50, 50])
# upper_purple = np.array([170, 255, 255])
lower_purple = np.array([120, 35, 100])
upper_purple = np.array([140, 255, 255])

path = 'C:/Users/rajam/PycharmProjects/ChargedUpObjectDetectionData/EdgeImpulse/training/*.jpg'

images = glob.glob(path)

for image in images:
    start = time.time()
    image = cv2.imread(image)
    image = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)

    image_threshold_purple = cv2.inRange(image_hsv, lower_purple, upper_purple)
    image_threshold_yellow = cv2.inRange(image_hsv, lower_yellow, upper_yellow)

    kernel = np.ones((15, 15))
    threshold_yellow_open = cv2.morphologyEx(image_threshold_yellow, cv2.MORPH_OPEN, kernel)
    threshold_purple_open = cv2.morphologyEx(image_threshold_purple, cv2.MORPH_OPEN, kernel)

    combined = cv2.bitwise_or(threshold_yellow_open, threshold_purple_open)

    contours, hierarchy = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hulls = [cv2.convexHull(c) for c in contours]
    hulls = [h for h in hulls if cv2.contourArea(h) > area_threshold]
    print("----------------------------------")
    for i, c in enumerate(hulls):
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * perimeter, True)
        x, y = tuple(c[0][0])

        if 3 <= len(approx) <= 4:
            cv2.putText(image, "Cone: Sides " + str(len(approx)), (x - 50, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0),
                        2)
        elif len(approx) >= 5 & len(approx) <= 7:
            cv2.putText(image, "Cube: Sides " + str(len(approx)), (x - 50, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0),
                        2)
        print("Contour #{} -- perimeter: {}, approx: {}, area: {}".format(i + 1, perimeter, len(approx), cv2.contourArea(c)))

    image_copy = image.copy()
    cv2.drawContours(image_copy, hulls, -1, (0, 255, 0), -1)

    end = time.time()

    # put the time taken text in the corner of the frame
    cv2.putText(image_copy, "Time taken: {:.2f}ms".format((end - start) * 1000), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 255, 0), 2)

    cv2.imshow('image', image_copy)
    cv2.waitKey(0)
