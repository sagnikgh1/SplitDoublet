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
import pdb
import time

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
    args.trigmode = int(config['CAMERA']['trigmode'])

    lim1 = int(config['SPECTROMETER']['lambda1'])
    lim2 = int(config['SPECTROMETER']['lambda2'])
    args.lambda_limits = [lim1, lim2]

    # Now return arguments
    return args

if __name__ == '__main__':
    # First job is to simply create parser and extract configuration information
    args = create_config_and_parser()

    # Load device information
    device = utils.loadp('data/lcos_nir2/device.pkl')[0]

    # Create wavelengths and get the Hadamard matrix
    wvl = np.linspace(args.lambda_limits[0], args.lambda_limits[1],
                      args.nbands)
    print(wvl)

    # Step 2 -- create a new camera
    camera = hardware.Camera(args.camera_id, args.exposure, args.trigmode)
    
    # Create storage arrays
    H = 2048
    W = 2048

    data = np.zeros((H*W, args.nbands), dtype=np.float32)

    profile =  np.zeros(args.nbands)
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
        profile[idx] = 1

        # Get display image for positive half
        imdisp = device_utils.get_coding_im(wvl, profile, device,
                                            display.shape, 'gamma')

        # And display it
        display.show(imdisp)

        # Discard one image and capture next
        img = camera.capture(args.nscans)

        # We instead acccept this.
        img = camera.capture(args.nscans)
        data[:, idx] = img.reshape(-1)

        profile[idx] = 0

    # Save data
    print('Saving data')
    utils.savep(data,
                'experiments/%s/Identity_%d.pkl'%(args.experiment, args.nbands))

    # Close the display and camera
    display.close()
    camera.close()
