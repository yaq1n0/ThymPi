# combining imu_test and thymio_test

from mpu6050 import mpu6050

import os
import dbus
import dbus.mainloop.glib
import time
import numpy as np
import matplotlib.pyplot as plt

sensor = mpu6050(0x68)

t, x, y, z = [], [], [], []


def dbusReply():
    pass


def dbusError():
    pass


# init the dbus main loop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

# get stub of the aseba network
bus = dbus.SessionBus()
asebaNetworkObject = bus.get_object('ch.epfl.mobots.Aseba', '/')

# prepare interface
asebaNetwork = dbus.Interface(asebaNetworkObject, dbus_interface='ch.epfl.mobots.AsebaNetwork')

# load the file which is run on the thymio
asebaNetwork.LoadScripts('thympi.aesl', reply_handler=dbusReply, error_handler=dbusError)


def setSpeed(speed):
    left_wheel = speed
    right_wheel = speed
    asebaNetwork.SendEventName(
        'motor.target',
        [left_wheel, right_wheel]
    )


print("starting test")
start_time = time.time()
end_time = time.time() + 5

setSpeed(300)

while time.time() <= end_time:
    acc_data = sensor.get_accel_data()
    # returns acc_data in dict form ("x", "y", "z")

    t.append(time.time())
    x.append(acc_data["x"])
    y.append(acc_data["y"])
    z.append(acc_data["z"])

setSpeed(0)

print("ended test")

print("starting plot")
plt.plot(t, x)
plt.plot(t, y)
plt.plot(t, z)

plt.show()

print("finishing plot")
