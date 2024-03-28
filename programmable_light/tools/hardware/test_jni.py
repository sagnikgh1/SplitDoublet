#!/usr/bin/env python3

# Script to test spectrometer

import os
import sys

import numpy as np

import matplotlib.pyplot as plt

# Necessary for making jnius work correctly
OOI_HOME = 'C:/Program Files/Ocean Optics/OmniDriverSPAM/OOI_HOME/'
os.environ['CLASSPATH'] = '%s/OmniDriver.jar'%OOI_HOME

JAVA_HOME = 'C:/Program Files/Java/jdk1.8.0_191/jre/bin/server'
os.environ['PATH'] = '%s;%s'%(os.environ['PATH'], JAVA_HOME)
os.environ['PATH'] = '%s;%s'%(os.environ['PATH'], OOI_HOME)

from jnius import autoclass

def set_spectrometer(wrapper, device_id=0, exposure_time=10 , nscans=1):
    '''
        Function to open and set properties for a spectrometer

        Inputs:
            wrapper: (Opened) Java wrapper for spectrometer interface
            device_id: Number of the device to open. Default is 0, first device
            exposure_time: Integration time in ms. Default is 10ms
            nscans: Number of scans to capture. Default is 1.

        Outputs:
            wvl: Wavelengths
            
    '''
    ndevices = wrapper.openAllSpectrometers()

    if ndevices < device_id + 1:
        raise RuntimeError('Fewer devices than requested')

    # Set parameters
    wrapper.setIntegrationTime(device_id, exposure_time*1000)
    wrapper.setScansToAverage(device_id, nscans)

    # Set correction parameters
    wrapper.setCorrectForDetectorNonlinearity(device_id, 1)
    wrapper.setCorrectForElectricalDark(device_id, 1)

    # Now get wavelengths
    wvl = np.array(wrapper.getWavelengths(device_id))

    return wvl

if __name__ == '__main__':
    # Measurement constants
    exposure_time = 500                 # Exposure time in ms
    nscans = 1                          # Number of scans
    device_id = 0                       # Device ID (0 for single device)

    # Get the spectrometer wrapper
    wrapper_name = 'com.oceanoptics.omnidriver.api.wrapper.Wrapper'
    wrapper_cls = autoclass(wrapper_name)

    # Create an instance
    wrapper = wrapper_cls()

    # Open and set required parameters
    wvl = set_spectrometer(wrapper, device_id, exposure_time, nscans)

    # Measure one spectrum
    spectrum = np.array(wrapper.getSpectrum(device_id))

    # Plot
    plt.plot(wvl, spectrum)
    plt.autoscale(enable=True, tight=True)
    plt.grid(True)
    plt.xlabel('$\lambda$')
    plt.ylabel('Intensity')
    plt.show()
