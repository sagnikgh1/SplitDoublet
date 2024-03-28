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
from skimage.transform import rotate
from scipy import signal

import matplotlib.pyplot as plt

# Hacky way of getting SDL2 path
from modules import hardware
from modules import coding
from modules import utils

def grab_im(camera, port, trig, navg, ndrops=1):
    '''
        Function to trigger and capture images

        Inputs:
            camera: Hamamatsu camera object
            port: Serial port to control Arduino
            trig: Character to send for firing a trigger
            navg: Number of averages
            ndrops: Number of captures to discard

        Outputs:
            im: Captured image
    '''
    # First keep discarding
    for idx in range(ndrops):
        port.write(trig.encode())
        discard = camera.capture(1)

    # Now capture diligently
    im = 0
    for idx in range(navg):
        # Trigger
        port.write(trig.encode())

        # Capture
        im += camera.capture(1).astype(np.float32)

    im /= navg

    return im

def grab_im_software_trigger(camera, navg, ndrops=1):
    '''
        Function to trigger and capture images

        Inputs:
            camera: Hamamatsu camera object
            port: Serial port to control Arduino
            trig: Character to send for firing a trigger
            navg: Number of averages
            ndrops: Number of captures to discard

        Outputs:
            im: Captured image
    '''
    # First keep discarding
    for idx in range(ndrops):
        camera.fire_trigger()
        discard = camera.capture(1)

    # Now capture diligently
    im = 0
    for idx in range(navg):
        # Trigger
        camera.fire_trigger()
        # Capture
        im += camera.capture(1).astype(np.float32)

    im /= navg

    return im


def get_setup_profile(profile, wvl, target_wvl, code):
    '''
        Compute a profile that can be displayed in the optical setup, by
        interpolating to calibration wavelength and blurring with code.

        Inputs:
            profile: Desired coding profile
            wvl: Wavelengths where profile is defined
            target_wvl: Setup wavelengths
            code: spectral blur code defined on the same domain as target_wvl

        Outputs:
            target_profile: Interpolated and blurred spectral profile
    '''
    # Step 1 -- interpolate
    f = interpolate.interp1d(np.linspace(0, 1, wvl.size),
                                 profile, 'nearest',
                                 bounds_error=False,
                                 fill_value=0)
    target_profile = f(np.linspace(0, 1, target_wvl.size)).reshape(1, -1)

    # Step 2 -- blur
    target_blurred = signal.convolve()

def get_filter_im(profile, camera, display, port, navg, imsize, up_min, up_max,
                  lo_min, lo_max, theta=0, method='kron', debug=False,
                  zero_im=0):
    '''
        Function to filter an HSI and get image for arbitrary wavelength
        profiles.

        Inputs:
            profile: Spectral profile to filter HSI with
            camera: HCamera instance to control Hamamatsu camera
            display: Display object
            port: Serial port object
            navg: Number of camera image averages
            imsize: Size of display
            up_min: Upward minimum index from which coding will start
            up_max: Upward maximum index till which coding exists
            lo_min: Downward minimum
            lo_max: Downward maximum
            theta: Angle of roration of image
            method: 'kron' or 'interp'. Default is 'kron'
            debug: If True, return positive and negative images. Default is
                False
            zero_im: All zeros image to correct bias

        Outputs:
            filtered_im: Single image as a result of spectral filtering
    '''
    # First get positive and negative patterns
    [impos, imneg, pval, nval] = get_posneg_im(profile, imsize, up_min, up_max,
                                               lo_min, lo_max, theta, method)

    # Then display positive pattern, capture an image
    display.showData(impos)
    campos = grab_im(camera, port, 't', navg, 2)

    # Finally display negative pattern and capture an image
    if nval != 0:
        # Capture this image only if the pattern has negative part, else skip
        display.showData(imneg)
        camneg = grab_im(camera, port, 't', navg, 2)
    else:
        camneg = 0

    # Compute the final answer
    filtered_im = (campos-zero_im)*pval - (camneg-zero_im)*nval

    if debug:
        return filtered_im, campos, camneg

    return filtered_im

def get_posneg_im(profile, imsize, up_min, up_max, lo_min, lo_max,
                  theta=0, method='kron'):
    '''
        Function to get positive and negative display images for a given
        spectral profile. The function calls get_coding_im for positive
        and negative halves separately.

        Inputs:
            profile: Profile to create image for
            imsize: Two-tuple of SLM size
            up_min: Upward minimum index from which coding will start
            up_max: Upward maximum index till which coding exists
            lo_min: Downward minimum
            lo_max: Downward maximum
            theta: Angle of roration of image
            method: 'kron' or 'interp'. Default is 'kron'

        Outputs:
            impos: Display image for positive part
            imneg: Display image for negative part
            pval: Maximum value of positive part
            nval: Maximum value of negative part
    '''
    # Create binary mask for positive values
    pmask = np.copy(profile)
    pmask[pmask < 0] = 0
    pmask[pmask > 0] = 1

    pval = profile[profile > 0].max()

    if profile.min() > 0:
        nval = 0
    else:
        nval = (-profile[profile < 0]).max()

    impos = get_coding_im(profile*pmask, imsize, up_min, up_max,
                          lo_min, lo_max, theta, method)
    imneg = get_coding_im(profile*(pmask-1), imsize, up_min, up_max,
                          lo_min, lo_max, theta, method)
    
    return impos, imneg, pval, nval

def get_coding_im(profile, imsize, up_min, up_max, lo_min, lo_max,
                  theta=0, method='kron'):
    '''
        Function to get display image for a given spectral profile using
        spatial PWM.

        Inputs:
            profile: Profile to create image for
            imsize: Two-tuple of SLM size
            up_min: Upward minimum index from which coding will start
            up_max: Upward maximum index till which coding exists
            lo_min: Downward minimum
            lo_max: Downward maximum
            theta: Angle of roration of image
            method: 'kron' or 'interp'. Default is 'kron'

        Outputs:
            imdisp: Image to project on LCoS to achieve desired coding.
    '''
    [H, W] = imsize
    nbands = profile.size

    if method == 'interp':
        # First step, interpolate to device wavelengths
        f = interpolate.interp1d(np.linspace(0, 1, nbands),
                                 profile, 'nearest',
                                 bounds_error=False,
                                 fill_value=0)
        profile = f(np.linspace(0, 1, W)).reshape(1, -1)
        
    else:
        scale = np.ceil(W/nbands).astype(int)
        scaler = np.ones((1, scale))
        profile = np.kron(profile.reshape(1, -1), scaler)[:, :W]

    # Careful when profile is all zeros.
    if profile.max() != 0:
        profile = (profile/profile.max()).reshape(-1)
        
    imdisp = np.zeros(imsize, dtype=np.uint8)

    # Separately create profiles for top and bottom half
    profile_up = (up_min + (up_max - up_min)*profile).astype(int).reshape(-1)
    profile_lo = (lo_min + (lo_max - lo_min)*profile).astype(int).reshape(-1)

    # Now code each column individually
    for idx in range(W):
        imdisp[H//2-profile_up[idx]:H//2+profile_lo[idx], idx] = 255

    # Finally rotate the image to correct for SLM rotation w.r.t spectrum
    if abs(theta) > 1e-2:
        imdisp = rotate(imdisp, theta, clip=True, preserve_range=True)

    return imdisp

def transfer_filter(profile, wavelengths, device_wvl, device_code, wconst,
                    device_response):
    '''
        Transfer filter from spectrometer (or any other source) to device.

        Inputs:
            profile: Target spectral filter
            wavelengths: Wavelengths on which the profile is defined
            device_wvl: Wavelength array for the device
            device_code: Coded aperture for the device
            wconst: Wiener filter constant
            device_response: Spectral response of device

        Outputs:
            transfered_profile: Profile that should be displayed on
            the device
    '''

    # First step, interpolate to device wavelengths
    f = interpolate.interp1d(wavelengths.ravel(),
                             profile.ravel(), 'linear',
                             bounds_error=False,
                             fill_value=0)
    device_profile = f(device_wvl.ravel()).reshape(1, -1)

    # Next, *divide* by response -- then the multiplication by device will
    # ensure the reflectance is preserved
    device_profile = device_profile/(1e-2 + device_response)

    # Now deconvolve
    profile_deconv = utils.deconvwnr1(device_profile, device_code[:, ::-1],
                                      wconst)

    # Finally return
    return profile_deconv
    

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
