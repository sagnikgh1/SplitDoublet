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

def calib_gamma(args, device):
    '''
        Calibrate gamma curve per wavelength
    '''
    # Load data
    fname = 'data/%s/gamma_data.pkl'%args.experiment
    args2, wvl, offset_data, data = utils.loadp(fname)

    # Subtract offset data
    data -= offset_data

    # Smoothen the spectra a bit
    for idx in range(data.shape[0]):
        spec = data[idx, :]
        spec = signal.convolve(spec, signal.hamming(5), 'same')
        data[idx, :] = spec

    nlevels = pow(2, args2.display_bits)
    device.gamma = np.zeros((nlevels, len(wvl)), dtype=np.uint8)

    for idx in range(len(wvl)):
        # Extract a curve
        gc = data[:, idx]
        gc = gc/gc.max()

        # Fit a 5-th degree poly
        p = np.polyfit(np.arange(nlevels), gc.reshape(-1), 10)
        gc = np.polyval(p, np.arange(nlevels))
        gc[gc < 0] = 0
        gc[gc >= 1] = 1

        # Find minimum and maximum indices
        idx1 = abs(gc).argmin()
        idx2 = abs(gc).argmax()

        idxmin = min(idx1, idx2)
        idxmax = max(idx1, idx2)

        # Now we can map
        #pdb.set_trace()
        gcinv = np.zeros(nlevels, dtype=np.uint8)
        gcinv[(gc[idxmin:idxmax]*255).astype(int)] = np.arange(idxmin, idxmax)

        # Interpolate unknown values
        idxnz = np.where(gcinv != 0)
        idxz = np.where(gcinv == 0)

        if len(idxnz[0]) > 2:
            f = interpolate.interp1d(idxnz[0], gcinv[idxnz], 'linear',
                                     bounds_error=False,
                                     fill_value=(gcinv.min(), gcinv.max()))
            gcinv = f(np.arange(nlevels))
            device.gamma[:, idx] = gcinv

    plt.imshow(device.gamma); plt.show()

    return device

def calib_mapping(args, device):
    '''
        Calibrate mapping between wavelengths and projector columns
    '''
    # Load data
    fname = 'data/%s/mapping_data.pkl'%args.experiment
    args2, wvl, zero_data, ones_data, data_p, data_n = utils.loadp(fname)

    # Create data for finding correspondences
    data = data_p - data_n
    ref = ones_data - zero_data

    # Now find mapping and binary images
    mapping, bin_img = coding.bindecode(data.T[:, np.newaxis, :],
                                        ref[:, np.newaxis])
    mapping = signal.medfilt(mapping.reshape(-1), 5)

    idx1 = abs(wvl - args.lambda_limits[0]).argmin()
    idx2 = abs(wvl - args.lambda_limits[1]).argmin()

    p = np.polyfit(wvl[idx1:idx2], mapping[idx1:idx2], 2)
    device.mapping = np.polyval(p, wvl)

    device.wvl = wvl
    device.limits = args.lambda_limits

    plt.plot(wvl[idx1:idx2], mapping[idx1:idx2], 'yx')
    plt.plot(wvl[idx1:idx2], device.mapping[idx1:idx2])
    plt.xlabel('$\lambda$')
    plt.ylabel('Projector index')
    plt.legend(['True points', 'Polyfit points'])
    plt.grid(True)
    plt.show()

    return device

def calib_contrast(args):
    '''
        Compute contrast ratio of LCoS projector.
    '''
    # Load data
    fname = 'data/%s/contrast_data.pkl'%args.experiment
    args2, wvl, offset_data, zero_data, ones_data = utils.loadp(fname)

    # Median filter data
    offset_data = signal.medfilt(offset_data, 101)
    zero_data = signal.medfilt(zero_data, 101)
    ones_data = signal.medfilt(ones_data, 101)

    contrast = (ones_data - offset_data)/(zero_data - offset_data)

    # Hard code wavelength limits for now
    idx1 = abs(wvl - 600).argmin()
    idx2 = abs(wvl - 900).argmin()

    plt.plot(wvl[idx1:idx2], contrast[idx1:idx2])
    plt.xlabel('$\lambda$'); plt.ylabel('Contrast ratio')
    plt.grid(True)
    plt.autoscale(tight=True)

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
    parser.add_argument('-c', '--calibrate', action='store',
                        default='all', type=str, help='Calibration type',
                        choices=['gamma', 'contrast', 'mapping', 'all'])

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

    # See if there is an existing device file
    if not os.path.isfile('data/%s/device.pkl'%args.experiment):
        # Create a new device file
        print('Creating new device structure')
        device = argparse.Namespace()
        device.wvl = None
        device.limits = None
        device.mapping = None
        device.gamma = None
        device.light = None
    else:
        device = utils.loadp('data/%s/device.pkl'%args.experiment)[0]

    # Now we are ready to calibrate
    if args.calibrate == 'gamma':
        device = calib_gamma(args, device)
    elif args.calibrate == 'contrast':
        calib_contrast(args)
    elif args.calibrate == 'mapping':
        device = calib_mapping(args, device)
    else:
        device = calib_gamma(args, device)
        device = calib_mapping(args, device)
        calib_contrast(args)

    # Now dump the device object
    utils.savep([device], 'data/%s/device.pkl'%args.experiment)
