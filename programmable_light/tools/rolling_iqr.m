function output = rolling_iqr(input, winsize)
	% Function to compute rolling inter quantile range for a 1D signal.
	%
	% Inputs:
	% 	input: Input signal
	% 	winsize: Window size for computing IQR
	%
	% Outputs:
	% 	output: Rolling IQR output.

	if mod(winsize, 2) == 0
		winsize = winsize + 1;
	end

	output = zeros(size(input));

	N = length(output);
	M = (winsize-1)/2;

	for idx = 1:length(input)
		output(idx) = iqr(input(max(1, idx - M):min(N, idx + M)));
	end
end
