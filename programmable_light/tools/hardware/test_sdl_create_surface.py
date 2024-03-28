#!/usr/bin/env python3

import os
import sys
import pdb

# Set SDL DLL path
os.environ["PYSDL2_DLL_PATH"] = "libsdl/"

# Now import sdl2
import sdl2
import sdl2.ext

# Import numpy and matplotlib
import numpy as np
import matplotlib.pyplot as plt

# Import ctypes for passing pointers to SDL
import ctypes

def im2surf(im):
    '''
        Convert uint8 RGB image to SDL2 surface

        Inputs:
            im: ndarray with 3 dimensions (H, W, 3)

        Outputs:
            im_surf: SDL2 surface object
    '''
    [H, W, _] = im.shape
    
    # Flags for red green and blue channels
    rmask = 0x000000ff
    gmask = 0x0000ff00
    bmask = 0x00ff0000
    amask = 0x00000000

    # Compute pitch -- aka stride
    depth = 24
    pitch = 3*W

    # Convert to a c pointer
    data_ptr = ctypes.c_void_p(im.ctypes.data)

    # Now create the surface
    sdl2.SDL_ClearError()
    im_surf = sdl2.SDL_CreateRGBSurfaceFrom(data_ptr,
                                            ctypes.c_int(W),
                                            ctypes.c_int(H),
                                            ctypes.c_int(depth),
                                            ctypes.c_int(pitch),
                                            ctypes.c_uint32(rmask),
                                            ctypes.c_uint32(gmask),
                                            ctypes.c_uint32(bmask),
                                            ctypes.c_uint32(amask))
    
    print('Create surface: %s'%sdl2.SDL_GetError().decode())
    print(im_surf.contents.pixels)
    return im_surf

if __name__ == '__main__':
    # Testing constants
    screen_num = 0                              # Number of screen to use
    ntimes = 10                                 # Number of times to display
    delay = 10                                  # Delay between frames (ms)

    # Read image and format as uint8
    im = plt.imread('blank.png')
    im = (im*255).astype(np.uint8)[:, :, :3]

    # WARNING!! Convert to a contiguous array, else SDL2 won't work
    im = np.ascontiguousarray(im, dtype=np.uint8)

    # Initialize SDL video
    sdl2.SDL_ClearError()
    err = sdl2.SDL_Init(ctypes.c_uint32(sdl2.SDL_INIT_VIDEO))
    print('Initialize: %s; Err: %d'%(sdl2.SDL_GetError().decode(), err))

    # Get surface from image
    im_surf = im2surf(im)

    # Find number of displays and display bounds
    ndisplays = sdl2.SDL_GetNumVideoDisplays()
    bounds = sdl2.SDL_Rect()

    # Get display bounds for last display
    ret = sdl2.SDL_GetDisplayBounds(screen_num, bounds)

    # Create a window
    sdl2.SDL_ClearError()
    flags = sdl2.SDL_WINDOW_FULLSCREEN|sdl2.SDL_WINDOW_OPENGL
    window = sdl2.SDL_CreateWindow(r"Test Window".encode(),
                                   bounds.x,
                                   bounds.y,
                                   bounds.w,
                                   bounds.h,
                                   flags)
    print('Create window: %s'%sdl2.SDL_GetError().decode())

    # Create a GL Context
    sdl2.SDL_ClearError()
    glcontext = sdl2.SDL_GL_CreateContext(window);
    print('Create GL context: %s'%sdl2.SDL_GetError().decode())

    # Create a renderer for the texture surface
    sdl2.SDL_ClearError()
    renderer = sdl2.SDL_CreateRenderer(window,
                                       ctypes.c_int(-1),
                                       sdl2.SDL_RENDERER_PRESENTVSYNC)
    print('Create renderer: %s'%sdl2.SDL_GetError().decode())

    sdl2.SDL_ClearError()
    sdl2.SDL_GL_SetSwapInterval(0)
    print('Set adaptive swap: %s'%sdl2.SDL_GetError().decode())

    # Renderer reads from texture which is on GPU. So transfer the surface
    # on CPU to texture on GPU.
    sdl2.SDL_ClearError()
    im_texture = sdl2.SDL_CreateTextureFromSurface(renderer, im_surf)
    print('Texture from surface: %s'%sdl2.SDL_GetError().decode())

    # Make sure window was created
    if (window == None):
        print('Window could not be created')

    # Sweep through some random set of images
    for idx in range(1, bounds.h, 100):
        # Fun fact: We can directly play with pixel values here
        im[:, :] = 0
        im[:idx, :idx] = (np.random.rand(idx, idx, 3)*255).astype(np.uint8)

        # And just copy to texture
        im_texture = sdl2.SDL_CreateTextureFromSurface(renderer, im_surf)

        sdl2.SDL_RenderClear(renderer)
        sdl2.SDL_RenderCopy(renderer, im_texture, None, None)
        sdl2.SDL_RenderPresent(renderer)

        sdl2.SDL_Delay(delay)
        
    # Don, we can destroy window
    #sdl2.SDL_DestroyWindow(window)

    # And free surface
    #sdl2.SDL_FreeSurface(im_surf)

    # Finally quit
    #sdl2.SDL_Quit()
