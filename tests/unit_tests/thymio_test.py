
# testing controlling Thymio with Raspberry Pi using AsebaMedulla
# based on: https://github.com/lebalz/thympi

import os
import time

import dbus
import dbus.mainloop.glib

# initialize asebamedulla in background (using terminal) and wait 0.5s to let it setup
os.system("(asebamedulla ser:name=Thymio-II &) && sleep 0.5")


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


setSpeed(0)
