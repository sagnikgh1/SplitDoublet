function output = iqr_filter(input, winsize)
    % Remove spikes in data by finding points outside median+3IQR
    %
    % Inputs:
    %   input: Input signal
    %   winsize: Window size for rolling median and IQR
    %
    % Outputs:
    %   output: Signal with spikes removed.

    input_med = medfilt1(input, winsize);
    input_iqr = rolling_iqr(input, winsize);

    valid = find(abs(input - input_med) < 3*input_iqr);

    output = interp1(valid, input(valid), 1:length(input), 'linear', 0);
end
