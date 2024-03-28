#!/usr/bin/env python3

import os
import sys

# Set SDL DLL path
os.environ["PYSDL2_DLL_PATH"] = "libsdl/"

# Now import sdl2
import sdl2
import sdl2.ext

if __name__ == '__main__':
    screen_num = 0
    ntimes = 10

    # Initialize SDL video
    sdl2.SDL_ClearError()
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
    print(sdl2.SDL_GetError())

    # Load images
    blank_surf = sdl2.sdlimage.IMG_Load('blank.png'.encode())
    ramp_surf = sdl2.sdlimage.IMG_Load('ramp.png'.encode())

    # Find number of displays and display bounds
    ndisplays = sdl2.SDL_GetNumVideoDisplays()
    bounds = sdl2.SDL_Rect()

    # Get display bounds for last display
    ret = sdl2.SDL_GetDisplayBounds(screen_num, bounds)

    # Create a window
    window = sdl2.SDL_CreateWindow(r"Test Window".encode(),
                                   bounds.x,
                                   bounds.y,
                                   bounds.w,
                                   bounds.h,
                                   sdl2.SDL_WINDOW_FULLSCREEN)
    # Create a renderer
    renderer = sdl2.SDL_CreateRenderer(window, -1,
                                       sdl2.SDL_RENDERER_PRESENTVSYNC)

    # Set adaptive vsync
    sdl2.SDL_GL_SetSwapInterval(-1)

    # I am not quite sure why, but I need to create texture from surface
    blank_texture = sdl2.SDL_CreateTextureFromSurface(renderer, blank_surf)
    ramp_texture = sdl2.SDL_CreateTextureFromSurface(renderer, ramp_surf)

    # Make sure window was created
    if (window == None):
        print('Window could not be created')

    for idx in range(ntimes):
        # Blank
        sdl2.SDL_RenderClear(renderer)
        sdl2.SDL_RenderCopy(renderer, blank_texture, None, None)
        sdl2.SDL_RenderPresent(renderer)
        #sdl2.SDL_Delay(100)

        # Ramp
        sdl2.SDL_RenderClear(renderer)
        sdl2.SDL_RenderCopy(renderer, ramp_texture, None, None)
        sdl2.SDL_RenderPresent(renderer)
        #sdl2.SDL_Delay(100)

    # And then destroy window
    sdl2.SDL_DestroyWindow(window)

    sdl2.SDL_Quit()

