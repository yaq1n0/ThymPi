# main ThymPi file

# general imports
import os
import time

# opencv imports
import cv2

# thymio imports
import dbus
import dbus.mainloop.glib

# mpu6050 imports
from mpu6050 import mpu6050

# compliance lib imports
from lib.compliance import calcCompliance


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
        self.frame_size = 50  # LEGACY: accelerometer reading frame size (default=50)

        # call setup methods
        self.setupModel()
        self.setupThymio()
        self.setupIMU()

        if self.verbose:
            print("setup complete! \n")

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
        # stop and wait
        self.setSpeed(0, 0)
        time.sleep(0.2)

        # start calibration
        xs = []
        end = time.time() + self.calibration_duration

        while time.time() <= end:
            xs.append(self.sensor.get_accel_data(g=False)["x"])

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
        c_mean, c_error = self.calibrateSensor()
        noise_floor = 2 * (c_error - c_mean)

        # start test
        self.setSpeed(self.test_speed, self.test_speed)

        xs = []
        accel_events = []
        decel_events = []

        accel_event = []
        decel_event = []

        i = 0
        prev = None

        end = time.time() + self.test_duration

        while time.time() <= end:
            x = self.sensor.get_accel_data(g=False)["x"] - c_mean
            xs.append(x)

            # NOTE: might work without this
            if i == 0:
                prev = x

            # only perform calculations every time an accel_event or decel_event finishes
            if x > noise_floor:
                if prev > noise_floor:
                    # accel -> accel
                    accel_event.append(x)

                elif prev <= -1 * noise_floor:
                    # decel -> accel
                    if len(decel_event) > 0:
                        decel_events.append(decel_event)
                        decel_event = []

            elif x <= -1 * noise_floor:
                if prev > noise_floor:
                    # accel -> decel
                    if len(accel_event) > 0:
                        accel_events.append(accel_event)
                        accel_event = []

                elif prev <= -1 * noise_floor:
                    # decel -> decel
                    decel_event.append(x)

            prev = x
            i += 1

        # go back 10 cm after test
        self.goBackCM(10)

        compliance = calcCompliance(accel_events, decel_events)
        self.compliances[class_name] = compliance

        if self.verbose:
            print("known compliances: ")
            for comp in self.compliances:
                if self.compliances[comp] != None:
                    print("class: {} | compliance: {}".format(comp, self.compliances[comp]))

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
    # create singleton instance
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
                thympi.confidence_threshold -= 0.025  # reduce confidence threshold every time nothing is detected

            for obj in objects:
                print("{} detected with {}% confidence".format(obj, objects[obj]))

            maxConfObject = max(objects, key=objects.get)

            if thympi.compliances[maxConfObject] is not None:
                print("compliance of {} is known to be {}".format(maxConfObject, thympi.compliances[maxConfObject]))
                tmp = input("do you want to retest the compliance of {}?: ".format(maxConfObject))
                if tmp == "yes" or tmp == "y":
                    thympi.testCompliance(maxConfObject)
                elif tmp == "no" or tmp == "n":
                    pass
            elif thympi.compliances[maxConfObject] is None:
                if thympi.verbose:
                    print("automatically testing compliance of {}".format(maxConfObject))
                    thympi.testCompliance(maxConfObject)
