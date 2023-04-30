# combine live openCV with live MPU and live Thymio
#

import pygame
import os
import dbus
import dbus.mainloop.glib

from mpu6050 import mpu6050

import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import cv2


class Thympi:

    def __init__(self):
        # confidence threshold for model (default = 0.5) to remove low confidence detections
        self.conf_threshold = 0.5

        # nms threshold for model (default = 0.2) to remove duplicate detections
        self.nms_threshold = 0.2

        # default absolute path to folder that detection model files
        self.bin_path = "/home/pi/Documents/ThymPi/bin"

        # empty class names
        self.classNames = []

        # initialize net variable
        self.net = None

        # initialize sensor variable
        self.sensor = None

        self.bus = None
        self.asebaNetworkObject = None
        self.asebaNetwork = None
        self.currentLeftSpeed = None
        self.currentRightSpeed = None


    def setupModel(self):
        # set up the detection model with files from self.bin_path
        classFile = os.path.join(self.bin_path, "coco.names")
        configFile = os.path.join(self.bin_path, "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt")
        weightsFile = os.path.join(self.bin_path, "frozen_inference_graph.pb")

        with open(classFile, "rt") as f:
            self.classNames = f.read().rstrip("\n").split("\n")

        self.net = cv2.dnn_DetectionModel(weightsFile, configFile)
        self.net.setInputSize(120, 120)
        self.net.setInputScale(1.0 / 127.5)
        self.net.setInputMean((127.5, 127.5, 127.5))
        self.net.setInputSwapRB(True)

    def setupIMU(self):
        # set up IMU
        self.sensor = mpu6050(0x68)

    def setupThymio(self):
        # initialize the dbus main loop
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        # get stub of the aseba network
        self.bus = dbus.SessionBus()
        self.asebaNetworkObject = self.bus.get_object('ch.epfl.mobots.Aseba', '/')

        # prepare interface
        self.asebaNetwork = dbus.Interface(asebaNetworkObject, dbus_interface='ch.epfl.mobots.AsebaNetwork')

        self.asebaNetwork.LoadScripts(os.path.join(self.bin_path, "thympi.aesl"), reply_handler=self.dbusReply, error_handler=dbusError)

        self.setSpeed(0, 0)

    def dbusReply(self):
        pass

    def dbusError(self):
        pass

    def setSpeed(self, left, right):
        self.currentLeftSpeed = left
        self.currentRightSpeed = right
        self.asebaNetwork.SendEventName('motor.target', [self.currentLeftSpeed, self.currentRightSpeed])
        
    def modSpeed(self, left, right):
        self.currentLeftSpeed += left
        self.currentRightSpeed += right

        # setting bounds
        if self.currentLeftSpeed > 500:
            self.currentLeftSpeed = 500
        if self.currentRightSpeed > 500:
            self.currentRightSpeed = 500
        if self.currentLeftSpeed < -500:
            self.currentLeftSpeed = -500
        if self.currentRightSpeed < -500:
            self.currentRightSpeed = -500
            
        self.asebaNetwork.SendEventName('motor.target', [self.currentLeftSpeed, self.currentRightSpeed])
        
    def getObjects(self, img, draw=True, objects=[]):
        classIds, confs, bbox = self.net.detect(img, confThreshold=self.conf_threshold, nmsThreshold=self.nms_threshold)
        # print(classIds,confs,bbox)

        if len(objects) == 0:
            objects = self.classNames

        objectInfo = []

        if len(classIds) != 0:
            for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
                className = self.classNames[classId - 1]
                if className in objects:
                    objectInfo.append([box, className])
                    if draw:
                        # draw bounding rectangles and put text on image
                        cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                        cv2.putText(img, self.classNames[classId - 1].upper(), (box[0] + 10, box[1] + 30),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(img, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                        # TODO: put code to draw compliance value and confidence value here
                    else:
                        # TODO: return detected classNames in console somehow
                        print(objectInfo)

        return img, objectInfo

    def setConfidenceThreshold(self, thres):
        self.conf_threshold = thres

    def setNMSThreshold(self, thres):
        self.nms_threshold = thres

    def setBinPath(self, path):
        self.bin_path = path

    def testObject(self):
        # TODO: test specific object class for compliance
        # extract compliance value between 0-1.0 from collision data and save it to lookup table, increment test count


if __name__ == '__main__':
    # run when file executed

    # initialize asebamedulla in background (using terminal) and wait 0.5s to let it setup
    os.system("(asebamedulla ser:name=Thymio-II &) && sleep 0.5")

    print("ThymPi Started")
    thympi = Thympi()
    thympi.setupModel()
    thympi.setupIMU()
    thympi.setupThymio()

    #TODO: mainloop here??

    # SDA LOOP

    # SENSE
    # read IMU data, assign to timestamp, add to log
    # read camera, assign to timestamp, add to log?
    # read key event

    # output any collision events
    # output any detected objects
    # option to start automated test

    # test output




