# Getting compliance of object autonomously

import time

def testCompliance(object_class, aseba_network):
    # take object class (string) and it along with compliance value (float) between 0 (low deceleration) and 1.0 (
    # high deceleration)

    setSpeed(aseba_network, 500, 500)

    time.sleep(2)

    setSpeed(aseba_network, 0, 0)


def setupIMU():
    pass

def setupThymio(os_setup):
    if os_setup:
        # OPTIONAL: setup asebemedulla
        from os import system as os_system
        os_system("(asebamedulla ser:name=Thymio-II &) && sleep 0.5")

    # set up thymio dbus
    import dbus

    # init the dbus main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # get stub of the aseba network
    bus = dbus.SessionBus()
    asebaNetworkObject = bus.get_object('ch.epfl.mobots.Aseba', '/')

    # prepare interface
    asebaNetwork = dbus.Interface(asebaNetworkObject, dbus_interface='ch.epfl.mobots.AsebaNetwork')

    # load the file which is run on the thymio
    asebaNetwork.LoadScripts('bin/thympi.aesl', reply_handler=dbusReply, error_handler=dbusError)

    return asebaNetwork

def dbusReply(reply):
    print(reply)


def dbusError(error):
    print(error)


def setSpeed(net, left, right):
    net.SendEventName(
        'motor.target',
        [left, right]
        )

if __name__ == '__main__':
    # setup asebamedulla and thymio dbus
    aseba_network = setupThymio(True)

    # setup MPU6050 IMU
    setupIMU()

    testCompliance(aseba_network)

