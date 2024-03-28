function [lpp, mtf, mtf30] = eval_mtf(im, linepairs, minradius, maxradius, ...
                                      center)
	% Function to evaluate MTF of a given sector star image
	%
	% Inputs:
	% 	im: Image of sector star
	% 	linepairs: Total number of sectors in the image
	% 	minradius: Minimum radius for MTF computation
	% 	maxradius: Maximum radius for MTF computation
    %   center: Center of the sector star. if nit is not provided, the 
    %       function prompts user to click the center on the image.
	%
	% Outputs:
	% 	lpp: Line pairs per pixel
	% 	mtf: Array of MTF values
	% 	mtf30: lpp at 30% contrast ratio
    
    % Ask user to click center of image
    if ~exist('center', 'var')
        imshow(im, []);
        [x, y] = ginput(1);
        close all;

        center = [round(y), round(x)];
    end

	radii = minradius:maxradius;

	lpp = zeros(1, length(radii));
	mtf = zeros(1, length(radii));

	for idx = 1:length(radii)
		rad = radii(idx);
		angles = linspace(0, 2*pi, 100);

		x = rad*cos(angles) + center(1);
		y = rad*sin(angles) + center(2);

		sector_vals = interp2(im, x, y, 'bilinear', 0);
		lpp(idx) = linepairs/(2*pi*rad);

		% Evaluate MTF as local ratio of min to max
		up = movmax(sector_vals, round(rad/2));
		lo = -movmax(-sector_vals, round(rad/2));

		mtf(idx) = mean((up-lo)./(up+lo));
	end

	% Evaluate mtf30
	mtf30 = interp1(lpp, mtf, 0.3, 'linear', 0);
end
