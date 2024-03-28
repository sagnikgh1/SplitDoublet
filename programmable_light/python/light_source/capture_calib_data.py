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

# Plotting
import matplotlib.pyplot as plt

from modules import utils
from modules import hardware
from modules import coding

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

    # Type of calibration
    parser.add_argument('-c', '--calibrate', action='store', 
                        required=True, type=str, help='Calibration type',
                        choices=['gamma', 'contrast', 'mapping'])

    # Exposure time of spectrometer
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

    # Now return arguments
    return args

if __name__ == '__main__':
    # First job is to simply create parser and extract configuration information
    args = create_config_and_parser()

    # Step 2 -- create a new spectrometer
    spectrometer = hardware.Spectrometer(args.spectrometer_id,
                                         args.exposure,
                                         args.nscans)
    # Step 3 -- create a new display object
    display = hardware.Display(args.display_id, args.display_name)

    # Before step 4, create a saving folder and save arguments
    try:
        os.mkdir('data/%s'%args.experiment)
    except OSError:
        print('Directory exists. Skipping')

    # Step 4 -- find out which function to call
    if args.calibrate == 'gamma':
        capture_gamma(args, spectrometer, display)
    elif args.calibrate == 'mapping':
        capture_mapping(args, spectrometer, display)
    elif args.calibrate == 'contrast':
        capture_contrast(args, spectrometer, display)

    # Close the display and spectrometer
    display.close()
    spectrometer.close()

