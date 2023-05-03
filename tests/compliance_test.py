# library with compliance testing functions and automated compliance testing script

import time
import os
import dbus
import dbus.mainloop.glib
from mpu6050 import mpu6050

frame_size = 50  # number of readings per frame, 50 seems to work for most cases


def calibrate(sensor, seconds, verbose):
    xs = []

    start = time.time()
    end = time.time() + seconds

    while time.time() <= end: xs.append(sensor.get_accel_data()["x"])

    avg = sum(xs) / len(xs)
    error = (max(xs) - min(xs)) / 2

    if verbose:
        print("""calibration results: 
average value: {}
error range +-: {}
data points: {}""".format(avg, error, len(xs)))

    return avg, error


def read_test(sensor, seconds, frame_size, verbose):
    # read sensor values and analyse them as frames
    # seconds to run loop
    # verbose to print to console, noverbose for return 

    xs = []
    i = 0

    # perform calibration at start
    c_mean, c_error = calibrate(sensor, 1, verbose)
    noise_floor = round(c_error - c_mean, 2)

    start = time.time()
    end = start + seconds

    while (time.time() <= end):
        xs.append(sensor.get_accel_data()["x"])
        i += 1

        # only perform calculations every time frame size is reached
        if i % frame_size == 0 and i > frame_size:
            # take average of readings in last frame and normalize with calibration average
            avg_lastx = (sum(xs[-frame_size:]) / len(xs[-frame_size:])) - c_mean

            # use calibrated error to ignore noise
            if avg_lastx > noise_floor:
                print("accel event: " + str(avg_lastx))
            elif avg_lastx < (-1 * noise_floor):
                print("decel event: " + str(avg_lastx))


def compliance_test(object_class, sensor, aseba_network, verbose):
    # around -1g for complete stop
    # TODO: start from ~10cm out (can be changed)
    # return first collision decel

    # perform calibration at start
    c_mean, c_error = calibrate(sensor, 1, verbose)
    noise_floor = round(c_error - c_mean, 2)

    asebaNetwork.SendEventName('motor.target', [500, 500])

    xs = []
    accel_events = []
    decel_events = []
    i = 0

    start = time.time()
    end = start + 2

    while (time.time() <= end):
        xs.append(sensor.get_accel_data()["x"])
        i += 1

        # only perform calculations every time frame size is reached
        if i % frame_size == 0 and i > frame_size:
            # take average of readings in last frame and normalize with calibration average
            avg_lastx = (sum(xs[-frame_size:]) / len(xs[-frame_size:])) - c_mean

            # use calibrated error to ignore noise
            if avg_lastx > noise_floor:
                if verbose: print("accel event: " + str(avg_lastx))
                accel_events.append(avg_lastx)
            elif avg_lastx < (-1 * noise_floor):
                if verbose: print("decel event: " + str(avg_lastx))
                decel_events.append(avg_lastx)

    asebaNetwork.SendEventName('motor.target', [0, 0])

    # defining compliance
    # first decel is most important (collision event)
    # multiple deceleration events suggests object is moving but putting up resistance in movement

    def getCompliance(decel_events):
        # calculate compliance from deceleration events
        compliance = 1.0

        if len(decel_events) == 0:
            # no deceleration detected, assume full compliance, pass
            pass
        else:
            for i in range(len(decel_events)):
                compliance = compliance - abs(decel_events[i] / (i + 1))
        if compliance < 0: compliance = 0  # cap compliance at 0

        return compliance

    compliance = getCompliance(decel_events)

    if verbose:
        print("""decels: {}\ncompliance: {}""".format(decel_events, compliance))

    return compliance


def dbusReply(reply):
    return reply


def dbusError(error):
    return error


if __name__ == "__main__":
    # test module
    sensor = mpu6050(0x68)

    # thymio setup
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    asebaNetworkObject = bus.get_object('ch.epfl.mobots.Aseba', '/')
    asebaNetwork = dbus.Interface(asebaNetworkObject, dbus_interface='ch.epfl.mobots.AsebaNetwork')
    asebaNetwork.LoadScripts('bin/thympi.aesl', reply_handler=dbusReply, error_handler=dbusError)

    # calibrate(sensor, 1, True)
    # read_test(sensor, 120, frame_size, True)
    print(compliance_test("placeholder", sensor, asebaNetwork, True))
