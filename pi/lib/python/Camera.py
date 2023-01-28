import pickle
from os import path

import numpy as np

from Constants import *


class Camera:
    def __init__(self):
        self.intrinsic_parameters, self.distortion_coefficients = self.__get_calibrated_parameters()

    @staticmethod
    def __get_calibrated_parameters():
        """
        This function is used to get the calibrated parameters of the camera
        :return: intrinsic_parameters, distortion_coefficients
        """
        if path.exists(CALIBRATION_FILE):
            print("Calibration file found")
            objects = []
            with (open(CALIBRATION_FILE, "rb")) as openfile:
                while True:
                    try:
                        objects.append(pickle.load(openfile))
                    except EOFError:
                        break
            return objects[0][0], objects[0][1]
        else:
            print("Calibration file not found, using old pre-defined values")
            return np.asarray([[660.42091855, 0., 342.7709279], [0., 658.68629884, 231.84135911],
                               [0., 0., 1.]]), np.asarray(
                [[1.72827466e-01, -1.26394997e+00, -7.47066210e-03, 2.81406371e-03, 3.15535405e+00]])

    def get_camera_properties(self):
        return self.intrinsic_parameters, self.distortion_coefficients


if __name__ == '__main__':
    camera = Camera()
