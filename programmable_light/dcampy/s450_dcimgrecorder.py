import sys
import ctypes
import msvcrt
import time
import dcampy

print("S450_DCIMGRECORDER START")

framestocapture = 10
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


retval = cam.preparecapture(-1, seqframes)
if retval == False:
	print("preparecapture FAILED")
	exit()

retval = cam.startrecorder("e:/temp/python.dcimg", framestocapture)
if retval == False:
	print("startrecorder FAILED")
	exit()

retval = cam.startcapture()
if retval == False:
	print("startcapture FAILED")
	exit()

recorderframecount = 0

while recorderframecount < framestocapture:
	time.sleep(1)
	recorderframecount = cam.getrecorderframecount()
	print("Current Frame Count:", recorderframecount)

cam.stopcapture()
cam.stoprecorder()
cam.unpreparecapture()
cam.close()
dcampy.uninit()
