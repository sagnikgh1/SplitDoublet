function xsmooth = polysmooth(x, ord)
	% Smoothen a curve using polynomial fitting.
	%
	% Inputs:
	% 	x: Input signal
	% 	ord: Order of polynomial
	%
	% Outputs:
	% 	xsmooth: Polynomial fit of x.

	[p, S, mu] = polyfit(1:length(x), x(:)', ord);
	xsmooth = reshape(polyval(p, 1:length(x), S, mu), size(x));
end
