function nb_filter = get_nb_filter(wvl, cwl, fwhm)
    % Function to get a narrowband filter of given central wavelength
    % and FWHM
    % 
    % Inputs:
    %   wvl: Vector of wavelengths in nm
    %   cwl: Central wavelength in nm
    %   fwhm: Full width half max in nm
    %
    % Outputs:
    %   nb_filter: Narrowband filter of same dimensions as wvl.
    
    sigma = fwhm/(2*sqrt(2*log(2)));
    
    nb_filter = exp(-(wvl - cwl).^2/(2*sigma*sigma));
    
end