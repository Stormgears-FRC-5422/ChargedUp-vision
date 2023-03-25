#!/usr/bin/env python3

# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.

import json
import time
import sys
import collections
import numpy as np
import os
import cv2
import time


from cscore import CameraServer, VideoSource, UsbCamera, MjpegServer, CvSink, CvSource, VideoSink, VideoMode
from ntcore import NetworkTableInstance, EventFlags

# Make sure our python libraries are in the path
sys.path.insert(0,"/home/pi/lib/python")
import storm_core
import storm_vision
from MarkerDetection import MarkerDetection



#   JSON format:
#   {
#       "team": <team number>,
#       "ntmode": <"client" or "server", "client" if unspecified>
#       "cameras": [
#           {
#               "name": <camera name>
#               "path": <path, e.g. "/dev/video0">
#               "pixel format": <"MJPEG", "YUYV", etc>   // optional
#               "width": <video mode width>              // optional
#               "height": <video mode height>            // optional
#               "fps": <video mode fps>                  // optional
#               "brightness": <percentage brightness>    // optional
#               "white balance": <"auto", "hold", value> // optional
#               "exposure": <"auto", "hold", value>      // optional
#               "properties": [                          // optional
#                   {
#                       "name": <property name>
#                       "value": <property value>
#                   }
#               ],
#               "stream": {                              // optional
#                   "properties": [
#                       {
#                           "name": <stream property name>
#                           "value": <stream property value>
#                       }
#                   ]
#               }
#           }
#       ]
#       "switched cameras": [
#           {
#               "name": <virtual camera name>
#               "key": <network table key used for selection>
#               // if NT value is a string, it's treated as a name
#               // if NT value is a double, it's treated as an integer index
#           }
#       ]
#   }

# Modified to point to local frc.json instead of /boot/version
configFile = "etc/frc.json"

class CameraConfig: pass

team = None
server = False
cameraConfigs = []
switchedCameraConfigs = []
cameras = []

def parseError(str):
    """Report parse error."""
    print("config error in '" + configFile + "': " + str, file=sys.stderr)

def readCameraConfig(config):
    """Read single camera configuration."""
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read camera name")
        return False

    # path
    try:
        cam.path = config["path"]
    except KeyError:
        parseError("camera '{}': could not read path".format(cam.name))
        return False

    # stream properties
    cam.streamConfig = config.get("stream")

    cam.config = config

    cameraConfigs.append(cam)
    return True

def readSwitchedCameraConfig(config):
    """Read single switched camera configuration."""
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read switched camera name")
        return False

    # path
    try:
        cam.key = config["key"]
    except KeyError:
        parseError("switched camera '{}': could not read key".format(cam.name))
        return False

    switchedCameraConfigs.append(cam)
    return True

def readConfig():
    """Read configuration file."""
    global team
    global server

    # parse file
    try:
        with open(configFile, "rt", encoding="utf-8") as f:
            j = json.load(f)
    except OSError as err:
        print("could not open '{}': {}".format(configFile, err), file=sys.stderr)
        return False

    # top level must be an object
    if not isinstance(j, dict):
        parseError("must be JSON object")
        return False

    # team number
    try:
        team = j["team"]
    except KeyError:
        parseError("could not read team number")
        return False

    # ntmode (optional)
    if "ntmode" in j:
        str = j["ntmode"]
        if str.lower() == "client":
            server = False
        elif str.lower() == "server":
            server = True
        else:
            parseError("could not understand ntmode value '{}'".format(str))

    # cameras
    try:
        cameras = j["cameras"]
    except KeyError:
        parseError("could not read cameras")
        return False
    for camera in cameras:
        if not readCameraConfig(camera):
            return False

    # switched cameras
    if "switched cameras" in j:
        for camera in j["switched cameras"]:
            if not readSwitchedCameraConfig(camera):
                return False

    return True

def startCamera(config):
    """Start running the camera."""
    print("Starting camera '{}' on {}".format(config.name, config.path))
    camera = UsbCamera(config.name, config.path)
    server = CameraServer.startAutomaticCapture(camera=camera)

    camera.setConfigJson(json.dumps(config.config))
    camera.setConnectionStrategy(VideoSource.ConnectionStrategy.kConnectionKeepOpen)

    if config.streamConfig is not None:
        server.setConfigJson(json.dumps(config.streamConfig))

    return camera

def startSwitchedCamera(config):
    """Start running the switched camera."""
    print("Starting switched camera '{}' on {}".format(config.name, config.key))
    server = CameraServer.addSwitchedCamera(config.name)

    def listener(event):
        data = event.data
        if data is not None:
            value = data.value.value()
            if isinstance(value, int):
                if value >= 0 and value < len(cameras):
                    server.setSource(cameras[value])
            elif isinstance(value, float):
                i = int(value)
                if i >= 0 and i < len(cameras):
                    server.setSource(cameras[i])
            elif isinstance(value, str):
                for i in range(len(cameraConfigs)):
                    if value == cameraConfigs[i].name:
                        server.setSource(cameras[i])
                        break

    NetworkTableInstance.getDefault().addListener(
        NetworkTableInstance.getDefault().getEntry(config.key),
        EventFlags.kImmediate | EventFlags.kValueAll,
        listener)

    return server

def nt_connect():
    ntinst = NetworkTableInstance.getDefault()

    while not ntinst.isConnected():
        ntinst.stopClient()
        if os.system("ifconfig eth0 | grep 192.168.200") == 0:
            print("Connecting to non-robot server")
            ntinst.setServer("192.168.200.106", NetworkTableInstance.kDefaultPort4)
        else:
            print("Setting up NetworkTables client for team {}".format(team))
            ntinst.setServerTeam(team)
        ntinst.startClient4("wpilibpi")
        print(f"NetworkTables: connected = {ntinst.isConnected()}")
        time.sleep(1)
    connections = ntinst.getConnections()
    print(f"Connected to Network Tables {connections[0]}")


# FIXME - we should really move this function to its own module
def process_april_tag(frame,frame_count,detector):
    height = frame.shape[0]
    width = frame.shape[1]

    id_dict = detector.get_information(frame)
    tag_list = []
    for ID in id_dict.keys():
        tag_data = {}
        tag_data['id'] = int(ID)
        tag_data['distance'] = id_dict[ID][0]
        tag_data['roll'] = id_dict[ID][1]
        tag_data['yaw'] = id_dict[ID][2]
        tag_data['pitch'] = id_dict[ID][3]
        tag_data['leftright'] = (58.74/width) * (id_dict[ID][4] - (width/2))
        tag_data['updown'] = (35.2/height) * ((height/2) - id_dict[ID][5])

        tag_list.append(tag_data)
    return tag_list


# FIXME - we should really move this function to its own module
def process_objects(frame,frame_count):
    if frame_count % 20 == 0:
        print("I can't process objects yet")
    return None


# This is an example.  instead we should instance an instance of our CV processing code
# with handles to ntinst, camera and stream out and execute the a processing method in 
# the loop below
def cv_thread(ntinst, camera, stream_out):
    print("Processing cv_thread")
    frame = np.zeros(shape=(640, 420, 3), dtype=np.uint8)
    detector = MarkerDetection()

    detection_mode = 0   # 0 = AprilTag, 1 = Cube/Cone

    ntu = storm_core.nt_util(nt_inst=ntinst,base_table="vision-data")

    tag_data_struct = collections.OrderedDict()
    tag_data_struct['id'] = ntu.encode_encoding_field(num_bytes=1,precision=0)
    tag_data_struct['distance'] = ntu.encode_encoding_field(num_bytes=2,precision=2,signed=True)
    tag_data_struct['roll'] = ntu.encode_encoding_field(num_bytes=2,precision=1,signed=True)
    tag_data_struct['yaw'] = ntu.encode_encoding_field(num_bytes=2,precision=1,signed=True)
    tag_data_struct['pitch'] = ntu.encode_encoding_field(num_bytes=2,precision=1,signed=True)
    tag_data_struct['leftright'] = ntu.encode_encoding_field(num_bytes=2,precision=1,signed=True)
    tag_data_struct['updown'] = ntu.encode_encoding_field(num_bytes=2,precision=1,signed=True)
    tag_data_struct['process_time'] = ntu.encode_encoding_field(num_bytes=2,precision=0,signed=False)
    tag_data_struct['frame_id'] = ntu.encode_encoding_field(num_bytes=2,precision=0,signed=False)


    ntu.publish_data_structure(type="tag_data",structure_definition=tag_data_struct)
    # 68.5 diagonal
    # 
    # 1200x800
    # 
    # sqrt(1200^2 + 800^2) = 1442.22
    # Horiz = 68.5*1200/1442.22 = 57
    # Vert  = 68.5*800/1442.22 = 38.5
    # 
    # sqrt(1200^2 + 720^2) = 1399.43
    # Horiz = 68.5*1200/1399.43 = 58.74
    # Vert  = 68.5*720/1399.43 = 35.2

    # setup mode subscriber
    table = ntinst.getTable("vision_data")
    mode_sub = table.getIntegerTopic("vision_mode").subscribe(-1)

    frame_count = 0

    while True:
        start = time.perf_counter()

        next_detection_mode = mode_sub.get(0)
        if next_detection_mode != detection_mode:
            print(f"Changing vision mode to {next_detection_mode}")
            detection_mode = next_detection_mode

        _, frame = camera.grabFrame(frame)
        if detection_mode == 0:
            tag_list = process_april_tag(frame,frame_count,detector)
            end = time.perf_counter()
            delta_ms = (start - end) * 1000;
            for tag in tag_list:
                tag['process_time'] = delta_ms
                tag['frame_id'] = frame_count
                if frame_count % 20 == 0:
                    print("ID: {}, frame: {} , Process_time: {}, Distance: {}, Roll: {}, Yaw: {}, Pitch: {} X: {:.1f}, Y:{:.1f}".format(tag['id'], tag['frame_id'],tag['distance'],tag['process_time'],tag['roll'],tag['yaw'],tag['pitch'],tag['leftright'],tag['updown']))



            ntu.publish_data("april_tag","tag_data",tag_list)
            output_frame = cv2.resize(np.copy(frame), (320, 240))
            stream_out.putFrame(output_frame)
        elif detection_mode == 1:
            new_frame = process_objects(frame,frame_count)
            output_frame = cv2.resize(np.copy(new_frame), (320, 240))
            stream_out.putFrame(output_frame)

        frame_count += 1


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        configFile = sys.argv[1]

    # read configuration
    if not readConfig():
        sys.exit(1)

    # start NetworkTables
    ntinst = NetworkTableInstance.getDefault()
    if server:
        print("Setting up NetworkTables server")
        ntinst.startServer()
    else:
        nt_connect()

    # start cameras
    for config in cameraConfigs:
        cam = startCamera(config)
        cameras.append(cam)

    # start switched cameras
    for config in switchedCameraConfigs:
        startSwitchedCamera(config)

    ## start stormgears code
    c_sink = CameraServer.getVideo(name="LifeCamVision")
    c_source = CameraServer.putVideo(name="DriverCam",width=320,height=240)
#    c_source = CvSource("DriverCam",VideoMode(VideoMode.PixelFormat.kMJPEG, 320,240,15))
#    mjpegServer = CameraServer.addSserver("Drive Cam")
#    mjpegServer.setSource(c_source)

    stormvision = storm_vision.vision_thread_mgr(cv_thread,(ntinst,c_sink,c_source))
    stormvision.start()
    ## end stormgears code

    # loop forever
    while True:
        # reconnect network tables
        if not ntinst.isConnected():
            print("Network tables disconnected, trying to reconnect")
            nt_connect()
            if not stormvision.is_alive() and ntinst.isConnected():
                stormvision.restart()

        # restart camera thread
        if not stormvision.is_alive() and ntinst.isConnected():
            stormvision.restart()

        time.sleep(5)
