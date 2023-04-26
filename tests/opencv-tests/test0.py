
# getting openCV to read from picamera
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2


# initialize camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))

# wait for camera to start
time.sleep(0.5)

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # grab the raw NumPy array representing the frame, then initialize the timestamp and occupied/unoccupied text
    image = frame.array
    
    cv2.imshow("Frame", image)
    key = cv2.waitKey(1) & 0xFF
    
    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)
    
    # break from loop on q key press
    if key == ord("q"):
        break


