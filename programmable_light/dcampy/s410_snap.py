import sys
import ctypes
import cv2
import msvcrt
import dcampy
import dcamapi

import matplotlib.pyplot as plt

print("S410_SNAP START")

snapframes = 1

totalcams = dcampy.init()
if(totalcams <= 0):
	print("No Cameras Found")
	exit()

cam = dcampy.Camera()
if cam.open(0) == False:
	print("open FAILED")
	exit()

print(str(cam))
print("Model   =", cam.getstringinfo(dcampy.dcamapi.IDSTR.MODEL))
print("Serial  =", cam.getCameraSerial())
print("Version =", cam.getCameraVersion())

# Set binning
if cam.setpropvalue(dcampy.dcamapi.DCAMIDPROP.BINNING,
                    dcampy.dcamapi.DCAMPROPMODEVALUE.BINNING__2) == False:
        print('Binning failed')
        exit()

if cam.setpropvalue(dcampy.dcamapi.DCAMIDPROP.EXPOSURETIME, 100/1000) == False:
	print("setpropvalue FAILED")
	exit()

exposure = cam.getpropvalue(dcamapi.DCAMIDPROP.EXPOSURETIME)
print("Exposure =", exposure)

H = cam.getpropvalue(dcamapi.DCAMIDPROP.IMAGE_HEIGHT)
W = cam.getpropvalue(dcamapi.DCAMIDPROP.IMAGE_WIDTH)
print('Image dimensions: [%d, %d]'%(H, W))

mode = dcamapi.DCAMPROPMODEVALUE.TRIGGERSOURCE__EXTERNAL
cam.setpropvalue(dcampy.dcamapi.DCAMIDPROP.TRIGGERSOURCE, mode)
if cam.preparecapture(0, snapframes) == False:
	print("preparecapture FAILED")
	exit()

if cam.startcapture() == False:
	print("startcapture FAILED")
	exit()

if cam.waitforframe(5000) == False:
	print("waitforframe FAILED")
	exit()

image = cam.getframe(-1)
plt.imshow(image, cmap='gray'); plt.show()
cam.stopcapture()
cam.unpreparecapture()
cam.close()

dcampy.uninit()
