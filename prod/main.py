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
        self.test_speed = 500  # compliance test speed (default=500)
        self.frame_size = 50  # accelerometer reading frame size (default=50)

        # call setup methods
        self.setupModel()
        self.setupThymio()
        self.setupIMU()

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
        self.net.setInputSize(320, 320)
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

    def testComplianceFrameBased(self, class_name):
        # perform calibration at start (stop, wait and calibrate)
        self.setSpeed(0, 0)
        time.sleep(0.2)

        c_mean, c_error = self.calibrateSensor()
        noise_floor = round(c_error - c_mean, 2)

        self.setSpeed(self.test_speed, self.test_speed)

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

        self.goBackCM(10)

        compliance = self.getCompliance(decel_events)
        self.compliances[class_name] = compliance

        if self.verbose:
            print("known compliances: ")
            for comp in self.compliances:
                if self.compliances[comp] != None:
                    print("class: {} | compliance: {}".format(comp, self.compliances[comp]))

    def testCompliance(self, class_name):
        # perform calibration at start (stop, wait and calibrate)
        self.setSpeed(0, 0)
        time.sleep(0.2)

        c_mean, c_error = self.calibrateSensor()
        noise_floor = round(c_error - c_mean, 2)

        self.setSpeed(self.test_speed, self.test_speed)

        xs = []
        accel_event = []
        decel_event = []

        accel_events = []
        decel_events = []
        i = 0
        prev = 0

        end = time.time() + self.test_duration

        while (time.time() <= end):
            i += 1
            x = self.sensor.get_accel_data()["x"] - c_mean
            xs.append(x)

            # only perform calculations every time an accel_event or decel_event occurs\
            if x > noise_floor:
                if prev > 0:
                    # accel -> accel
                    accel_event.append(x)
                elif prev <= 0:
                    # decel -> accel
                    decel_events.append(sum(decel_event) / len(decel_event))
                    if self.verbose:
                        print("end decel event: " + str(decel_events[-1]))

            elif x < -1 * noise_floor:
                if prev > 0:
                    # accel -> decel
                    accel_events.append(sum(accel_event) / len(accel_event))
                    if self.verbose:
                        print("end accel event: " + str(accel_events[-1]))
                elif prev <= 0:
                    # decel -> decel
                    decel_event.append(x)

            prev = x

        self.goBackCM(10)

        compliance = self.getCompliance(decel_events)
        self.compliances[class_name] = compliance

        if self.verbose:
            print("known compliances: ")
            for comp in self.compliances:
                if self.compliances[comp] != None:
                    print("class: {} | compliance: {}".format(comp, self.compliances[comp]))

    def getCompliance(self, decel_events):
        # calculate compliance from list of deceleration events
        # first decel is most important (collision event)
        # multiple deceleration events suggests object is moving but putting up resistance in movement
        # at 500 testing_speed, full non compliance is around -1g

        compliance = 1.0

        if len(decel_events) > 0:
            for i in range(len(decel_events)):
                scaling = 500 / self.test_speed
                compliance = compliance - (scaling * abs(decel_events[i] / (i + 1)))
        else:
            pass

        if compliance < 0:
            compliance = 0  # cap compliance at 0

        return round(compliance, 2)

    def getObjects(self, img):
        classIds, confs, bbox = self.net.detect(img,
                                                confThreshold=self.confidence_threshold,
                                                nmsThreshold=self.nms_threshold
                                                )

        objects = {}

        if len(classIds) > 0:
            obj_names = []
            obj_confidences = []

            for classId in classIds:
                obj_names.append(self.class_names[classId - 1])

            for conf in confs:
                obj_confidences.append(round(conf * 100, 0))

            objects = dict(zip(obj_names, obj_confidences))

            if self.verbose:
                print(objects)

        return objects

    def setSpeed(self, left, right):
        self.aseba_network.SendEventName('motor.target', [left, right])

    def goBackCM(self, distance_cm, speed=250):
        # go back x centimeters
        # 500 motor speed is roughly ~20cm/s
        # default speed=250 (~10cm/s)

        duration = round(distance_cm / (speed / 25), 0)
        thympi.setSpeed(-1 * speed, -1 * speed)
        time.sleep(duration)
        thympi.setSpeed(0, 0)


if __name__ == '__main__':
    # create thympi object
    thympi = ThymPi()

    # start video capture
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    while True:
        if thympi.aseba_network.GetVariable('thymio-II', 'prox.horizontal')[2] > 0:
            # if center prox detects something, (detection distance ~ 10cm)
            if thympi.verbose:
                print("object in proximity!")

            objects = []

            # go back 10cm (20cm tends to detect most objects)
            thympi.goBackCM(10)

            thympi.confidence_threshold = 0.5
            while len(objects) == 0:
                if thympi.verbose:
                    print("attempting to detect objects")
                success, img = cap.read()
                objects = thympi.getObjects(img)
                thympi.confidence_threshold -= 0.025

            for object in objects:
                print("{} detected with {}% confidence".format(object, objects[object]))

            maxConfObject = max(objects, key=objects.get)

            if thympi.compliances[maxConfObject] != None:
                print("compliance of {} is known to be {}".format(maxConfObject, thympi.compliances[maxConfObject]))
                tmp = input("do you want to retest the compliance of {}?: ".format(maxConfObject))
                if tmp == "yes" or tmp == "y":
                    thympi.testCompliance(maxConfObject)
                elif tmp == "no" or tmp == "n":
                    pass
            elif thympi.compliances[maxConfObject] == None:
                if thympi.verbose:
                    print("automatically testing compliance of {}".format(maxConfObject))
                    thympi.testCompliance(maxConfObject)
