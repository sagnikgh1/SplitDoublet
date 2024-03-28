#!/usr/bin/env python

'''
    Central script to capture data for evaluating metrics.
'''

# System imports
import os
import sys
import argparse
import configparser
import pickle

# Scientific computing
import numpy as np
from scipy import signal

# Plotting
import matplotlib.pyplot as plt

from modules import utils
from modules import hardware
from modules import coding
from modules import device_utils

def capture_gamma(args, spectrometer, display):
    '''
        test gamma curve calibration accuracy
    '''
    nlevels = pow(2, args.display_bits)
    levels = np.arange(0, nlevels-5, 10)

    # Load device data
    device = utils.loadp('data/%s/device.pkl'%args.experiment)[0]
    
    data = np.zeros((len(levels), len(spectrometer.wvl)))

    img = np.zeros(display.shape, dtype=np.uint8)

    # Then other data
    valid = (device.mapping > 0)*(device.mapping < display.shape[1])
    for idx in range(len(levels)):
        print('Intensity: %d'%levels[idx])

        # Get gamma corrected profile
        profile = device.gamma[levels[idx], :].reshape(-1, 1)
        img[:, device.mapping[valid].astype(int)] = profile[valid].reshape(-1)

        # Now display the corrected image
        display.show(img)
        spec = spectrometer.capture()
        data[idx, :] = spec

    # Save data
    wvl = spectrometer.wvl
    utils.savep([args, wvl, levels, data],
                'data/%s/gamma_test.pkl'%args.experiment)
    
def capture_contrast(args, spectrometer, display):
    '''
        Capture contrast ratio data using calibrated gamma
    '''
    # First, block light and capture data
    input('Block light and press a key')
    offset_data = spectrometer.capture()

    input('Remove block and press a key')

    # Load device
    device = utils.loadp('data/%s/device.pkl'%args.experiment)[0]

    # Zero data
    print('All zeros data')
    display.show(np.zeros(display.shape, dtype=np.uint8))
    zero_data = spectrometer.capture()

    # Create gamma corrected all ones image
    img = np.zeros(display.shape, dtype=np.uint8)

    valid = (device.mapping > 0)*(device.mapping < display.shape[1])

    profile = device.gamma[-1, :].reshape(-1, 1)
    img[:, device.mapping[valid].astype(int)] = profile[valid].reshape(-1)

    # Ones data
    print('All ones data')
    display.show(img)
    ones_data = spectrometer.capture()

    # Save data
    wvl = spectrometer.wvl
    utils.savep([args, wvl, offset_data, zero_data, ones_data, img],
                'data/%s/contrast_test.pkl'%args.experiment)

def capture_pwm(args, spectrometer, display):
    '''
        Capture arbitrary gray coding using spatial PWM.
    '''
    nvals = 100
    H = display.shape[0]

    # Load device data
    device = utils.loadp('data/%s/device.pkl'%args.experiment)[0]

    # Get gamma corrected profile for maximum intensity
    valid = (device.mapping > 0)*(device.mapping < display.shape[1])
    profile = device.gamma[255, :].reshape(-1, 1)
    profile = profile[valid].reshape(-1)
    
    # Place holder image
    img = np.zeros(display.shape, dtype=np.uint8)

    levels = np.linspace(0, H//2, nvals).astype(int)
    data = np.zeros((nvals, len(spectrometer.wvl)))

    for idx in range(nvals):
        print('Level: %d'%idx)
        img[H//2-idx:H//2+idx, device.mapping[valid].astype(int)] = profile
        display.show(img)
        data[idx, :] = spectrometer.capture()

    # Save data
    wvl = spectrometer.wvl
    utils.savep([args, wvl, levels, data],
                'data/%s/pwm_test.pkl'%args.experiment)

def capture_fwhm(args, spectrometer, display):
    '''
        Estimate FWHM by varying width of 'slit' till the FWHM value keeps
        reducing. Do so for a select set of wavelengths. This will also
        verify accuracy of mapping between wavelengths and projector columns
    '''
    # Some testing constants
    ntest = 20                          # Number of test wavelengths
    max_width = 30                      # Maximum 'slit' width
    
    # Load device data
    device = utils.loadp('data/%s/device.pkl'%args.experiment)[0]
    wvl = spectrometer.wvl
    
    # Zero data
    print('All zeros data')
    display.show(np.zeros(display.shape, dtype=np.uint8))
    zero_data = spectrometer.capture()

    # Find wavelength limits
    idx1 = abs(spectrometer.wvl - args.lambda_limits[0]).argmin()
    idx2 = abs(spectrometer.wvl - args.lambda_limits[1]).argmin()

    # Probe the middle most wavelength
    test_wvl = np.arange(args.lambda_limits[0], args.lambda_limits[1], ntest)
    slit_width = np.arange(1, max_width, 2)

    data = np.zeros((len(spectrometer.wvl), ntest, max_width//2))
    imdisp = np.zeros(display.shape, dtype=np.uint8)
    
    for wvl_idx in range(len(test_wvl)):
        print('Wavelength: %dnm'%test_wvl[wvl_idx])

        # Compute corresponding projector index
        lmb = test_wvl[wvl_idx]
        idx = abs(wvl - lmb).argmin()
        proj_idx = int(device.mapping[idx])
        
        for w_idx in range(len(slit_width)):
            print('\tSlit width: %dpx'%slit_width[w_idx])
            w = slit_width[w_idx]//2

            # Create slit image
            imdisp[:, :] = 0
            imdisp[:, proj_idx-w:proj_idx+w] = 255

            display.show(imdisp)
            spec = spectrometer.capture()

            data[:, wvl_idx, w_idx] = spec
            
    # Save data
    utils.savep([args, wvl, zero_data, data, test_wvl, slit_width],
                'data/%s/fwhm_test.pkl'%args.experiment)

def capture_profiles(args, spectrometer, device):
    '''
        Capture spectra with arbitrary coding.
    '''
    # Some testing constants
    nwvl = 100                          # Number of test wavelengths

    # Create wavelengths
    wvl = np.linspace(args.lambda_limits[0], args.lambda_limits[1], nwvl)

    # Create some profiles
    target_profiles = np.zeros((6, nwvl))

    # 1 -- all ones
    target_profiles[0, :] = 1

    # 2 -- Increasing ramp
    target_profiles[1, :] = np.linspace(0, 1, nwvl)

    # 3 -- Decreasing ramp
    target_profiles[2, :] = np.linspace(1, 0, nwvl)

    # 4 -- Triangle
    target_profiles[3, :nwvl//2] = np.linspace(0, 1, nwvl//2)
    target_profiles[3, nwvl//2:] = np.linspace(1, 0, nwvl//2)

    # 5 -- High variance gaussian
    target_profiles[4, :] = signal.gaussian(nwvl, 20)

    # 6 -- Two low variance gaussians
    target_profiles[5, :nwvl//2] = signal.gaussian(nwvl//2, 4)
    target_profiles[5, nwvl//2:] = 0.5*signal.gaussian(nwvl//2, 4)

    # We will capture both gamma-based coding and PWM coding
    data_gamma = np.zeros((6, len(spectrometer.wvl)))
    data_pwm = np.zeros((6, len(spectrometer.wvl)))
    
    # Load device data
    device = utils.loadp('data/%s/device.pkl'%args.experiment)[0]
    spectrometer.wvl
    
    # Zero data
    print('All zeros data')
    display.show(np.zeros(display.shape, dtype=np.uint8))
    zero_data = spectrometer.capture()

    for idx in range(6):
        print('Profile %d'%idx)
        # First -- gamma
        imdisp = device_utils.get_coding_im(wvl, target_profiles[idx, :],
                                            device, display.shape, 'gamma')
        display.show(imdisp)
        data_gamma[idx, :] = spectrometer.capture()

        # Second -- PWM
        imdisp = device_utils.get_coding_im(wvl, target_profiles[idx, :],
                                            device, display.shape, 'pwm')
        display.show(imdisp)
        data_pwm[idx, :] = spectrometer.capture()
        
    # Save
    utils.savep([args, wvl, target_profiles, zero_data, data_gamma, data_pwm],
                'data/%s/profiles_test.pkl'%args.experiment)
                
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
    parser.add_argument('-m', '--metric', action='store', 
                        required=True, type=str, help='Metric type',
                        choices=['mapping', 'gamma', 'contrast', 'fwhm',
                                 'pwm', 'profiles'])

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

    args.lambda_limits = [0, 0]
    args.lambda_limits[0] = int(config['SPECTROMETER']['lambda1'])
    args.lambda_limits[1] = int(config['SPECTROMETER']['lambda2'])

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
    if args.metric == 'gamma':
        capture_gamma(args, spectrometer, display)
    elif args.metric == 'contrast':
        capture_contrast(args, spectrometer, display)
    elif args.metric == 'fwhm':
        capture_fwhm(args, spectrometer, display)
    elif args.metric == 'pwm':
        capture_pwm(args, spectrometer, display)
    elif args.metric == 'profiles':
        capture_profiles(args, spectrometer, display)

    # Close the display and spectrometer
    display.close()
    spectrometer.close()
