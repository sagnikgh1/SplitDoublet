import sys
import ctypes
import cv2
import msvcrt
import dcampy

import numpy as np

print("S420_SEQUENCE START")

framestocapture = 200
seqframes = 10

totalcams = dcampy.init()
if(totalcams <= 0):
	print("No Cameras Found")
	exit()

cam = dcampy.Camera()
if cam.open(0) == False:
	print("open FAILED")
	exit()

print(str(cam))
print("Model   =", cam.getCameraModel())
print("Serial  =", cam.getCameraSerial())
print("Version =", cam.getCameraVersion())

if cam.preparecapture(-1, seqframes) == False:
	print("preparecapture FAILED")
	exit()

if cam.startcapture() == False:
	print("startcapture FAILED")
	exit()

cv2.namedWindow("dcam", cv2.WINDOW_NORMAL)
cv2.resizeWindow("dcam", 1024, 1024)

for i in range(0, framestocapture):
	if cam.waitforframe(5000) == False:
		print("waitforframe FAILED")
		exit()
	image = cam.getframe(-1)
	cv2.imshow("dcam", (image).astype(np.uint8))
	cv2.waitKey(100)

cv2.destroyAllWindows()
cam.stopcapture()
cam.unpreparecapture()
cam.close()
dcampy.uninit()

