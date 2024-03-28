#!/usr/bin/env python

'''
    Central script to calibrate the spectrometer
'''

# System imports
import os
import sys
import argparse
import configparser
import pickle
import pdb

# Scientific computing
import numpy as np
from scipy import signal
from scipy import interpolate

# sklearn for RANSAC fitting
from sklearn import linear_model

# Plotting
import matplotlib.pyplot as plt

from modules import utils
from modules import coding
from modules import hyperspectral

def test_gamma(args, device, mode='gamma'):
    '''
        Calibrate gamma curve per wavelength
    '''
    # Load data
    fname = 'data/%s/%s_test.pkl'%(args.experiment, mode)
    args2, wvl, levels, data = utils.loadp(fname)

    linearity_snr = np.zeros(len(wvl))

    idx1 = abs(wvl - args.lambda_limits[0]).argmin()
    idx2 = abs(wvl - args.lambda_limits[1]).argmin()

    # Evaluate accuracy per wavelength
    for idx in range(len(wvl)):
        gc = data[:, idx]

        # Do a linear fit to data
        p = np.polyfit(levels, gc, 1)
        gc2 = np.polyval(p, levels)

        # And then evaluate accuracy
        linearity_snr[idx] = utils.rsnr(gc2, gc)

    # Plot accuracy as a function of wavelengths
    plt.plot(wvl[idx1:idx2], linearity_snr[idx1:idx2]);
    plt.xlabel('$\lambda$')
    plt.ylabel('SNR (dB)')
    plt.grid(True);
    plt.autoscale(tight=True)
    plt.show()

    pdb.set_trace()

def test_fwhm(args, device):
    '''
        Calibrate mapping between wavelengths and projector columns
    '''
    # Load data
    fname = 'data/%s/fwhm_test.pkl'%args.experiment
    args2, wvl, zero_data, data, test_wvl, slit_width = utils.loadp(fname)

    cwl_map = np.zeros((len(test_wvl), len(slit_width)))
    fwhm_map = np.zeros_like(cwl_map)

    for idx1 in range(len(test_wvl)):
        for idx2 in range(len(slit_width)):
            # Get rid of zero offset
            spec = data[:, idx1, idx2] - zero_data

            # Slightly smoothen the data
            spec = signal.convolve(spec, signal.hamming(5), 'same')

            [cwl, fwhm] = hyperspectral.fwhm(wvl, spec)
            cwl_map[idx1, idx2] = cwl
            fwhm_map[idx1, idx2] = fwhm

    pdb.set_trace()

def test_contrast(args):
    '''
        Compute contrast ratio of LCoS projector.
    '''
    # Load data
    fname = 'data/%s/contrast_test.pkl'%args.experiment
    args2, wvl, offset_data, zero_data, ones_data, img = utils.loadp(fname)

    # Median filter data
    offset_data = signal.medfilt(offset_data, 101)
    zero_data = signal.medfilt(zero_data, 101)
    ones_data = signal.medfilt(ones_data, 101)

    contrast = (ones_data - offset_data)/(zero_data - offset_data)

    # Hard code wavelength limits for now
    idx1 = abs(wvl - 600).argmin()
    idx2 = abs(wvl - 800).argmin()

    fig, ax = plt.subplots()
    lines = ax.plot(wvl[idx1:idx2], contrast[idx1:idx2])
    plt.xlabel('$\lambda$'); plt.ylabel('Contrast ratio')
    plt.grid(True)
    plt.autoscale(tight=True)
    mplcursors.cursor(lines)

    plt.show()

def test_profiles(args, device):
    '''
        Evaluate accuracy for arbitrary profile coding
    '''
    # Load data
    fname = 'data/%s/profiles_test.pkl'%args.experiment
    args2, wvl, target, zero_data, data_gamma, data_pwm = utils.loadp(fname)

    # Separate the two wavelength profiles
    twvl = wvl
    wvl = device.wvl

    # Subtract zero data
    data_gamma -= zero_data
    data_pwm -= zero_data

    pdb.set_trace()
    
    # Divide data by all ones, which is the first data point
    data_gamma /= data_gamma[0, :]
    data_pwm /= data_pwm[0, :]

    idx1 = abs(wvl - args.lambda_limits[0]).argmin()
    idx2 = abs(wvl - args.lambda_limits[1]).argmin()

    # Normalize data
    data_gamma = data_gamma/data_gamma[:, idx1:idx2].max(1).reshape(-1, 1)
    data_pwm = data_pwm/data_pwm[:, idx1:idx2].max(1).reshape(-1, 1)

    for idx in range(1, data_gamma.shape[0]):
        plt.clf()
        plt.plot(twvl, target[idx, :], 'k:')
        plt.plot(wvl[idx1:idx2], data_gamma[idx, idx1:idx2], 'r--')
        plt.plot(wvl[idx1:idx2], data_pwm[idx, idx1:idx2], 'b.-')
        plt.xlabel('$\lambda (nm)$')
        plt.legend(['Target', 'Gamma', 'PWM'])
        plt.grid(True)
        plt.autoscale(tight=True)
        plt.savefig('data/%s/profile%d.png'%(args.experiment, idx))
        plt.show()

def create_parser(config_name='config.ini'):
    '''
        Wrapper script to create argument parser.

        Inputs:
            config_name: Name used for configuration file.

        Outputs:
            args: Namespace object with experiment name
    '''
    # Create a new parser
    parser = argparse.ArgumentParser(description='Device calibration')

    # Name of experiment
    parser.add_argument('-e', '--experiment', action='store',
                        required=True, type=str, help='Experiment name')

    # Type of calibration. Defaults to all calibration
    parser.add_argument('-m', '--metric', action='store',
                        required=True, type=str, help='Metric type',
                        choices=['gamma', 'fwhm', 'contrast', 'pwm',
                                 'profiles'])

    # Now parse
    args = parser.parse_args()

    # We need configuration to get wavelength limits
    config = configparser.ConfigParser()
    config.read(config_name)

    lim1 = float(config['SPECTROMETER']['lambda1'])
    lim2 = float(config['SPECTROMETER']['lambda2'])

    args.lambda_limits = [lim1, lim2]

    return args

if __name__ == '__main__':
    # First job is to simply create parser and extract configuration information
    args = create_parser('config.ini')

    # Load device data
    device = utils.loadp('data/%s/device.pkl'%args.experiment)[0]

    # Now we are ready to calibrate
    if (args.metric == 'gamma') or (args.metric == 'pwm'):
        device = test_gamma(args, device, args.metric)
    elif args.metric == 'contrast':
        test_contrast(args)
    elif args.metric == 'fwhm':
        device = test_fwhm(args, device)
    elif args.metric == 'profiles':
        device = test_profiles(args, device)
