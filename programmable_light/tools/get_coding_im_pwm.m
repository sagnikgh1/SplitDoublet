function imcode = get_coding_im_pwm(code, wvl, device)
    % Function to get a coding image for projector for a given spectral
    % profile using spatial PWM.
    %
    % Inputs:
    %   code: Spectral profile with values between 0, 1
    %   wvl: Wavelengths for spectral profile
    %   device: Structure with device properties.
    %       wvl: WAvelengths used for calibrating device
    %       lambda1: Starting wavelength
    %       lambda2: Ending wavelength
    %       gamma_map: 256xlength(wvl) sized gamma correction map
    %       index_map: Indices map from wavelengths to projector column
    %           indices
    %       light_spectrum: Uncoded spectra of light source setup.
    %       size: Size of projector.
    %
    % imcode: Output image to display on light source projector to achieve
    %   desired spectral profile.
    
    % Step 1 -- convert profile to device wavelengths
    profile = interp1(wvl, code, device.wvl, 'linear', 0);
    mask = (profile ~= 0);
    
    H = device.size(1);
    
    % Step 2 -- get rid of devices' default spectrum
    %profile = (profile./device.light_spectrum).*mask;
    profile = round((H/2-1)*profile/max(profile(:)));
    
    % Step 5 -- find clipping indices for wavelengths
    [~, idx1] = min(abs(device.wvl - device.lambda1));
    [~, idx2] = min(abs(device.wvl - device.lambda2));
    
    % Step 4 -- create projector image.
    imcode = zeros(device.size);
    
    minidx = min(idx1, idx2);
    maxidx = max(idx1, idx2);
    
    for idx = minidx:maxidx
        dx = profile(idx); 
        imcode(H/2-dx:H/2+dx, round(device.index_map(idx))) = device.gamma_map(end, idx);
    end
        
    % Final step -- convert to uint8
    imcode = uint8(imcode);
end