import cv2
# from pi.lib.python.MarkerDetection import MarkerDetection
# from MarkerDetection import MarkerDetection
from pi.lib.python.DetectFieldElementRetro import DetectFieldElement
# from pi.lib.python.DetectFieldElement import DetectFieldElement

stream = cv2.VideoCapture(2)
stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
stream.set(cv2.CAP_PROP_BRIGHTNESS, 1)

detector = DetectFieldElement()
# detector = MarkerDetection()

while True:
    _, image = stream.read()
    # frame_copy, output = detector.get_information(image)
    output = detector.detect(image, "retro")
    print(f"Retro: {output['retro']}")
    print(f"Cubes: {output['cubes']}")
    print(f"Cones: {output['cones']}")
    print(f"Time: {output['speed']}")
    cv2.imshow('image', output["frame"])
    # cv2.imshow('Image', frame_copy)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
