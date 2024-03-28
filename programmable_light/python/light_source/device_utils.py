#!/usr/bin/env python

'''
    Module for programmable-light functions.
'''

# System imports
import os
import sys
import pdb

# Numpy-ish imports
import numpy as np
from scipy import interpolate

# Hacky way of getting SDL2 path
from modules import hardware
from modules import coding
from modules import utils

def get_coding_im(wvl, profile, device, display_shape, mode='pwm'):
    '''
        Function to get display image for a given spectral profile.

        Inputs:
            wvl: Wavelengths where profile is defined
            profile: Desired profile
            device: Device structure with calibration parameters
            display_shape: Two-tuple with size of display
            mode: 'pwm' does spatial PWM and 'gamma' uses wavelength-dependent
                gamma.

        Outputs:
            imdisp: Image to project on LCoS to achieve desired coding.
    '''
    # First step, interpolate to device wavelengths
    f = interpolate.interp1d(wvl, profile, 'nearest',
                             bounds_error=False,
                             fill_value=0)
    profile = f(device.wvl)
    profile = profile/profile.max()

    imdisp = np.zeros(display_shape, dtype=np.uint8)

    # Sanity check -- make sure indices are within device size
    H, W = display_shape
    valid = (device.mapping > 0)*(device.mapping < W)

    # Now we decide how to code -- PWM or gamma
    if mode == 'pwm':
        profile = (H*profile).astype(int)//2

        # Get the profile for maximum intensity
        max_profile = device.gamma[-1, :].astype(np.uint8)

        # For now, brute force and assign values
        for idx in range(len(device.wvl)):
            if valid[idx]:
                imdisp[H//2-profile[idx]:H//2+profile[idx],
                       device.mapping[idx].astype(int)] = max_profile[idx]

    elif mode == 'gamma':
        profile = (255*profile).astype(int)
        row = device.gamma[profile, np.arange(len(device.wvl))].reshape(-1)
        imdisp[:, device.mapping[valid].astype(int)] = row[valid]

    return imdisp

def diffraction_fix(im, minlim, maxlim):
    '''
        Fix a pupil plane pattern by setting central band to all ones to avoid
        diffraction.

        Inputs:
            im: Input image pattern to fix
            minlim: Minimum rows from center of image which is set to one
            maxlim: Maximum rows after which it's all zeros

        Outputs:
            imfixed: Fixed image to avoid diffraction
    '''
    imfixed = np.copy(im)
    H, W = im.shape

    if im.dtype == np.uint8:
        maxval = 255
    else:
        maxval = 1

    imfixed[H//2-minlim:H//2+minlim, :] = maxval
    imfixed[H//2+maxlim:, :] = 0
    imfixed[:H//2-maxlim, :] = 0

    return imfixed
