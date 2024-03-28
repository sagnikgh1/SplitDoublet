function denoised_im = wdenoise2(im, thres)
    % Wavelet denoising of images
    
    [H, W] = size(im);
    N = min(floor(log2([H, W])));
    
    [C, S] = wavedec2(im, N, 'bior4.4');
    
    C(abs(C) < thres*max(abs(C))) = 0;
    
    denoised_im = waverec2(C, S, 'bior4.4');
end