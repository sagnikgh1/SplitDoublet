#!/usr/bin/env python

'''
    Module for controlling hardware devices such as display, spectrometer
    and (soon) Hamamatsu camera
'''


# System imports
import os
import sys
import pdb
import ctypes
import socket
from tqdm import tqdm

# Paths for drivers and dlls
import platform

if platform.system() == 'Windows':
    OOI_HOME = 'C:/Program Files/Ocean Optics/OmniDriverSPAM/OOI_HOME/'
    print('Am here')

    if socket.gethostname() == 'DESKTOP-31LNKSF':
        print('Airybison laptop')
        JAVA_HOME = 'C:/Program Files/Java/jdk-13/bin/server'
    else:
        JAVA_HOME = 'C:/Program Files/Java/jdk-15.0.2/bin/server'
        
elif platform.system() == 'Linux':
    OOI_HOME = '/home/vishwanath/OmniDriver/OOI_HOME'
    JAVA_HOME = os.environ['JAVA_HOME']

# Numpy-ish imports
import numpy as np
import matplotlib.pyplot as plt

# Hacky way of getting SDL2 path
from modules import this_path
SDL_HOME = this_path.__file__.replace('this_path.py', 'libsdl/')

# Set global environment variables
os.environ['CLASSPATH'] = '%s/OmniDriver.jar'%OOI_HOME
os.environ['PATH'] = '%s;%s'%(os.environ['PATH'], JAVA_HOME)
os.environ['PATH'] = '%s;%s'%(os.environ['PATH'], OOI_HOME)

# Set the SDL home only if in windows
if sys.platform == 'win32':
    os.environ['PYSDL2_DLL_PATH'] = SDL_HOME

# NOTE: It is very important to set this variable to zero, else only the
#       last created window works.
os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'

# Now import jni
try:
    from jnius import autoclass
    from jnius import JavaException
except ImportError:
    print('Java/pyjnius was not found. Spectrometer will not work')

# SDL imports
import sdl2
import sdl2.ext

# Import Hamamatsu provided DCAM files
try:
    from modules import dcampy
    from modules import dcamapi
except OSError:
    print('Hamamatsu camera will not work')

# Import Spinnaker module
try:
    import PySpin
except ImportError:
    print('PySpin not found. Spinnaker camera will not work')

class Spectrometer(object):
    '''
        Class for handling Ocean Optics FLAME spectrometer. Relies on java
        classes and pyjnius wrapper  to control.
    '''
    def __init__(self, device_id=0, exposure_time=10, nscans=1):
        '''
            Constructor for spectrometer class

            Inputs:
                device_id: Number of the device to open. Default is 0.
                exposure_time: Integration time in ms. Default is 10ms
                nscans: Number of scans to capture. Default is 1.

            Outputs:
                status: 1 if successful, -1 if opening spectrometer failed

        '''
        self.id = device_id

        # First, create a wrapper
        wrapper_name = 'com.oceanoptics.omnidriver.api.wrapper.Wrapper'
        wrapper_cls = autoclass(wrapper_name)

        # Open a new wrapper
        self.wrapper = wrapper_cls()

        # Open all spectrometers
        ndevices = self.wrapper.openAllSpectrometers()

        if ndevices < self.id+1:
            raise RuntimeError('Not enough attached devices')

        # Set parameters
        self.set_params(exposure_time, nscans)

        # Set correction parameters
        self.wrapper.setCorrectForDetectorNonlinearity(self.id, 1)
        self.wrapper.setCorrectForElectricalDark(self.id, 1)

        # Get wavelengths
        self.wvl = np.array(self.wrapper.getWavelengths(self.id))

    def capture(self):
        '''
            Capture a single spectrum from the device

            Inputs: None

            Outputs:
                spectrum: Captured spectrum for given parameters
        '''
        return np.array(self.wrapper.getSpectrum(self.id))

    def set_params(self, exposure_time=10, nscans=1):
        '''
            Modify integration time and number of scans for the device

            Inputs:
                exposure_time: Exposure time in ms
                nscans: Number of scans

            Outputs:
                None
        '''
        self.wrapper.setIntegrationTime(self.id, exposure_time*1000)
        self.wrapper.setScansToAverage(self.id, nscans)

    def close(self):
        '''
            Close the spectrometer device

            Inputs: None
            Outputs: None
        '''
        self.wrapper.closeAllSpectrometers()

class Display(object):
    '''
        Display class for displaying fullscreen images on (second) screen.
        Relies on SDL2 library
    '''
    def __init__(self, screen_id=0, window_name='New window', initialize=True,
                 delay=5):
        '''
            Initializer for display class.

            Inputs:
                screen_id: Which screen to display images on. Default is 0
                window_name: Name of the window. Default is 'New window'
                initialize: If True, initialize video system.
                delay: Time delay after rendering in milliseconds

            Outputs:
                None
        '''
        self.id = screen_id
        self.window_name = window_name
        self.delay = delay

        # Use this for saving created surfaces.
        self._counter = 0

        # First, initialize SDL Video interface
        if initialize:
            sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)

        # Find number of displays
        ndisplays = sdl2.SDL_GetNumVideoDisplays()

        if ndisplays < screen_id+1:
            raise RuntimeError('Fewer displays than required')

        # Get screen bounds
        self.bounds = sdl2.SDL_Rect()
        ret = sdl2.SDL_GetDisplayBounds(self.id, self.bounds)

        # Add bounds size as a member variable
        self.shape = [self.bounds.h, self.bounds.w]

        # Create a new window
        flags = (sdl2.SDL_WINDOW_FULLSCREEN | sdl2.SDL_WINDOW_OPENGL |
                 sdl2.SDL_WINDOW_SHOWN)

        sdl2.SDL_GL_SetAttribute(sdl2.SDL_GL_SHARE_WITH_CURRENT_CONTEXT, 0)

        self._window = sdl2.SDL_CreateWindow(window_name.encode(),
                                             self.bounds.x,
                                             self.bounds.y,
                                             self.bounds.w,
                                             self.bounds.h,
                                             flags)

        # Create a GL Context for VSYNC
        self._glcontext = sdl2.SDL_GL_CreateContext(self._window)

        # Now create a renderer
        flags = (sdl2.SDL_RENDERER_ACCELERATED |
                 sdl2.SDL_RENDERER_PRESENTVSYNC |
                 sdl2.SDL_RENDERER_TARGETTEXTURE)
        self._renderer = sdl2.SDL_CreateRenderer(self._window, -1, flags)

        # Set swap interval to 1 for update synced with VSYNC
        retval = sdl2.SDL_GL_SetSwapInterval(1)
        if retval == -1:
            print('Adaptive VSYNC not supported')

        # Now time to create the data buffer for screen image.
        # XXX: Make sure the data is contiguous by setting order='c'
        h = self.bounds.h
        w = self.bounds.w
        self._data = np.zeros((h, w, 3), dtype=np.uint8, order='C')

        # Create the surface
        self._create_surface()

        # Start off by displaying the blank image
        self.render()

    def _create_surface(self):
        '''
            Convert RGB image to SDL2 surface
        '''
        h = self.bounds.h
        w = self.bounds.w

        # Masks for RGB channels
        rmask = 0x000000ff
        gmask = 0x0000ff00
        bmask = 0x00ff0000
        amask = 0x00000000

        # Compute the stride
        depth = 24
        pitch = 3*w

        # Create a data pointer out of member data buffer
        data_ptr = ctypes.c_void_p(self._data.ctypes.data)

        # Now create the surface
        self._surface = sdl2.SDL_CreateRGBSurfaceFrom(data_ptr,
                                                      ctypes.c_int(w),
                                                      ctypes.c_int(h),
                                                      ctypes.c_int(depth),
                                                      ctypes.c_int(pitch),
                                                      ctypes.c_uint32(rmask),
                                                      ctypes.c_uint32(gmask),
                                                      ctypes.c_uint32(bmask),
                                                      ctypes.c_uint32(amask))

    def create_textures_from_stack(self, imstack):
        '''
            Create a list of textures from a 3D numpy stack.

            Inputs:
                imstack: Numpy stack of arrays (H x W x nimg). Values must
                    be normalized between 0, 1 before passing.

            Outputs:
                textures: List of texture for each image
        '''
        textures = []

        if imstack.dtype == np.uint8:
            pass
        else:
            imstack = (imstack*255).astype(np.uint8)

        for idx in tqdm(range(imstack.shape[2])):
            textures.append(self.create_texture_from_numpy(imstack[:, :, idx]))

        return textures

    def create_texture_from_numpy(self, im):
        '''
            Create texture from a numpy array by saving and loading image.

            Inputs:
                im: Numpy array (uint8)

            Outputs:
                texture: Created texture.
        '''
        if np.ndim(im) == 2:
            im = np.tile(im[:, :, np.newaxis], [1, 1, 3])

        # Make sure the size of image matches size of screen
        [H, W, _] = im.shape

        if (H != self.bounds.h) or (W != self.bounds.w):
            raise ValueError('Image must be same size as screen')

        # Copy image data to our own buffer
        self._data[:, :, :] = im[:, :, :]

        # Now create texture
        im_texture = sdl2.SDL_CreateTextureFromSurface(self._renderer,
                                                       self._surface)

        return im_texture

    def destroy_textures(self, textures):
        for texture in textures:
            sdl2.SDL_DestroyTexture(texture)

    def render(self, texture=None):
        '''
            Render the image to GPU buffer and onto screen for a given texture.

            If texture is None, self._surface is used to create one.
        '''
        # https://stackoverflow.com/questions/22227811/ ...
        # ... sdl2-and-opengl-functions-with-two-windows
        #
        # If handling multiple windows, you need to set the current GL
        # context
        sdl2.SDL_GL_MakeCurrent(self._window, self._glcontext)
        
        if texture is None:
            texture = sdl2.SDL_CreateTextureFromSurface(self._renderer,
                                                        self._surface)

        #sdl2.SDL_RenderClear(self._renderer)
        sdl2.SDL_RenderCopy(self._renderer, texture, None, None)
        sdl2.SDL_RenderPresent(self._renderer)

    def showData(self, im):
        '''
            Display a given image.

            Inputs:
                im: Image of same size as screen. Can be either RGB or grayscale

            Outputs: None
        '''
        if np.ndim(im) == 2:
            im = np.tile(im[:, :, np.newaxis], [1, 1, 3])

        # Make sure the size of image matches size of screen
        [H, W, _] = im.shape

        if (H != self.bounds.h) or (W != self.bounds.w):
            raise ValueError('Image must be same size as screen')

        # Copy image data to our own buffer
        self._data[:, :, :] = im[:, :, :]

        # And then render
        self.render()

        # Wait for it to update for
        sdl2.SDL_Delay(self.delay)

    def close(self):
        '''
            Close the display
        '''
        # Python has a problem when closing the window -- the window
        # disappears only when python is closed. So just display all black
        # and then close
        self._data[:, :, :] = 0
        self.render()

        # Now it is okay to close
        sdl2.SDL_DestroyWindow(self._window)
        sdl2.SDL_FreeSurface(self._surface)
        sdl2.SDL_Quit()

class HCamera(object):
    '''
        Camera class wrapper for Hamamatsu camera. Uses DCAM API provided by
        Hamamatsu folks. Thanks a lot!
    '''
    def __init__(self, cam_num=0, exposure_time=10, binning=1, mode=0,
                 roi_pos=[0, 0], roi_size=[512, 512], waittime=5000,
                 fast=False):
        '''
            Initialize a Hamamatsu camera.

            Inputs:
                cam_num: Number of the camera. Default is 0
                exposure_time: Integration time in milliseconds. Default is 10ms
                binning: Number of pixels to bin. ORCA Flash 4.0 LT only
                    supports 1, 2, 4.
                mode: Camera capture mode. 0 is internal, 2 is external edge.
                waittime: Waiting time before bailing out for a new frame
                fast: If True, image buffer is only created in the beginning.
                    WARNING: fast may not work correctly.                

            Outputs: None
        '''
        self.id = cam_num
        self.waittime = waittime
        self.bufsize = 10            # Hard coded, suggested by Ciprian
        self.fast = fast
        self.trig_mode = mode

        # Initialize camera
        ncameras = dcampy.init()
        if (ncameras < self.id+1):
            raise IOError('Could not find the requested number of cameras')

        # Open a new camera object
        self._camera = dcampy.Camera()
        self.verify(self._camera.open(self.id), 'Camera opening')

        # Set exposure
        self.set_exposure(exposure_time)

        # Set exposure type to delayed exposure
        trigtype = dcamapi.DCAMPROPMODEVALUE.TRIGGER_GLOBALEXPOSURE__DELAYED
        trigprop = dcamapi.DCAMIDPROP.TRIGGER_GLOBALEXPOSURE
        self.verify(self._camera.setpropvalue(trigprop, trigtype),
                    'Exposure type')

        # Set binning
        if binning == 1:
            prop_mode = dcamapi.DCAMPROPMODEVALUE.BINNING__1
        elif binning == 2:
            prop_mode = dcamapi.DCAMPROPMODEVALUE.BINNING__2
        elif binning == 4:
            prop_mode = dcamapi.DCAMPROPMODEVALUE.BINNING__4
        self.verify(self._camera.setpropvalue(dcamapi.DCAMIDPROP.BINNING,
                                              prop_mode), 'Binning')

        #Set ROI
        self.verify(self._camera.setpropvalue(dcamapi.DCAMIDPROP.SUBARRAYHSIZE,
                                              roi_size[1]), 'ROI HSIZE')
        self.verify(self._camera.setpropvalue(dcamapi.DCAMIDPROP.SUBARRAYVSIZE,
                                              roi_size[0]), 'ROI VSIZE')
        self.verify(self._camera.setpropvalue(dcamapi.DCAMIDPROP.SUBARRAYHPOS,
                                              roi_pos[1]), 'ROI HPOS')
        self.verify(self._camera.setpropvalue(dcamapi.DCAMIDPROP.SUBARRAYVPOS,
                                              roi_pos[0]), 'ROI VPOS')

        # Do not forget to enable subarray mode
        mode_on = dcamapi.DCAMPROPMODEVALUE.MODE__ON
        self.verify(self._camera.setpropvalue(dcamapi.DCAMIDPROP.SUBARRAYMODE,
                                              mode_on), 'ROI ON')
        self.roi_pos = roi_pos
        self.roi_size = roi_size

        # Get image dimensions
        H = self._camera.getpropvalue(dcamapi.DCAMIDPROP.IMAGE_HEIGHT)
        W = self._camera.getpropvalue(dcamapi.DCAMIDPROP.IMAGE_WIDTH)

        self.size = [H, W]

        # Set trigger
        if mode == 0:
            mode = dcamapi.DCAMPROPMODEVALUE.TRIGGERSOURCE__INTERNAL
        elif mode == 1:
            mode = dcamapi.DCAMPROPMODEVALUE.TRIGGERSOURCE__SOFTWARE
        elif mode == 2:
            mode = dcamapi.DCAMPROPMODEVALUE.TRIGGERSOURCE__EXTERNAL
        else:
            raise AttributeError('Trigger option not defined')

        self.verify(self._camera.setpropvalue(
                dcamapi.DCAMIDPROP.TRIGGERSOURCE, mode), 'Trigger set')

        # If you set it to free running mode, then we are fine.
        if self.fast:
            self.verify(self._camera.preparecapture(-1, self.bufsize),
                        'Prepare capture')
            self.verify(self._camera.startcapture(), 'Start capture')

    def verify(self, retval, dbg_string='Unknown error'):
        '''
            Tiny wrapper to raise error when DCAMAPI is used
        '''
        if retval == False:
            raise AttributeError('DCAMAPI failed at %s'%dbg_string)

    def set_exposure(self, exposure_time):
        '''
            Separate method for setting exposure time.
        '''
        self.verify(self._camera.setpropvalue(dcamapi.DCAMIDPROP.EXPOSURETIME,
                                              exposure_time/1000.0),
                    'Exposure time')

    def fire_trigger(self):
        '''
            This function should have been defined in dcampy or dcamapi but it
            is not. The idea is to fire a trigger for software-triggered
            exposure.
        '''
        # The C++ definition is dcamcap_firetrigger(hdcam)
        retval = dcamapi.firetrigger(self._camera._hdcam)
        self.verify(retval, 'Fire trig')

    def capture(self, navg=1):
        '''
            Capture a single images.

            Inputs:
                navg: Number of images to average

            Outputs:
                img: Captured and averaged images
        '''
        img_accum = 0

        # If not in fast mode, prepare and start capture
        if not self.fast:
            self.verify(self._camera.preparecapture(-1, navg),
                        'Prepare capture')
            self.verify(self._camera.startcapture(), 'Start capture')
        for idx in range(navg):
            self.verify(self._camera.waitforframe(self.waittime), 'Waiting')
            buf = self._camera.getframe(self._camera.getcaptureindex())
            #buf = self._camera.getframe(-1)
            img_accum += buf.astype(np.float32)

        if not self.fast:
            self.verify(self._camera.stopcapture(), 'Stop capture')
            self.verify(self._camera.unpreparecapture(), 'Unprepare capture')

        img_accum = img_accum/navg

        return img_accum
    
    def close(self):
        '''
            Safely shutdown the camera.
        '''
        # If in fast mode, stop capture now
        if self.fast:
            self.verify(self._camera.stopcapture(), 'Stop capture')
            self.verify(self._camera.unpreparecapture(), 'Unprepare capture')
            
        self.verify(self._camera.close(), 'Close camera')
        dcampy.uninit()

class SPCamera(object):
    '''
        Create a class to handle Spinnaker (ptgrey) cameras.

        Inputs:
            cam_id: Camera id (default is 0)
            exposure_time: Exposure time in ms
            gain: Gain in dB
            trig_pin: Trigger pin. Set to -1 (default) to disable trigger

        Outputs:
            None
    '''
    def __init__(self, cam_id=0, exposure_time=10, binning=1,
                 trig_pin=-1, roi_pos=[-1, -1], roi_size=[0, 0],
                 fast=True, gain=0, debug=False, isrgb=False, israw=False):
        # The option fast=True is just to make the SPCamera compatible with
        # HCamera.
        
        # Create a PySpin system
        self.debug = debug
        self.isrgb = isrgb
        self.israw = israw
        
        if debug:
            print('\tInitializing PySpin system')   
        self._system = PySpin.System.GetInstance()

        if debug:
            print('\tGetting list of cameras')
        self._cam_list = self._system.GetCameras()
        ncameras = self._cam_list.GetSize()

        if type(cam_id) == int:
            if ncameras < cam_id+1:
                raise IOError('Could not find required number of cameras')

            self._cam = self._cam_list[cam_id]
        elif type(cam_id) == str:
            self._cam = self._cam_list.GetBySerial(cam_id)

        # Initialize camera
        if debug:
            print('\tInitializing the camera')

        try:
            self._cam.Init()
        except PySpin.SpinnakerException:
            raise AttributeError('Could not initialize camera')

        if debug:
            print('\tSetting continuous acqusition mode')
        if self._cam.AcquisitionMode.GetAccessMode() != PySpin.RW:
            raise ValueError('Unable to set continuous acquisition mode.')

        self._cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)

        # Set Gain now
        if debug:
            print('\tSetting gain')
        if self._cam.GainAuto.GetAccessMode() != PySpin.RW:
            raise ValueError('Cannot configure gain. Bailing out.')

        self._cam.GainAuto.SetValue(PySpin.GainAuto_Off)

        if self._cam.Gain.GetAccessMode() != PySpin.RW:
            raise ValueError('Cannot set gain. Bailing out.')

        self._cam.Gain.SetValue(gain)

        # Finally, configure trigger mode
        # Need nodemap for this
        if debug:
            print('\tSetting trigger')
        nodemap = self._cam.GetNodeMap()

        # Rely on QuickSpin settings
        if self._cam.TriggerSource.GetAccessMode() != PySpin.RW:
            raise AttributeError('Cannot control trigger.')

        self.software_trigger = False
        
        if trig_pin == -1:
            self._cam.TriggerSource.SetValue(PySpin.TriggerSource_Software)
            self.software_trigger = True
        elif trig_pin == 0:
            self._cam.TriggerSource.SetValue(PySpin.TriggerSource_Line0)
        elif trig_pin == 1:
            self._cam.TriggerSource.SetValue(PySpin.TriggerSource_Line1)
        elif trig_pin == 2:
            self._cam.TriggerSource.SetValue(PySpin.TriggerSource_Line2)
        else:
            raise AttributeError('Trigger pin is not supported')

        self._cam.TriggerMode.SetValue(PySpin.TriggerMode_On)

        # Before setting exposure, disable framerate control
        if debug:
            print('\tDisabling auto frame rate')

        af_str = 'AcquisitionFrameRateEnabled'
        autoframe_mode = PySpin.CBooleanPtr(nodemap.GetNode(af_str))

        if not PySpin.IsAvailable(autoframe_mode):
            print('autoframe feature does not exist')
        else:
            autoframe_mode.SetValue(False)

        # Set Gamma
        if self._cam.GammaEnable.GetAccessMode() == PySpin.RW:
            self._cam.GammaEnable.SetValue(False)
        else:
            print('Cannot set Gamma level')

        # Disable black level
        if debug:
            print('\tDisabling black level')

        bl_str = 'BlackLevelEnabled'
        blacklevel_mode = PySpin.CBooleanPtr(nodemap.GetNode(bl_str))

        if not PySpin.IsAvailable(blacklevel_mode) or not (
            PySpin.IsReadable(blacklevel_mode)):
            print('Cannot configure black level.')
        else:
            blacklevel_mode.SetValue(False)
            
        # Exposure can be configured only after trigger.
        if debug:
            print('\tSetting exposure')
        if self._cam.ExposureAuto.GetAccessMode() != PySpin.RW:
            raise AttributeError('Cannot configure exposure. Bailing out.')

        self._cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

        if self._cam.ExposureTime.GetAccessMode() != PySpin.RW:
            raise AttributeError('Unable to set exposure time. Bailing out.')

        self._cam.ExposureTime.SetValue(exposure_time*1000)

        # Start continuous acquisition
        if debug:
            print('\tStarting acquisition')
        self._cam.BeginAcquisition()

        # Set pixel format to Mono 16
        self._cam.EndAcquisition()

        if self.isrgb:
            if self.israw:
                pixformat = PySpin.PixelFormat_BayerRG8
            else:
                pixformat = PySpin.PixelFormat_RGB8Packed
        else:
            pixformat = PySpin.PixelFormat_Mono8
            
        if self._cam.PixelFormat.GetAccessMode() == PySpin.RW:
            self._cam.PixelFormat.SetValue(pixformat)
        else:
            print('\tCannot change pixel format')

        # Disable white balancing if pixelformat is RGB
        if self.isrgb:
            if self._cam.BalanceWhiteAuto.GetAccessMode() == PySpin.RW:
                self._cam.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Off)
            else:
                print('\tCannot disable auto white balance')

            if self._cam.BalanceRatioSelector.GetAccessMode() == PySpin.RW:
                selector = PySpin.BalanceRatioSelector_Blue
                self._cam.BalanceRatioSelector.SetValue(selector)
            else:
                print('\tCannot set blue balance ratio selector')

            if self._cam.BalanceRatio.GetAccessMode() == PySpin.RW:
                self._cam.BalanceRatio.SetValue(2.0)
            else:
                print('\tCannot set white balance ratio for blue channel')

            if self._cam.BalanceRatioSelector.GetAccessMode() == PySpin.RW:
                selector = PySpin.BalanceRatioSelector_Red
                self._cam.BalanceRatioSelector.SetValue(selector)
            else:
                print('\tCannot set red balance ratio selector')

            if self._cam.BalanceRatio.GetAccessMode() == PySpin.RW:
                self._cam.BalanceRatio.SetValue(1.0)
            else:
                print('\tCannot set white balance ratio for red channel')

        self._cam.BeginAcquisition()

        # Set binning
        self.set_binning(binning)

        # Set region of interest
        self.set_roi(roi_size, roi_pos)

    def set_binning(self, binning=1):
        '''
            Set binning
        '''
        # Stop acquisition before changing binning
        self._cam.EndAcquisition()
        if self._cam.BinningVertical.GetAccessMode() == PySpin.RW:
            self._cam.BinningVertical.SetValue(binning)
        else:
            print('\tCannot change vertical binning')

        if self._cam.BinningHorizontal.GetAccessMode() == PySpin.RW:
            self._cam.BinningHorizontal.SetValue(binning)
        else:
            print('\tCannot change horizontal binning')

        # Then restart acquisition
        self._cam.BeginAcquisition()

    def set_exposure(self, exposure_time=16.5):
        '''
            Set exposure time on the fly.

            Inputs:
                exposure_time: Exposure time in ms
        '''
        if self._cam.ExposureAuto.GetAccessMode() != PySpin.RW:
            raise AttributeError('Cannot configure exposure.')

        self._cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

        if self._cam.ExposureTime.GetAccessMode() != PySpin.RW:
            raise AttributeError('Unable to set exposure time.')

        self._cam.ExposureTime.SetValue(exposure_time*1000)

    def set_roi(self, roi_size, roi_offset=[-1, -1]):
        '''
            Change region of interest, and binning.

            Inputs:
                roi_size: 2-tuple with Height and width of region of interest
                roi_offset: 2-tuple of top left corner of ROI. If any entry
                    is -1, roi is centered.

            WARNING: ROI size and offset have to respect binning
        '''
        # Stop acquisition before changing ROI configuration
        self._cam.EndAcquisition()
        
        Hmax = self._cam.Height.GetMax()
        Wmax = self._cam.Width.GetMax()

        H, W = roi_size
        Ho, Wo = roi_offset

        # If any entry of roi_size is 0, set roi size to maximum
        if (H == 0) or (W == 0):
            H = Hmax
            W = Wmax

        if ((H + Ho) > Hmax) or ((W + Wo) > Wmax):
            raise ValueError('ROI configuration is wrong')

        # Set ROI dimensions first
        if self._cam.Width.GetAccessMode() == PySpin.RW:
            self._cam.Width.SetValue(W)
        else:
            print('Cannot set width of ROI')

        if self._cam.Height.GetAccessMode() == PySpin.RW:
            self._cam.Height.SetValue(H)
        else:
            print('Cannot set height of ROI')

        # Then set offset
        if (Ho < 0) or (Wo < 0):
            Ho = 4 * ((Hmax - H)//8)
            Wo = 4 * ((Wmax - W)//8)

        if self._cam.OffsetX.GetAccessMode() == PySpin.RW:
            self._cam.OffsetX.SetValue(Wo)
        else:
            print('Cannot set width offset')

        if self._cam.OffsetY.GetAccessMode() == PySpin.RW:
            self._cam.OffsetY.SetValue(Ho)
        else:
            print('Cannot set height offset')

        # Now we can restart acquisition
        self._cam.BeginAcquisition()
            
        
    def capture(self, navg=1):
        '''
            Capture and return an image
        '''
        imgcap = 0
        for idx in range(navg):
            try:
                if self.software_trigger:
                    self._cam.TriggerSoftware.Execute()
                    
                img = self._cam.GetNextImage()
                H = img.GetHeight()
                W = img.GetWidth()

                # Convert to RGB if required
                if self.isrgb:
                    if self.israw:                       
                        imgdata = img.GetData().reshape(H, W)
                    else:
                        imrgb = img.Convert(PySpin.PixelFormat_RGB8,
                                            PySpin.HQ_LINEAR)
                        imgdata = imrgb.GetData().reshape(H, W, -1)
                else:
                    imgdata = img.GetData().reshape(H, W)

                if navg == 1:
                    img.Release()
                    return imgdata
                else:
                    imgcap += imgdata.astype(np.float32)

                img.Release()
            except:
                pdb.set_trace()
                print('Not sure what happened, but shutting down system')
                self.close()

                raise SystemError('Camera malfunctioned')

        return imgcap/navg

    def close(self):
        '''
            Close the camera and release the system
        '''
        # Reset trigger
        if self._cam.TriggerMode.GetAccessMode() != PySpin.RW:
            raise AttributeError('Unable to disable trigger')

        self._cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)

        self._cam.EndAcquisition()
        
        if self.debug:
            print('\tDeleting camera')
        del self._cam

        if self.debug:
            print('\tClearing camera list')
        self._cam_list.Clear()

        if self.debug:
            print('\tReleasting PySpin system')
        self._system.ReleaseInstance()

if __name__ == '__main__':
    camera = SPCamera(exposure_time=50, gain=10, isrgb=True)

