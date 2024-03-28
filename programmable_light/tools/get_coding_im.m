function imcode = get_coding_im(code, wvl, device)
    % Function to get a coding image for projector for a given spectral
    % profile
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
    
    % Step 2 -- get rid of devices' default spectrum
    %profile = (profile./device.light_spectrum).*mask;
    profile = profile/max(profile(:));
    
    % Step 3 -- Gamma correct the profile
    profile = uint8(profile*255)+1;
    
    gamma_idx = sub2ind(size(device.gamma_map), profile', 1:length(device.wvl));
    profile = device.gamma_map(gamma_idx).*mask';
    
    % Step 5 -- find clipping indices for wavelengths
    [~, idx1] = min(abs(device.wvl - device.lambda1));
    [~, idx2] = min(abs(device.wvl - device.lambda2));
    
    % Step 4 -- create projector image.
    imcode = zeros(device.size);
    
    minidx = min(idx1, idx2);
    maxidx = max(idx1, idx2);
    
    
    profile_img = ones(device.size(1), 1)*profile(minidx:maxidx);
    imcode(:, round(device.index_map(minidx:maxidx))) = profile_img;
    
    % Final step -- convert to uint8
    imcode = uint8(imcode);
end