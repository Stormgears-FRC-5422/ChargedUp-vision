import cv2
# from pi.lib.python.MarkerDetection import MarkerDetection
from MarkerDetection import MarkerDetection
# from pi.lib.python.DetectFieldElement import DetectFieldElement

stream = cv2.VideoCapture(0)
stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
stream.set(cv2.CAP_PROP_BRIGHTNESS, 100)

# detector = DetectFieldElement()
detector = MarkerDetection()

while True:
    _, image = stream.read()
    frame_copy, output = detector.get_information(image)

    # cv2.imshow('image', output["frame"])
    cv2.imshow('Image', frame_copy)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
