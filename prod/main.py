# main ThymPi file

# general imports
import os
import time

# possibly unnecessary
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# opencv imports
import cv2

# thymio imports
import dbus
import dbus.mainloop.glib

# mpu6050 imports
from mpu6050 import mpu6050


class ThymPi:
    def __init__(self):
        # globals
        self.verbose = True
        self.compliances = {}

        # opencv globals
        self.confidence_threshold = 0.5
        self.nms_threshold = 0.2
        self.bin_path = "/home/pi/Documents/ThymPi/prod/bin"
        self.class_names = []
        self.net = None

        # thymio globals
        self.aseba_network = None
        self.currentLeftSpeed = None
        self.currentRightSpeed = None

        # mpu6050 globals
        self.sensor = None
        self.calibration_duration = 1  # mpu6050 calibration duration (seconds, default=1)
        self.test_duration = 2  # compliance test duration (seconds, default=2)
        self.frame_size = 50  # accelerometer reading frame size (default=50)

    def setupModel(self):
        if self.verbose:
            print("setting up openCV detection model")
        classFile = os.path.join(self.bin_path, "coco.names")
        configFile = os.path.join(self.bin_path, "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt")
        weightsFile = os.path.join(self.bin_path, "frozen_inference_graph.pb")

        # read class file into class_names list
        with open(classFile, "rt") as f:
            self.class_names = f.read().rstrip("\n").split("\n")

        # fill compliances dict
        for class_name in self.class_names:
            self.compliances[class_name] = None

        self.net = cv2.dnn_DetectionModel(weightsFile, configFile)
        self.net.setInputSize(120, 120)
        self.net.setInputScale(1.0 / 127.5)
        self.net.setInputMean((127.5, 127.5, 127.5))
        self.net.setInputSwapRB(True)

    def setupThymio(self):
        if self.verbose:
            print("setting up Thymio-II AsebaMedulla interface")

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        asebaNetworkObject = bus.get_object('ch.epfl.mobots.Aseba', '/')
        self.aseba_network = dbus.Interface(asebaNetworkObject, dbus_interface='ch.epfl.mobots.AsebaNetwork')
        self.aseba_network.LoadScripts(os.path.join(self.bin_path, "thympi.aesl"),
                                       reply_handler=self.dbusReply,
                                       error_handler=self.dbusError)

    def setupIMU(self):
        if self.verbose:
            print("setting up MPU6050")
        self.sensor = mpu6050(0x68)

    def dbusReply(self, reply):
        if self.verbose:
            print(reply)

    def dbusError(self, error):
        if self.verbose:
            print(error)

    def calibrateSensor(self):
        xs = []
        end = time.time() + self.calibration_duration

        while time.time() <= end:
            xs.append(self.sensor.get_accel_data()["x"])

        avg = sum(xs) / len(xs)
        error = (max(xs) - min(xs)) / 2

        if self.verbose:
            print("""calibration results: 
        average value: {}
        error range +-: {}
        data points: {}""".format(avg, error, len(xs)))

        return avg, error

    def testCompliance(self, class_name):

        # perform calibration at start (stop, wait and calibrate)
        self.setSpeed(0, 0)
        time.sleep(0.2)

        c_mean, c_error = self.calibrateSensor()
        noise_floor = round(c_error - c_mean, 2)

        self.setSpeed(500, 500)

        xs = []
        accel_events = []
        decel_events = []
        i = 0

        end = time.time() + self.test_duration

        while (time.time() <= end):
            xs.append(self.sensor.get_accel_data()["x"])
            i += 1

            # only perform calculations every time frame size is reached
            if i % self.frame_size == 0 and i > self.frame_size:
                # take average of readings in last frame and normalize with calibration average
                avg_lastx = (sum(xs[-self.frame_size:]) / len(xs[-self.frame_size:])) - c_mean

                # use calibration error to ignore noise
                if avg_lastx > noise_floor:
                    if self.verbose:
                        print("accel event: " + str(avg_lastx))
                    accel_events.append(avg_lastx)
                elif avg_lastx < (-1 * noise_floor):
                    if self.verbose:
                        print("decel event: " + str(avg_lastx))
                    decel_events.append(avg_lastx)

        self.setSpeed(0, 0)

        compliance = self.getCompliance(decel_events)
        self.compliances[class_name] = compliance

        if self.verbose:
            print("known compliances: ")
            for comp in self.compliances:
                print("class: {} | compliance: {}".format(comp, self.compliances[comp]))

    def getCompliance(self, decel_events):
        # calculate compliance from list of deceleration events
        # first decel is most important (collision event)
        # multiple deceleration events suggests object is moving but putting up resistance in movement

        compliance = 1.0

        if len(decel_events) > 0:
            for i in range(len(decel_events)):
                compliance = compliance - abs(decel_events[i] / (i + 1))
        else:
            pass

        if compliance < 0:
            compliance = 0  # cap compliance at 0

        return compliance

    def getObjects(self, img):
        classIds, confs, bbox = self.net.detect(img,
                                                confThreshold=self.confidence_threshold,
                                                nmsThreshold=self.nms_threshold
                                                )

        objects = self.class_names

        for classId in classIds:
            objects.append(self.class_names[classId - 1])

        if self.verbose:
            print(objects)

        return objects

    def setSpeed(self, left, right):
        self.aseba_network.SendEventName('motor.target', [left, right])


if __name__ == '__main__':
    # create thympi object
    thympi = ThymPi()

    # start video capture
    cap = cv2.VideoCapture(0)
    cap.set(3, 1920)
    cap.set(4, 1080)

    while True:
        # if center prox detects something
        if thympi.aseba_network.GetVariable('thymio-II', 'prox.horizontal')[2] > 0:
            objects = []

            if thympi.verbose:
                print("attempting to detect objects")

            while len(objects) == 0:
                success, img = cap.read()
                objects = thympi.getObjects(img)

            for object in objects:
                print(str(object) + " detected")

            first_object = objects[0]

            thympi.testCompliance(first_object)
