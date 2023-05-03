
# using OpenCV to detect objects
# youtube video: https://www.youtube.com/watch?v=iOTWZI4RHA8
# supporting article: https://core-electronics.com.au/guides/object-identify-raspberry-pi/
# based on object-ident.py from the article above's downloadable files

import cv2

confidence_threshold = 0.50
nms_threshold = 0.1
draw = True  # True to draw bounding boxes on output image, False to output object and detection confidence only as a list

bin_path = "/home/pi/Documents/ThymPi/prod/bin/"

classPath = bin_path + "coco.names"
configPath = bin_path + "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = bin_path + "frozen_inference_graph.pb"

classNames = []
with open(classPath, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)


def getObjects(img, objects=[]):
    classIds, confs, bbox = net.detect(img, confThreshold=confidence_threshold, nmsThreshold=nms_threshold)
    # print(classIds,bbox)
    if len(objects) == 0: objects = classNames
    objectInfo = []
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append([box, className])
                if (draw):
                    cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                    cv2.putText(img, classNames[classId - 1].upper(), (box[0] + 10, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(img, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                else:
                    print("object detected: {} | confidence: {}".format(classNames[classId - 1],
                                                                        round(confidence * 100, 2)))

    return img, objectInfo


if __name__ == "__main__":

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    while True:
        success, img = cap.read()
        result, objectInfo = getObjects(img, objects=[])
        # print(objectInfo)
        if draw:
            cv2.imshow("Output", img)
            cv2.waitKey(1)
