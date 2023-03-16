import cv2

from pi.lib.python.MarkerDetection import MarkerDetection

stream = cv2.VideoCapture(0)
stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

detector = MarkerDetection()

while True:
    ret, frame = stream.read()

    id_dict = detector.get_information(frame)

    for ID in id_dict.keys():
        print("ID: {}, Distance: {}, Roll: {}, Yaw: {}, Pitch: {}".format(ID, id_dict[ID][0], id_dict[ID][1],
                                                                          id_dict[ID][2], id_dict[ID][3]))

    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
