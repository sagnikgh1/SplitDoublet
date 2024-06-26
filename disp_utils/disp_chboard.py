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
    parser.add_argument('-w', '--display_name', default='SLM Window',
                        help='Display name')
    
    # Square size
    parser.add_argument('-s', '--square_size', default=128,
                        help='Checkerboard square size')

    
    # Now parse
    args = parser.parse_args()

    # Now return arguments
    return args

def Checkerboard(N,n):
    """N: size of board; n=size of each square; N/(2*n) must be an integer """
    if (N%(2*n)):
        print('Error: N/(2*n) must be an integer')
        return False
    a = np.concatenate((np.zeros(n),np.ones(n)))
    b=np.pad(a,int((N**2)/2-n),'wrap').reshape((N,N))
    return (b+b.T==1).astype(int)

def disp_pattern(args):
    """
    Function to obtain and plot SLM calibration curve
    """
    
    # Create a new display
    display = hardware.Display(args.display_id, args.display_name)
    Hd, Wd = display.shape

    pattern = Checkerboard(Wd, args.square_size)[:Hd, :]*255
    
    # Convert to red
    pattern = np.stack([pattern]*3, axis=2)
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