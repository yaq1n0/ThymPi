
# testing picamera module
# picamera documentation: https://picamera.readthedocs.io/en/release-1.13/install.html

from picamera import PiCamera
from time import sleep

camera = PiCamera()

camera.start_preview()

sleep(10)