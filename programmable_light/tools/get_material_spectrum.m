function s = get_material_spectrum(cube)
    % Function to get material spectrum for a given hyperspectral cube
    %
    % Inputs:
    %   cube: 3D HSI cube
    %
    % Outputs:
    %   s: Spectrum of selected area which should be a representative of 
    %      the material's spectrm
    
    im_avg = sum(cube, 3);
    
    imshow(im_avg, []); title('Draw a rectangle around relevant region');
    rect = getrect();
    y1 = round(rect(1)); x1 = round(rect(2));
    y2 = y1 + round(rect(3)); x2 = x1 + round(rect(4));
    
    sub_cube = cube(x1:x2, y1:y2, :);
    
    s = squeeze(mean(mean(sub_cube, 1), 2));
    
    close all;
end