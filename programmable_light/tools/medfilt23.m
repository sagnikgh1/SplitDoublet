function output = medfilt23(cube, fsize)
    % Function to median filter a cube in a per-band basis.
    
    output = zeros(size(cube));
    for idx = 1:size(cube, 3)
        output(:, :, idx) = medfilt2(cube(:, :, idx), fsize);
    end
        
end