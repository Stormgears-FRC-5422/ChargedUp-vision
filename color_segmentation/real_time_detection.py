import cv2
import numpy as np
from matplotlib import pyplot as plt
import glob
import time

# Constants
area_threshold = 3000
# lower_yellow = np.array([22, 93, 0])
# upper_yellow = np.array([45, 255, 255])
# lower_yellow = np.array([10, 35, 100])
lower_yellow = np.array([10, 180, 100])
upper_yellow = np.array([45, 255, 255])

# lower_purple = np.array([120, 50, 50])
# upper_purple = np.array([170, 255, 255])
lower_purple = np.array([115, 35, 100])
upper_purple = np.array([140, 255, 255])

stream = cv2.VideoCapture(2)
stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
stream.set(cv2.CAP_PROP_BRIGHTNESS, 100)

def determine_color(value):
    if lower_yellow[0] <= value[0] <= upper_yellow[0] and lower_yellow[1] <= value[1] <= upper_yellow[1] and lower_yellow[2] <= value[2] <= upper_yellow[2]:
        return "yellow"
    elif lower_purple[0] <= value[0] <= upper_purple[0] and lower_purple[1] <= value[1] <= upper_purple[1] and lower_purple[2] <= value[2] <= upper_purple[2]:
        return "purple"
    else: return "none"


while True:
    
    start = time.time()
    _, image = stream.read()
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
    
    image_copy = image.copy()
    cv2.drawContours(image_copy, hulls, -1, (0, 255, 0), -1)
    
    # print("----------------------------------")
    for i, c in enumerate(hulls):
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * perimeter, True)
        
        M = cv2.moments(c)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        
        color = determine_color(image_hsv[cY, cX])
        
        cv2.circle(image_copy, (cX, cY), 7, (255, 255, 255), -1)
        
        x, y = tuple(c[0][0])

        if color == "yellow":
            cv2.putText(image_copy, "Cone: Sides " + str(len(approx)), (x - 50, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0),
                        2)
            print("Cone at: " + str(cX) + ", " + str(cY))
        elif color == "purple":
            cv2.putText(image_copy, "Cube: Sides " + str(len(approx)), (x - 50, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0),
                        2)
            print("Cube at: " + str(cX) + ", " + str(cY))
        # print("Contour #{} -- perimeter: {}, approx: {}, area: {}".format(i + 1, perimeter, len(approx), cv2.contourArea(c)))

    cv2.line(image_copy, (217, 480), (253, 0), (0, 0, 255), 2)
    # draw a blue vertical line in the middle of the frame
    cv2.line(image_copy, (320, 480), (320, 0), (255, 0, 0), 2)
    end = time.time()

    # put the time taken text in the corner of the frame
    cv2.putText(image_copy, "Time taken: {:.2f}ms".format((end - start) * 1000), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 255, 0), 2)

    cv2.imshow('image', image_copy)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


