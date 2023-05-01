
# live control of Thymio using terminal
# pygame example: https://www.edureka.co/blog/snake-game-with-pygame/
# pygame keys: https://www.pygame.org/docs/ref/key.html

import pygame
import os
import dbus
import dbus.mainloop.glib


# defining speed class (data type)
class ThymSpeed:
    def __init__(self, left, right):
        self.left = left
        self.right = right

# creating singleton global currentSpeed ThymSpeed instance
currentSpeed = ThymSpeed(0,0)
    
# defining handlers for dbus 
def dbusReply(reply):
    print(reply)
    pass

def dbusError(error):
    print(error)
    pass

# initialize the dbus main loop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

# get stub of the aseba network
bus = dbus.SessionBus()
asebaNetworkObject = bus.get_object('ch.epfl.mobots.Aseba', '/')

# prepare interface
asebaNetwork = dbus.Interface(asebaNetworkObject, dbus_interface='ch.epfl.mobots.AsebaNetwork')

# load the file which is run on the thymio
asebaNetwork.LoadScripts('bin/thympi.aesl',reply_handler=dbusReply,error_handler=dbusError)


# set left and right motor speed to value between -500 and 500
def setSpeed(left, right):
    currentSpeed.left = left
    currentSpeed.right = right

    asebaNetwork.SendEventName(
        'motor.target',
        [currentSpeed.left, currentSpeed.right]
        )
    
# set left and right motor speed to value between -500 and 500
def modSpeed(left, right):
    currentSpeed.left += left
    currentSpeed.right += right
    
    # setting bounds
    if currentSpeed.left > 500:
        currentSpeed.left = 500
    if currentSpeed.right > 500:
        currentSpeed.right = 500
    if currentSpeed.left < -500:
        currentSpeed.left = -500
    if currentSpeed.right < -500:
        currentSpeed.right = -500
    
    asebaNetwork.SendEventName(
        'motor.target',
        [currentSpeed.left, currentSpeed.right]
        )


# setting up pygame 
pygame.init()
dis = pygame.display.set_mode((400, 300))
pygame.display.update()
pygame.display.set_caption("Live Thymio Control Test")
test_over = False


while not test_over:
    #print(asebaNetwork.GetVariable('thymio-II', 'prox.horizontal')[2])
    for event in pygame.event.get():
        # print(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                setSpeed(0,0)
                test_over = True
            elif event.key == pygame.K_SPACE:
                print("stop")
                setSpeed(0,0)
            elif event.key == pygame.K_w:
                print("forward")
                setSpeed(500,500)
            elif event.key == pygame.K_a:
                print("left")
                #modSpeed(-100,100)
            elif event.key == pygame.K_s:
                print("backward")
                setSpeed(-100,-100)
            elif event.key == pygame.K_d:
                print("right")
                #modSpeed(100,-100)

            
pygame.quit()
quit()
