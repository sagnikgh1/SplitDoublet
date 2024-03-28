#!/usr/bin/env python

'''
  Modules to handle coding utilities such as binary coding, and gray coding
'''

import numpy as np
import scipy.linalg as lin

def next_pow2(x):
    '''
        Compute the next power of two for a given scalar.

        Inputs:
          x: input scalar

        Outputs:
          x2: Next highest power of two
    '''
    logx = np.log2(x)

    return int(pow(2, np.ceil(logx)))

def hadamard_code(H, W, col=True):
    '''
        Get display images for row/column hadamard coding

        Inputs:
            H: Height of display
            W: Width of display
            col: If true (default), code the columns, else code rows.

        Outputs:
            codes: H x W x ncodes tensor with binary codes.
            Hmat: The hadamard matrix that generated codes
    '''
    if col is False:
        [H, W] = [W, H]

    # Find next power of two for number of columns
    W2 = next_pow2(W)
    ncodes = int(np.log2(W2))

    codes = np.zeros((H, W2, ncodes))

    # Get a Hadamard matrix
    Hmat = lin.hadamard(W2, dtype=np.float32)
    Hmat[Hmat == -1] = 0

    for idx in range(ncodes):
        row = Hmat[idx, :].reshape(1, -1)

        codes[:, :, idx] = np.dot(np.ones((H, 1)), row)

    codes = codes[:, :W, :]

    if col is False:
        codes = np.transpose(codes, (1, 0, 2))

    return codes, Hmat

def bincode(H, W, col=True):
    '''
        Get display images for binary coded correspondences

        Inputs:
            H: Height of display
            W: Width of display
            col: If true (default), code the columns, else code rows.

        Outputs:
            codes: HxWxncodes tensor with binary codes.
    '''
    if col is False:
        [H, W] = [W, H]

    # Find next power of two for number of columns
    W2 = next_pow2(W)
    ncodes = int(np.log2(W2))

    codes = np.zeros((H, W2, ncodes))

    for idx in range(ncodes):
        dim = int(W2/pow(2, idx+1))
        white = np.ones((1, dim))
        black = np.zeros((1, dim))

        row = np.hstack([black, white])
        row = np.tile(row, [1, pow(2, idx)])

        codes[:, :, idx] = np.dot(np.ones((H, 1)), row)

    codes = codes[:, :W, :]

    if col is False:
        codes = np.transpose(codes, (1, 0, 2))

    return codes

def bindecode(data, ref):
    '''
        Decode binary coded data to get correspondences

        Input:
            data: Captured data that is binary coded
            ref: All ones reference image

        Outputs:
            mapping: Map with individual pixel locations
            binary_data: Thresholded data for reference
    '''
    [H, W, nbits] = data.shape
    mapping = np.zeros((H, W))
    binary_data = np.zeros_like(data)

    for idx in range(nbits):
        binary_im = np.zeros((H, W))
        data_im = data[:, :, idx]

        # Sanity checking to zero out non-measured pixels
        data_im[ref == 0] = 0

        # Now threshold
        binary_im[data_im > 0] = 1

        # Then add to map
        mapping += binary_im*pow(2, nbits - idx - 1)

        binary_data[:, :, idx] = binary_im

    return mapping, binary_data

def checker(H, W, checker_size):
    '''
        Create a 2D checker board pattern.

        Inputs:
            H, W: Dimensions of checker image
            checker_size: Size of each black/white box.

        Outputs:
            checker_img: Checker image.
    '''
    nH = int(0.5*np.ceil(H/checker_size))
    nW = int(0.5*np.ceil(W/checker_size))

    imunit = np.zeros((2*checker_size, 2*checker_size))
    imunit[:checker_size, :checker_size] = 1
    imunit[checker_size:, checker_size:] = 1

    checker_img = np.tile(imunit, [nH+1, nW+1])

    return checker_img[:H, :W]

    
    
