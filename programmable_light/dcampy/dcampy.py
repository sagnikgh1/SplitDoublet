import ctypes
from ctypes import c_int32, c_uint32, c_void_p, c_char_p, c_double
from ctypes import Structure, POINTER, sizeof, byref
import numpy
import dcamapi

def init():
	initparam = dcamapi.DCAMAPI_INIT()
	retval = dcamapi.init(initparam)
	if retval != dcamapi.DCERR.SUCCESS:
		return 0
	return initparam.iDeviceCount

def uninit():
	retval = dcamapi.uninit()
	if retval != dcamapi.DCERR.SUCCESS:
		return False
	return True

class Property(Structure):
	_pack_ = 8
	_fields_ = [
		("type", 				c_int32),
		("mode", 				c_int32),
		("id", 					c_int32),
		("name", 				c_char_p),
		("attributes", 			c_uint32),
		("value_current", 		POINTER(c_double*4)),
		("value_min", 			c_double),
		("value_max", 			c_double),
		("value_step", 			c_double),
		("value_default", 		c_double),
		("value_text_no", 		c_int32),
		("value_text", 			POINTER(c_char_p*16)),
		("value_text_value", 	POINTER(c_double*16)),
	]

class Camera:
	def __init__(self, index=-1):
		"""
		Constructor of Camera.
		Initialize camera and get handle.
		"""
		self._index = index
		self._hdcam = c_void_p(None)
		self._hrec = c_void_p(None) 
		self._hwait = c_void_p(None)
		self._bOpened = False		#hdcam
		self._bOpenedrec = False	#hrec
		self._bOpenedwait = False	#hwait
		self._bAlloc = False		#True: called dcambuf_alloc() / False: not called dcambuf_alloc(), or called dcambuf_release()
		self._bCapturing = False
		self._nAllocatedFrames = 0
		self._mCaptureMode = 1
		return

	def __repr__(self):
		return 'Camera({})'.format(self._index)

	def __str__(self):
		model = self.getCameraModel()
		return 'Camera class for {} at index {}'.format(model, self._index)

	def __len__(self):
		" Return number of frames available to read "
		if self._bAlloc == False:
			return 0
		transferparam = dcamapi.DCAMCAP_TRANSFERINFO()
		retval = dcamapi.gettransferinfo(self._hdcam, transferparam)
		if retval != dcamapi.DCERR.SUCCESS:
			return 0
		if transferparam.nFrameCount < self._nAllocatedFrames:
			return transferparam.nFrameCount
		return self._nAllocatedFrames

	def open(self, index):
		openparam = dcamapi.DCAMDEV_OPEN()
		openparam.index = index
		retval = dcamapi.open(openparam)
		if retval != dcamapi.DCERR.SUCCESS:
			self._bOpened = False
			return 0
		self._hdcam = openparam.hdcam
		self._bOpened = True
		self._index = index
		waitopenparam = dcamapi.DCAMWAIT_OPEN()
		waitopenparam.hdcam = self._hdcam
		retval = dcamapi.waitopen(waitopenparam)	
		if retval != dcamapi.DCERR.SUCCESS:
			return False
		self._hwait = waitopenparam.hwait
		self._bOpenedwait = True
		return True
	
	def close(self):
		if self._bAlloc:
			retval = dcamapi.release(self._hdcam)
		if self._bOpenedwait:
			retval = dcamapi.waitclose(self._hwait)
		if self._bOpened:
			retval = dcamapi.close(self._hdcam)
		return True

	def getstringinfo(self, stringid):
		strsize = 64
		if self._bOpened == False:
			return None
		pystring = "x" * strsize
		b_string = pystring.encode('utf-8')
		stringparam = dcamapi.DCAMDEV_STRING()
		stringparam.iString = stringid
		stringparam.textbytes = strsize
		stringparam.text = ctypes.c_char_p(b_string)
		retval = dcamapi.getstring(self._hdcam, stringparam)
		if retval != dcamapi.DCERR.SUCCESS:
			print("DEBUG:", retval)
			return None
		return stringparam.text.decode()

	def getCameraModel(self):
		return self.getstringinfo(dcamapi.IDSTR.MODEL)

	def getCameraSerial(self):
		return self.getstringinfo(dcamapi.IDSTR.CAMERAID)

	def getCameraVersion(self):
		return self.getstringinfo(dcamapi.IDSTR.CAMERAVERSION)

	def preparecapture(self, mode, frames):
		if self._bOpened == False:
			return False
		if self._bAlloc == True:
			return False
		retval = dcamapi.alloc(self._hdcam, frames)
		if retval != dcamapi.DCERR.SUCCESS:
			self._bAlloc = False
			return False
		self._bAlloc = True
		self._nAllocatedFrames = frames
		self._mCaptureMode = mode	
		return True

	def unpreparecapture(self):
		if self._bCapturing == True:
			return False
		if self._bAlloc == True:
			retval = dcamapi.release(self._hdcam)
			self._bAlloc = False
			self._nAllocatedFrames = 0
		return True

	def startcapture(self):
		if self._bAlloc == False:
			return False
		retval = dcamapi.startcapture(self._hdcam, self._mCaptureMode)
		if retval != dcamapi.DCERR.SUCCESS:
			self._bCapturing = False
			return False
		self._bCapturing = True
		return True
	
	def stopcapture(self):
		retval = dcamapi.stopcapture(self._hdcam)
		self._bCapturing = False
		return True
	
	def getcapturecount(self):
		transferparam = dcamapi.DCAMCAP_TRANSFERINFO()
		retval = dcamapi.gettransferinfo(self._hdcam, transferparam)
		if retval != dcamapi.DCERR.SUCCESS:
			return 0
		return transferparam.nFrameCount
	
	def getcaptureindex(self):
		transferparam = dcamapi.DCAMCAP_TRANSFERINFO()
		retval = dcamapi.gettransferinfo(self._hdcam, transferparam)
		if retval != dcamapi.DCERR.SUCCESS:
			return 0
		return transferparam.nNewestFrameIndex

	def waitforframe(self, timeout):
		waitstartparam = dcamapi.DCAMWAIT_START()
		waitstartparam.eventmask = dcamapi.WAIT_EVENT.CAP_FRAMEREADY
		waitstartparam.timeout = timeout
		retval = dcamapi.waitstart(self._hwait, waitstartparam)
		if retval != dcamapi.DCERR.SUCCESS:
			print("ERROR: waitforframe()", retval)
			return False
		return True
	
	def getframe(self, frameindex):
		frameparam = dcamapi.DCAMBUF_FRAME()
		frameparam.iFrame = frameindex
		retval = dcamapi.lockframe(self._hdcam, frameparam)
		if retval != dcamapi.DCERR.SUCCESS:
			return None
		data_pointer = ctypes.cast(frameparam.buf, ctypes.POINTER(ctypes.c_int))
		buffrommem = ctypes.pythonapi.PyMemoryView_FromMemory
		buffrommem.restype = ctypes.py_object
		buffer = buffrommem(data_pointer, frameparam.width*frameparam.height*2, 0x100)
		data_array = numpy.frombuffer(buffer, dtype=numpy.uint16)
		return numpy.reshape(data_array, (-1, frameparam.width))

	def getproplist(self, option):
		proplist = []
		propid = 0
		func = dcamapi.getnextpropid(self._hdcam, propid, option)
		while func != 0:
			proplist.append(func)
			propid = func
			func = dcamapi.getnextpropid(self._hdcam, propid, option)
		return proplist

	def getpropinfo(self, propid):
		attrparam = dcamapi.DCAMPROP_ATTR()
		attrparam.iProp = propid
		retval = dcamapi.getpropattr(self._hdcam, attrparam)
		if retval != dcamapi.DCERR.SUCCESS:
			print("ERROR: getpropattr")
			return None
		return attrparam

	def getpropvalue(self, propid):
		return dcamapi.getpropvalue(self._hdcam, propid)

	def setpropvalue(self, propid, value):
		retval = dcamapi.setpropvalue(self._hdcam, propid, value)
		if retval != dcamapi.DCERR.SUCCESS:
			return False
		return True

	def getpropname(self, propid):
		strsize = 64
		pystring = " " * strsize
		b_string = pystring.encode('utf-8')
		stringparam = dcamapi.DCAMDEV_STRING()
		stringparam.text = ctypes.c_char_p(b_string)
		newtext = dcamapi.getpropname(self._hdcam, propid, stringparam.text, strsize)
		return newtext.strip()

	def querypropvalue(self, propid, value, option):
		return dcamapi.querypropvalue(self._hdcam, propid, value, option)

	def getvaluetextlist(self, propid):
		valuetextlist = []
		attrparam = dcamapi.DCAMPROP_ATTR()
		attrparam.iProp = propid
		retval = dcamapi.getpropattr(self._hdcam, attrparam)
		typemask = attrparam.attribute & dcamapi.DCAMPROPATTRIBUTE.TYPE_MASK
		if typemask == 1:
			valuetextlist.append(attrparam.valuemin)
			currentvalue = attrparam.valuemin
			while currentvalue != attrparam.valuemax:
				currentvalue = dcamapi.querypropvalue(self._hdcam, propid, currentvalue, dcamapi.DCAMPROPOPTION.NEXT)
				valuetextlist.append(currentvalue)
		return valuetextlist

	def getvaluetext(self, propid, value):
		strsize = 64
		pystring = " " * strsize
		b_string = pystring.encode('utf-8')
		vtparam = dcamapi.DCAMPROP_VALUETEXT()
		vtparam.iProp = propid
		vtparam.value = value
		vtparam.text = ctypes.c_char_p(b_string)
		vtparam.textbytes = strsize
		dcamapi.getvaluetext(self._hdcam, vtparam)
		return vtparam.text.decode()


	def startrecorder(self, path, frames):
		b_string = path.encode('utf-8')
		recparam = dcamapi.DCAMREC_OPEN()
		recparam.path = ctypes.c_char_p(b_string)
		recparam.maxframepersession = frames
		retval = dcamapi.openrec(recparam)
		if retval != dcamapi.DCERR.SUCCESS:
			print("dcamapi.openrec(recparam) FAILED")
			return False
		self._hrec = recparam.hrec
		retval = dcamapi.startrecorder(self._hdcam, self._hrec)
		if retval != dcamapi.DCERR.SUCCESS:
			print("dcamapi.startrecorder(self._hdcam, self._hrec) FAILED")
			return False
		return True

	def stoprecorder(self):
		retval = dcamapi.closerec(self._hrec)
		return False

	def getrecorderframecount(self):
		recorderstatus = dcamapi.DCAMREC_STATUS()
		retval = dcamapi.getrecorderstatus(self._hrec, recorderstatus)
		if retval != dcamapi.DCERR.SUCCESS:
			return False
		return recorderstatus.totalframecount

