import math

import cv2
import numpy as np


class Camera:
    def __init__(self):
        self.meters = True  # false = inches

        if self.meters:
            self.tag_size = 0.1524
        else:
            self.tag_size = 6

        self.intrinsic_parameters = np.asarray([[660.42091855, 0., 342.7709279], [0., 658.68629884, 231.84135911],
                                                [0., 0., 1.]])
        self.distortion_coefficients = np.asarray([
            [1.72827466e-01, -1.26394997e+00, -7.47066210e-03, 2.81406371e-03, 3.15535405e+00]])

        self.camera_stream = cv2.VideoCapture(1)
        self.frame = None

        self.original_corners, self.corners = None, None
        self.ids = None
        self.pointA, self.pointB, self.pointC, self.pointD = None, None, None, None
        self.centerX, self.centerY = None, None
        self.side1, self.side2, self.side3, self.side4 = None, None, None, None

        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_16h5)
        self.parameters = cv2.aruco.DetectorParameters()
        self.parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)

    @staticmethod
    def calculate_distance_between_two_points(point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def detect_tags(self):

        ret, self.frame = self.camera_stream.read()

        if ret:
            self.original_corners, self.ids, _ = self.detector.detectMarkers(self.frame)
            self.corners = self.original_corners
            markers = []
            if len(self.corners) > 0:
                for marker in range(len(self.corners)):
                    (self.pointA, self.pointB, self.pointC, self.pointD) = self.corners[marker][0]
                    self.pointA = (int(self.pointA[0]), int(self.pointA[1]))
                    self.pointB = (int(self.pointB[0]), int(self.pointB[1]))
                    self.pointC = (int(self.pointC[0]), int(self.pointC[1]))
                    self.pointD = (int(self.pointD[0]), int(self.pointD[1]))

                    self.centerX, self.centerY = (self.pointA[0] + self.pointC[0]) // 2, (
                            self.pointA[1] + self.pointC[1]) // 2

                    self.side1 = self.calculate_distance_between_two_points(self.pointA, self.pointB)
                    self.side2 = self.calculate_distance_between_two_points(self.pointB, self.pointC)
                    self.side3 = self.calculate_distance_between_two_points(self.pointC, self.pointD)
                    self.side4 = self.calculate_distance_between_two_points(self.pointD, self.pointA)

                    markers.append([[self.pointA, self.pointB, self.pointC, self.pointD], (
                        self.centerX, self.centerY), [self.side1, self.side2, self.side3, self.side4]])

            return self.ids, markers, self.corners
