 # System imports
import sys
import argparse
from tqdm import tqdm

# Scientific computing
import numpy as np

# Our own imports
sys.path.append('../programmable_light/python')
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

    # Display id
    parser.add_argument('-d', '--display_id', default=1, type=int,
                        help='Display id')
    
    # Display name
    parser.add_argument('-n', '--display_name', default='SLM Window',
                        help='Display name')
    
    # Dot spacing
    parser.add_argument('-s', '--space', default=100,
                        help='Dot spacing')
    
    # Dot width
    parser.add_argument('-w', '--width', default=5,
                        help='Dot spacing')

    
    # Now parse
    args = parser.parse_args()

    # Now return arguments
    return args


def dots(args, h, w):
    im = np.zeros((h, w, 3))
    indexs = np.arange(0, h-args.space, args.space)
    line = np.zeros(args.width, h)
    line[indexs] = 1

def disp_pattern(args):
    """
    Function to obtain and plot SLM calibration curve
    """
    
    # Create a new display
    display = hardware.Display(args.display_id, args.display_name)
    Hd, Wd = display.shape

    pattern = dots(args, int(Hd), int(Wd))*255
    
    # Convert to red
    pattern[:,:,1:] = 0
    

    while True:
        try:
            texture = display.create_texture_from_numpy(pattern)
            display.render(texture)

        except KeyboardInterrupt:
            display.close()
            break


if __name__=="__main__":
    args = parse_args()
    disp_pattern(args)