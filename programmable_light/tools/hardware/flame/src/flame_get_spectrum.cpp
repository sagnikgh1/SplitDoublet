/* Mex function to get data from FLAME spectrometer */
#define HIGHRESTIMESTAMP_H
#define SPECTROMETERCHANNEL_H

/* Matlab standard imports */
#include <mex.h>
#include <stdio.h>
#include <conio.h>

/* Omnidriver imports */
#include <Wrapper.h>
#include <ArrayTypes.h>

/* Our own imports */
#include <utils.h>

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])
{	 
	int exposure_time;          /* Exposure time in us */
	int	npixels;                /* Number of pixels */
	int nspectrometers;         /* Number of spectrometers (usuall 1) */
	//DoubleArray spectrumArray;  /* Data is initially imported as array */
	//DoubleArray wavelengthArray;/* So are wavelengths */
	Wrapper wrapper;			/* All talking will happen through wrapper */
   
    /* Get number of spectrometers */
	//nspectrometers = wrapper.openAllSpectrometers();	
	//printf ("\n\nNumber of spectrometers found: %d\n", nspectrometers);

	/* That's it. No fancy things */
}