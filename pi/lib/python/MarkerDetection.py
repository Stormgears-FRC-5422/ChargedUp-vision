import math

import cv2
import numpy as np
import time
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



        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_16h5)
        self.parameters = cv2.aruco.DetectorParameters()
        self.parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)

    @staticmethod
    def __calculate_distance_between_two_points(point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def __detect_tags(self, frame):
        marker_info, ids, _ = self.detector.detectMarkers(frame)
        markers = []
        
        frame_copy = frame.copy()
        frame_copy = cv2.aruco.drawDetectedMarkers(frame_copy, marker_info)
        
        if len(marker_info) > 0:
            for i,marker in enumerate(marker_info):
                corners = marker[0]
#                (pointA, pointB, pointC, pointD) = [ (int(x),int(y)) for (x,y) in corner]

                side1 = self.__calculate_distance_between_two_points(corners[0],corners[1])
                side2 = self.__calculate_distance_between_two_points(corners[1],corners[2])
                side3 = self.__calculate_distance_between_two_points(corners[2],corners[3])
                side4 = self.__calculate_distance_between_two_points(corners[3],corners[0])
                
                id = ids[i][0]

                markers.append([id,corners,[side1, side2, side3, side4]])
        return frame_copy, markers

    def __calculate_distance_angle(self,markers,frame_copy):
        info = {}
        if len(markers):
            for marker in markers:
                id,corners,side_lengths = marker

                center = [(corners[0][0] + corners[2][0]) // 2, (corners[0][1] + corners[2][1]) // 2]

                rotational_vectors, translation_vectors, _ = cv2.aruco.estimatePoseSingleMarkers([corners], self.tag_size, self.intrinsic_parameters,self.distortion_coefficients)
                frame_copy = cv2.drawFrameAxes(frame_copy, self.intrinsic_parameters, self.distortion_coefficients, rotational_vectors, translation_vectors, 0.1)
                
                distance = np.round(np.linalg.norm(translation_vectors), 3)

                rotation_matrix = np.eye(4)
                rotation_matrix[0:3, 0:3] = cv2.Rodrigues(np.array(rotational_vectors[0]))[0]
                r = Rotation.from_matrix(rotation_matrix[0:3, 0:3])
                quaternion = r.as_quat()

                transform_rotation_x = quaternion[0]
                transform_rotation_y = quaternion[1]
                transform_rotation_z = quaternion[2]
                transform_rotation_w = quaternion[3]

                roll, yaw, pitch = euler_from_quaternion([transform_rotation_x, transform_rotation_y, transform_rotation_z, transform_rotation_w])

                roll = np.round(math.degrees(roll), 3)
                yaw = np.round(math.degrees(yaw), 3)
                pitch = np.round(math.degrees(pitch), 3)

                info[id] = [distance, roll, yaw, pitch, center[0], center[1]]
        return frame_copy, info

    def get_information(self, frame):
        start = time.time()
        frame_copy, markers = self.__detect_tags(frame)
        frame_copy, info = self.__calculate_distance_angle(markers, frame_copy)
        end = time.time()
        return frame_copy, info, end - start

