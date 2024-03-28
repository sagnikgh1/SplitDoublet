#!/usr/bin/env python

'''
    Central script to capture all calibration data for the programmable light
    source.
'''

# System imports
import os
import sys
import argparse
import configparser
import pickle

# Scientific computing
import numpy as np
import scipy.linalg as lin

# Plotting
import matplotlib.pyplot as plt

from UUTrack.Model.Cameras import Hamamatsu

from modules import utils
from modules import hardware
from modules import coding
from modules import device_utils

def capture_gamma(args, spectrometer, display):
    '''
        Calibrate gamma curve for each wavelength.
    '''
    nlevels = pow(2, args.display_bits)
    data = np.zeros((nlevels, len(spectrometer.wvl)))

    img = np.zeros(display.shape, dtype=np.uint8)

    # First, block light and capture data
    input('Block light and press a key')
    offset_data = spectrometer.capture()

    input('Remove block and press a key')

    # Then other data
    for idx in range(nlevels):
        print('Intensity: %d'%idx)
        img[:, :] = idx
        display.show(img)
        spec = spectrometer.capture()
        data[idx, :] = spec

    # Save data
    wvl = spectrometer.wvl
    utils.savep([args, wvl, offset_data, data],
                'data/%s/gamma_data.pkl'%args.experiment)
    
def capture_mapping(args, spectrometer, display):
    '''
        Capture wavelength-column correspondence
    '''
    # Get binary coding images
    codes = coding.bincode(display.shape[0], display.shape[1], col=True)

    data_p = np.zeros((codes.shape[2], len(spectrometer.wvl)))
    data_n = np.zeros((codes.shape[2], len(spectrometer.wvl)))

    # Zero data
    display.show(np.zeros(display.shape, dtype=np.uint8))
    zero_data = spectrometer.capture()

    # Ones data
    display.show(255*np.ones(display.shape, dtype=np.uint8))
    ones_data = spectrometer.capture()

    # Other data
    for idx in range(codes.shape[2]):
        print('Code %d'%idx)
        display.show((codes[:, :, idx]*255).astype(np.uint8))
        spec = spectrometer.capture()
        data_p[idx, :] = spec

        display.show(255-(codes[:, :, idx]*255).astype(np.uint8))
        spec = spectrometer.capture()
        data_n[idx, :] = spec

    # Save data
    wvl = spectrometer.wvl
    utils.savep([args, wvl, zero_data, ones_data, data_p, data_n],
                'data/%s/mapping_data.pkl'%args.experiment)

def capture_contrast(args, spectrometer, display):
    '''
        Capture contrast ratio data
    '''
    # First, block light and capture data
    input('Block light and press a key')
    offset_data = spectrometer.capture()

    input('Remove block and press a key')

    # Zero data
    print('All zeros data')
    display.show(np.zeros(display.shape, dtype=np.uint8))
    zero_data = spectrometer.capture()

    # Ones data
    print('All ones data')
    display.show(255*np.ones(display.shape, dtype=np.uint8))
    ones_data = spectrometer.capture()

    # Save data
    wvl = spectrometer.wvl
    utils.savep([args, wvl, offset_data, zero_data, ones_data],
                'data/%s/contrast_data.pkl'%args.experiment)

def create_config_and_parser(config_name='config.ini'):
    '''
        Wrapper script to generate system configuration from config file and
        input arguments.

        Inputs:
            config_name: Name used for configuration file.

        Outputs:
            args: Namespace object with experiment and hardware properties
    '''
    # Create a new parser
    parser = argparse.ArgumentParser(description='Calibration data capture')

    # Name of experiment
    parser.add_argument('-e', '--experiment', action='store',
                        required=True, type=str, help='Experiment name')

    # Number of wavelength bands
    parser.add_argument('-w', '--nbands', action='store', type=int,
                        default=32, help='Number of wavelength bands')

    # Exposure time of camera in ms
    parser.add_argument('-i', '--exposure', action='store', type=float,
                        default=10, help='Exposure time (ms)')

    # Number of scans
    parser.add_argument('-n', '--nscans', action='store', type=int,
                        default=1, help='Number of scans')

    # Now parse
    args = parser.parse_args()

    # Now read configuration file
    config = configparser.ConfigParser()
    config.read(config_name)

    # Now parse the configuration file
    args.spectrometer_id = int(config['SPECTROMETER']['id'])
    args.display_id = int(config['DISPLAY']['id'])
    args.display_name = config['DISPLAY']['name']
    args.display_bits = int(config['DISPLAY']['nbits'])
    args.camera_id = int(config['CAMERA']['id'])

    lim1 = int(config['SPECTROMETER']['lambda1'])
    lim2 = int(config['SPECTROMETER']['lambda2'])
    args.lambda_limits = [lim1, lim2]

    # Now return arguments
    return args

if __name__ == '__main__':
    # First job is to simply create parser and extract configuration information
    args = create_config_and_parser()

    # Load device information
    device = utils.loadp('data/lcos_nir/device.pkl')[0]

    # Create wavelengths and get the Hadamard matrix
    wvl = np.linspace(args.lambda_limits[0], args.lambda_limits[1],
                      args.nbands)
    Hmat = lin.hadamard(args.nbands, dtype=np.float32)

    # Step 2 -- create a new camera
    camera = Hamamatsu.camera(args.camera_id)
    camera.initializeCamera()

    # Set exposure and other properties
    camera.mode = camera.MODE_EXTERNAL
    camera.setExposure(args.exposure)

    # Start acquisition process
    camera.camera.startAcquisition()

    # Create storage arrays
    H = camera.GetCCDHeight()
    W = camera.GetCCDWidth()

    data_p = np.zeros((H*W, args.nbands), dtype=np.float32)
    data_n = np.zeros((H*W, args.nbands), dtype=np.float32)

    img = np.zeros((H, W), dtype=np.float32)

    # Step 3 -- create a new display object
    display = hardware.Display(args.display_id, args.display_name)

    # Before step 4, create a saving folder and save arguments
    try:
        os.mkdir('experiments/%s'%args.experiment)
    except OSError:
        print('Directory exists. Skipping')

    # Now scan
    for idx in range(args.nbands):
        print('Pattern %d'%idx)
        profile = Hmat[idx, :]
        profile[profile < 0] = 0

        # Get display image for positive half
        imdisp = device_utils.get_coding_im(wvl, profile, device,
                                            display.shape, 'gamma')

        # And display it
        display.show(imdisp)

        # Scan averages
        img[:, :] = 0
        for iidx in range(args.nscans):
            img += camera.readCamera()[-1].astype(np.float32)

        img /= args.nscans

        data_p[:, idx] = img.reshape(-1)

        # Now for negative half
        if idx == 0:
            imdisp[:, :] = 0
        else:
            imdisp = device_utils.get_coding_im(wvl, 1-profile, device,
                                                display.shape, 'gamma')

        # And display it
        display.show(imdisp)

        # Scan averages
        img[:, :] = 0
        for iidx in range(args.nscans):
            img += camera.readCamera()[-1].astype(np.float32)

        img /= args.nscans

        data_n[:, idx] = img.reshape(-1)

    # Save data
    print('Saving data')
    utils.savep([Hmat, data_p, data_n],
                'experiments/%s/Hadamard_%d.pkl'%(args.experiment, args.nbands))

    # Close the display and spectrometer
    display.close()
    camera.camera.stopAcquisition()

