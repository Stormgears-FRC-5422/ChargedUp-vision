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
                cv2.aruco.drawDetectedMarkers(self.camera.frame, self.native_corners, self.ids)

                if markers:
                    for marker in range(len(markers)):
                        self.corners, self.center, self.side_lengths = markers[marker][0], markers[marker][1], \
                            markers[marker][2]

                        rotational_vectors, translational_vectors, _ = \
                            cv2.aruco.estimatePoseSingleMarkers(self.native_corners[marker],
                                                                self.camera.tag_size,
                                                                self.camera.intrinsic_parameters,
                                                                self.camera.distortion_coefficients)
                        cv2.drawFrameAxes(self.camera.frame, self.camera.intrinsic_parameters,
                                          self.camera.distortion_coefficients, rotational_vectors,
                                          translational_vectors, 0.04)
                        distance = np.round(np.linalg.norm(translational_vectors) * 12 * 3.3, 3)
                        cv2.putText(self.camera.frame, ("Distance: {}".format(distance)),
                                    (self.center[0], self.center[1] + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 80),
                                    2)

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

                        roll_x = np.round(math.degrees(roll_x), 3)
                        pitch_y = np.round(math.degrees(pitch_y), 3)
                        yaw_z = np.round(math.degrees(yaw_z), 3)

                        cv2.putText(self.camera.frame, ("Roll: {}, Pitch: {}, Yaw: {}".format(roll_x, pitch_y, yaw_z)),
                                    (self.center[0], self.center[1] + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 80),
                                    2)
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
