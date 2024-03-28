function [direct_img, global_img] = separate_snapshot(img, winsize)
    % Function to separate direct and global parts of a scene using a 
    % single image.
    %
    % Inputs:
    %   img: Input snapshot image
    %   winsize: Window size to operate over
    %
    % Outputs:
    %   direct_img: Direct component
    %   global_img: Global component
    
    [H, W] = size(img);
    
    immin = zeros(H, W);
    immax = zeros(H, W);
    
    wh = winsize(1);
    ww = winsize(2);
    
    for h = 1:H
        for w = 1:W
            h1 = round(max(1, h-wh/2));
            h2 = round(min(H, h+wh/2));
            w1 = round(max(1, w-ww/2));
            w2 = round(min(W, w+ww/2));
            
            patch = img(h1:h2, w1:w2);
            immin(h, w) = min(patch(:));
            immax(h, w) = max(patch(:));
        end
    end
    direct_img = immax - immin;
    global_img = immin;
    
    %kern = gausswin(wh, 2)*gausswin(ww, 2)';
    %kern = kern/sum(kern(:));
    
    %direct_img = conv2(immax - immin, kern, 'same');
    %global_img = conv2(immin, kern, 'same');
end