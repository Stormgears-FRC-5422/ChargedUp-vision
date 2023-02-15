import math

import cv2
import numpy as np
from scipy.spatial.transform import Rotation
from transformations import euler_from_quaternion

from Camera import Camera
from Constants import *


class MarkerDetection:

    def __init__(self):

        self.camera_properties = Camera()

        self.meters = True  # false = inches

        self.tag_size = TAG_SIZE
        self.intrinsic_parameters, self.distortion_coefficients = self.camera_properties.get_camera_properties()

        self.markers = []
        self.original_corners, self.corners = None, None
        self.ids = None
        self.pointA, self.pointB, self.pointC, self.pointD = None, None, None, None
        self.center, self.centerX, self.centerY = None, None, None
        self.side_lengths, self.side1, self.side2, self.side3, self.side4 = None, None, None, None, None

        self.rotational_vectors, self.translation_vectors = None, None
        self.distance, self.roll, self.yaw, self.pitch = None, None, None, None

        self.information = {}

        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_16h5)
        self.parameters = cv2.aruco.DetectorParameters()
        self.parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)

    @staticmethod
    def __calculate_distance_between_two_points(point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def __detect_tags(self, frame):
        self.original_corners, self.ids, _ = self.detector.detectMarkers(frame)
        self.corners = self.original_corners
        self.markers = []
        if len(self.corners) > 0:
            for marker in range(len(self.corners)):
                (self.pointA, self.pointB, self.pointC, self.pointD) = self.corners[marker][0]
                self.pointA = (int(self.pointA[0]), int(self.pointA[1]))
                self.pointB = (int(self.pointB[0]), int(self.pointB[1]))
                self.pointC = (int(self.pointC[0]), int(self.pointC[1]))
                self.pointD = (int(self.pointD[0]), int(self.pointD[1]))

                self.centerX, self.centerY = (self.pointA[0] + self.pointC[0]) // 2, (
                        self.pointA[1] + self.pointC[1]) // 2

                self.side1 = self.__calculate_distance_between_two_points(self.pointA, self.pointB)
                self.side2 = self.__calculate_distance_between_two_points(self.pointB, self.pointC)
                self.side3 = self.__calculate_distance_between_two_points(self.pointC, self.pointD)
                self.side4 = self.__calculate_distance_between_two_points(self.pointD, self.pointA)

                self.markers.append([[self.pointA, self.pointB, self.pointC, self.pointD], (self.centerX, self.centerY),
                                     [self.side1, self.side2, self.side3, self.side4]])
        else:
            self.__no_markers_found()

    def __calculate_distance_angle(self):
        if self.markers:
            for marker in range(len(self.markers)):
                self.corners, self.center, self.side_lengths = self.markers[marker][0], self.markers[marker][1], \
                    self.markers[marker][2]

                self.rotational_vectors, self.translation_vectors, _ = cv2.aruco.estimatePoseSingleMarkers(
                    self.original_corners[marker], self.tag_size, self.intrinsic_parameters,
                    self.distortion_coefficients)
                self.distance = np.round(np.linalg.norm(self.translation_vectors), 3)

                rotation_matrix = np.eye(4)
                rotation_matrix[0:3, 0:3] = cv2.Rodrigues(np.array(self.rotational_vectors[0]))[0]
                r = Rotation.from_matrix(rotation_matrix[0:3, 0:3])
                quaternion = r.as_quat()

                transform_rotation_x = quaternion[0]
                transform_rotation_y = quaternion[1]
                transform_rotation_z = quaternion[2]
                transform_rotation_w = quaternion[3]

                self.roll, self.yaw, self.pitch = euler_from_quaternion(
                    [transform_rotation_x, transform_rotation_y, transform_rotation_z, transform_rotation_w])

                self.roll = np.round(math.degrees(self.roll), 3)
                self.yaw = np.round(math.degrees(self.yaw), 3)
                self.pitch = np.round(math.degrees(self.pitch), 3)

                self.information[self.ids[marker][0]] = [self.distance, self.roll, self.yaw, self.pitch]

    def get_information(self, frame):
        self.information.clear()
        self.__detect_tags(frame)
        self.__calculate_distance_angle()
        return self.information

    def __no_markers_found(self):
        self.distance, self.roll, self.yaw, self.pitch = None, None, None, None
