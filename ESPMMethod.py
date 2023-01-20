import math

import cv2
import numpy as np
from scipy.spatial.transform import Rotation
from transformations import euler_from_quaternion

from Camera import Camera


class ESPMMethod:

    def __init__(self):
        self.frame = None
        self.ids = None
        self.corners, self.native_corners = None, None
        self.center = None
        self.side_lengths = None
        self.pause = 0

        self.camera = Camera()
        self.display()

    def display(self):
        while True:
            key = cv2.waitKey(1) & 0xFF
            if not self.pause:
                self.ids, markers, self.native_corners = self.camera.detect_tags()
                if markers:
                    for marker in markers:
                        self.corners, self.center, self.side_lengths = marker[0], marker[1], marker[2]

                        cv2.aruco.drawDetectedMarkers(self.camera.frame, self.native_corners, self.ids)

                        # cv2.line(self.camera.frame, self.corners[0], self.corners[1], (0, 255, 0), 2)
                        # cv2.line(self.camera.frame, self.corners[1], self.corners[2], (0, 255, 0), 2)
                        # cv2.line(self.camera.frame, self.corners[2], self.corners[3], (0, 255, 0), 2)
                        # cv2.line(self.camera.frame, self.corners[3], self.corners[0], (0, 255, 0), 2)

                        rotational_vectors, translational_vectors, _ = \
                            cv2.aruco.estimatePoseSingleMarkers(self.native_corners,
                                                                self.camera.tag_size,
                                                                np.asarray(self.camera.intrinsic_parameters),
                                                                np.asarray(self.camera.distortion_coefficients))
                        distance = np.round(np.linalg.norm(translational_vectors), 3) * 12 * 3.3
                        cv2.putText(self.camera.frame, ("Distance: {}".format(distance)),
                                    (100, self.corners[0][1] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 80), 2)

                        rotation_matrix = np.eye(4)
                        rotation_matrix[0:3, 0:3] = cv2.Rodrigues(np.array(rotational_vectors[0]))[0]
                        r = Rotation.from_matrix(rotation_matrix[0:3, 0:3])
                        quaternion = r.as_quat()

                        transform_rotation_x = quaternion[0]
                        transform_rotation_y = quaternion[1]
                        transform_rotation_z = quaternion[2]
                        transform_rotation_w = quaternion[3]

                        roll_x, yaw_z, pitch_y = euler_from_quaternion([transform_rotation_x, transform_rotation_y,
                                                                        transform_rotation_z, transform_rotation_w])

                        roll_x = math.degrees(roll_x)
                        pitch_y = math.degrees(pitch_y)
                        yaw_z = math.degrees(yaw_z)
                        print("Roll: {}, Pitch: {}, Yaw: {}".format(roll_x, pitch_y, yaw_z))

            cv2.imshow("Frame", self.camera.frame)

            if key == ord('q'):
                break
            elif key == ord('p'):
                if self.pause is True:
                    self.pause = False
                else:
                    self.pause = True


if __name__ == '__main__':
    ESPMMethod()
