import numpy as np
import cv2
import time

class DetectFieldElement:
    
    def __init__(self):
        self.area_threshold = 3000

        self.lower_yellow = np.array([10, 180, 100])
        self.upper_yellow = np.array([45, 255, 255])


        self.lower_purple = np.array([115, 35, 100])
        self.upper_purple = np.array([140, 255, 255])
        self.kernel = np.ones((15, 15))

    def determine_color(self, value):
        if self.lower_yellow[0] <= value[0] <= self.upper_yellow[0] and self.lower_yellow[1] <= value[1] <= self.upper_yellow[1] and self.lower_yellow[2] <= value[2] <= self.upper_yellow[2]:
            return "yellow"
        elif self.lower_purple[0] <= value[0] <= self.upper_purple[0] and self.lower_purple[1] <= value[1] <= self.upper_purple[1] and self.lower_purple[2] <= value[2] <= self.upper_purple[2]:
            return "purple"
        else: return "none"

    def detect_field_element(self, frame):
        start = time.time()
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)

        image_threshold_purple = cv2.inRange(image_hsv, self.lower_purple, self.upper_purple)
        image_threshold_yellow = cv2.inRange(image_hsv, self.lower_yellow, self.upper_yellow)
        
        combined = cv2.bitwise_or(image_threshold_yellow, image_threshold_purple)
        
        combined_open = cv2.morphologyEx(combined, cv2.MORPH_OPEN, self.kernel)

        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        hulls = [cv2.convexHull(c) for c in contours]
        hulls = [h for h in hulls if cv2.contourArea(h) > self.area_threshold]
        
        image_copy = frame.copy()
        
        cv2.drawContours(image_copy, hulls, -1, (0, 255, 0), -1)
        cones = []
        cubes = []
        for i, c in enumerate(hulls):
            perimeter = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.04 * perimeter, True)
            
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            
            color = self.determine_color(image_hsv[cY, cX])
            
            cv2.circle(image_copy, (cX, cY), 7, (255, 255, 255), -1)
            
            x, y = tuple(c[0][0])

            if color == "yellow":
                cv2.putText(image_copy, "Cone: Sides " + str(len(approx)), (x - 50, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0),
                            2)
                cones.append([cX, cY])
                print("Cone at: " + str(cX) + ", " + str(cY))
            elif color == "purple":
                cv2.putText(image_copy, "Cube: Sides " + str(len(approx)), (x - 50, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0),
                            2)
                cubes.append([cX, cY])
                print("Cube at: " + str(cX) + ", " + str(cY))
            # print("Contour #{} -- perimeter: {}, approx: {}, area: {}".format(i + 1, perimeter, len(approx), cv2.contourArea(c)))

        cv2.line(image_copy, (217, 480), (253, 0), (0, 0, 255), 2)
        # draw a blue vertical line in the middle of the frame
        cv2.line(image_copy, (320, 480), (320, 0), (255, 0, 0), 2)
        end = time.time()

        # put the time taken text in the corner of the frame
        cv2.putText(image_copy, "Time taken: {:.2f}ms".format((end - start) * 1000), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 0), 2)
        
        return {"frame" : image_copy, "cones" : cones, "cubes" : cubes} 

