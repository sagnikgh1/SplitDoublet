import sys
import ctypes
import cv2
import msvcrt
import dcampy

print("S430_PROPERTIES START")

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

proplist = cam.getproplist(0)

for pl in proplist:
	name = cam.getpropname(pl)
	attr = cam.getpropinfo(pl)

	print(name, pl)
	typemask = attr.attribute & 0x0000000F
	if typemask == 1:
		vtlist = cam.getvaluetextlist(pl)
		for vtl in vtlist:
			textvalue = cam.getvaluetext(pl, vtl)
			print("\t{} {}".format(textvalue, vtl))
	else:
		print("\tMin:  {}".format(attr.valuemin))
		print("\tMax:  {}".format(attr.valuemax))
		print("\tStep: {}".format(attr.valuestep))
		print("\tDef:  {}".format(attr.valuedefault))


cam.close()
dcampy.uninit()

