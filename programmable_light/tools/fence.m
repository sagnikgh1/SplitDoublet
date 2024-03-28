function fenceim = fence(width, spacing, H, W)
    % Create a fence image with repeating vertical stripes.
    %
    % Inputs:
    %   width: Width of fence in pixels
    %   spacing: Spacing between fence columns in pixels.
    %   H, W: Size of image
    %
    % Outputs:
    %   fenceim: Fence image.
    
    fenceim = zeros(1, W);
    fenceim(1:spacing:W) = 1;
    
    fenceim = conv(fenceim, ones(1, width), 'same');
    fenceim = fenceim(1:W);
    
    fenceim = ones(H, 1)*fenceim;
end