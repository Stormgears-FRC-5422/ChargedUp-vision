#!/usr/bin/env python3

# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.

import json
import time
import sys
import collections
import numpy as np

from cscore import CameraServer, VideoSource, UsbCamera, MjpegServer
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

# This is an example.  instead we should instance an instance of our CV processing code
# with handles to ntinst, camera and stream out and execute the a processing method in 
# the loop below
def cv_thread(ntinst, camera, stream_out):
    print("Processing cv_thread")
    frame = np.zeros(shape=(640, 420, 3), dtype=np.uint8)
    detector = MarkerDetection()
    tag_data_struct = collections.OrderedDict()
    tag_data_struct['id'] = 1
    tag_data_struct['distance'] = -2
    tag_data_struct['roll'] = -2
    tag_data_struct['yaw'] = -2
    tag_data_struct['pitch'] = -2
    tag_data_struct['float_scale'] = 1

    ntu = storm_core.nt_util(nt_inst=ntinst,base_table="vision-data")
    ntu.publish_data_structure(type="tag_data",structure_definition=tag_data_struct)

    while True:
        _, frame = camera.grabFrame(frame)

        id_dict = detector.get_information(frame)

        id_array = []
        for ID in id_dict.keys():
            id_array.append([ID, id_dict[ID][0], id_dict[ID][1], id_dict[ID][2], id_dict[ID][3]])
            print("ID: {}, Distance: {}, Roll: {}, Yaw: {}, Pitch: {}".format(ID, id_dict[ID][0], id_dict[ID][1],
                                                                              id_dict[ID][2], id_dict[ID][3]))
        #ntu = storm_core.nt_util(nt_inst=ntinst, base_table="vision_data")
        output_frame = np.copy(frame)
        stream_out.putFrame(output_frame)


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
        print("Setting up NetworkTables client for team {}".format(team))
        ntinst.startClient4("wpilibpi")
        ntinst.setServerTeam(team)
        ntinst.startDSClient()

    # start cameras
    for config in cameraConfigs:
        cameras.append(startCamera(config))

    # start switched cameras
    for config in switchedCameraConfigs:
        startSwitchedCamera(config)

    ## start stormgears code
    c_sink = CameraServer.getVideo(name="LifeCamVision")
    c_source = CameraServer.putVideo(name="Target",width=320,height=240)
    stormvision = storm_vision.vision_thread_mgr(cv_thread,(ntinst,c_sink,c_source))
    stormvision.start()
    ## end stormgears code

    # loop forever
    while True:
        # reconnect network tables
        if False and not ntinst.isConnected():
            print("Network tables disconnected, tring to reconnect")
            ntinst.stopClient()
            ntinst.startClient4("wpilibpi")
            if not stormvision.is_alive() and ntinst.isConnected():
                stormvision.restart()

        # restart camera thread
        if not stormvision.is_alive() and ntinst.isConnected():
            stormvision.restart()

        time.sleep(5)
