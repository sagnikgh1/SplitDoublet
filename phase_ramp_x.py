 # System imports
import os
import sys
import time
import argparse
from tqdm import tqdm

# Scientific computing
import numpy as np

# Vision
import cv2

# Our own imports
sys.path.append('./programmable_light/python')
from modules import hardware

def parse_args(config_name="config.ini"):
    """
        Wrapper script to generate system configuration from config file and
        input arguments.

        Inputs:
            config_name: Name used for configuration file.

        Outputs:
            args: Namespace object with experiment and hardware properties
    """
    # Create a new parser
    parser = argparse.ArgumentParser(description='Calibration data capture')
                
    # Exposure time of camera in ms
    parser.add_argument('-i', '--exposure', action='store', type=float,
                        default=16.666, help='Exposure time (ms)')
                        
    # Gain in dB
    parser.add_argument('-g', '--gain', action='store', type=float,
                        default=29, help='Gain in dB')


    # Number of scans to average
    parser.add_argument('-n', '--nscans', action='store', type=int,
                        default=1, help='Number of scans')
                        
                        
    # Trigger pin. -1 to disable
    parser.add_argument('-t', '--trigger', action='store', type=int,
                        default=-1, help='Trigger pin (-1 to disable)')
    
    # Camera id
    parser.add_argument('-c', '--cam_id', default=0, type=int,
                        help='camera id')
    
    # Display id SLM
    parser.add_argument('-d1', '--display_id_slm', default=1, type=int,
                        help='Display id SLM')
    
    # Display name SLM
    parser.add_argument('-n1', '--display_name_slm', default='SLM Window',
                        help='Display name SLM')
    
    # Display id
    parser.add_argument('-d2', '--display_id_oled', default=2, type=int,
                        help='Display id')
    
    # Display name
    parser.add_argument('-n2', '--display_name_oled', default='OLED Window',
                        help='Display name OLED')
    
    # Dot width
    parser.add_argument('-w', '--width', default=5,
                        help='Dot width')
    
    
    # Now parse
    args = parser.parse_args()

    # Now return arguments
    return args

def phase_ramp_vid(args):
    """
    Function to obtain and plot SLM calibration curve
    """
    # Create a new SpinView camera object
    camera = hardware.SPCamera(args.cam_id, args.exposure,
                                     gain=args.gain, trig_pin=args.trigger,
                                     isrgb=False, israw=True)
    
    # Create a new display for SLM
    display1 = hardware.Display(args.display_id_slm, args.display_name_slm)
    Hd1, Wd1 = display1.shape

    # Create a new display for OLED
    display2 = hardware.Display(args.display_id_oled, args.display_name_oled)
    Hd2, Wd2 = display2.shape

    pattern = np.zeros((Hd2,Wd2))
    pattern[Hd2//2-args.width:Hd2//2+args.width,Wd2//2-args.width:Wd2//2+args.width] = 255
    pattern = np.stack([pattern]*3, axis=2)
    pattern[:,:,1:] = 0

    oled_texture = display2.create_texture_from_numpy(pattern)
    display2.render(oled_texture)
    time.sleep(0.2)

    x = np.arange(Wd1)
    y = np.arange(Hd1)
    xv, yv = np.meshgrid(x, y, indexing='xy')
    
    num = 0
    for i in tqdm(np.arange(0,0.5,0.05)):
        x_ramp = np.mod(xv*i, 1)*255
        
        slm_texture = display1.create_texture_from_numpy(np.round(x_ramp).astype(np.uint8))
        display1.render(slm_texture)
        time.sleep(0.2)
        img = camera.capture()
        cv2.imwrite(f"captured_ims/phase_ramp_x_vid/{num:03}.png", img)
        num+=1

    camera.close()
    display1.close()
    display2.close()

if __name__=="__main__":
    args = parse_args()
    phase_ramp_vid(args)