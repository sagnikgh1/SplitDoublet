function clipped_im = clip_im(im, thres)
    % Function wrapper to clip an image based on threshold
    %
    % Inputs:
    %   im: Input image
    %   thres: Threshold above which pixels are considered relevant.
    %       The output image is a clipped version of image which contains
    %       only relevant pixels
    % 
    % Outputs:
    %   clipped_im: Clipped image
    
    [X, Y] = find(im > thres);
    
    h1 = min(X); h2 = max(X);
    w1 = min(Y); w2 = max(Y);
    
    clipped_im = im(h1:h2, w1:w2);
end