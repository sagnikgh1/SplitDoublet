 # System imports
import os
import sys
import time
import argparse
from tqdm import tqdm

# Scientific computing
import numpy as np

# Plotting
import matplotlib.pyplot as plt

# Our own imports
sys.path.append('../programmable_light/python')
from modules import hardware

def parse_args():
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

    # Name of experiment
    parser.add_argument('-e', '--experiment', action='store',
                        required=True, type=str, help='Experiment name')

    # Name of Save File
    parser.add_argument('-f', '--filename', action='store', type=str,
                        default='FullSLMScan.mat', help='File name')
                        
    # Exposure time of camera in ms
    parser.add_argument('-i', '--exposure', action='store', type=float,
                        default=16.666, help='Exposure time (ms)')

    # Gain in dB
    parser.add_argument('-g', '--gain', action='store', type=float,
                        default=0, help='Gain in dB')


    # Number of scans to average
    parser.add_argument('-n', '--nscans', action='store', type=int,
                        default=1, help='Number of scans')
                        
                        
    # Trigger pin. -1 to disable
    parser.add_argument('-t', '--trigger', action='store', type=int,
                        default=-1, help='Trigger pin (-1 to disable)')
    
    # Camera id
    parser.add_argument('-c', '--cam_id', default=0, type=int,
                        help='Camera id')
    
    # Display id
    parser.add_argument('-d', '--disp_id', default=1, type=int,
                        help='Display id')
    
    # Display name
    parser.add_argument('-w', '--disp_name', default='SLM Window',
                        help='Display name')

    
    # Now parse
    args = parser.parse_args()

    # Now return arguments
    return args

def get_calibration_curve(args):
    """
    Function to obtain and plot SLM calibration curve
    """
    # Create a new SpinView camera object
    camera = hardware.SPCamera(args.cam_id, args.exposure,
                                     gain=args.gain, trig_pin=args.trigger,
                                     isrgb=False, israw=True)
    
    # Create a new display
    display = hardware.Display(args.display_id, args.display_name)
    Hd, Wd = display.shape

    out_vals = []

    for i in tqdm(range(256)):
        texture = display.create_texture_from_numpy((np.ones((Hd,Wd))*i).astype(np.uint8))
        display.render(texture)
        if i==0:
            time.sleep(0.8)
        time.sleep(0.2)

        img = camera.capture(args.nscans)
        out_vals.append(np.mean(img))

    # Normalize to -1 to 1
    out_vals = np.array(out_vals)
    out_vals = out_vals - np.min(out_vals)
    out_vals = out_vals/np.max(out_vals)
    out_vals = out_vals*2
    out_vals = out_vals - 1

    # Compute Phase
    phase = np.arccos(out_vals)

    np.save("phase_vals.npy", phase)

    camera.close()
    display.close()


if __name__=="__main__":
    # Get args
    args = parse_args()

    get_calibration_curve(args)