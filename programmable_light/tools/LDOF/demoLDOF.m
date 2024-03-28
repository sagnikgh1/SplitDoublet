im1 = double(imread('tennis492.ppm')); im1 = im1(1:2:end, 1:2:end, [1, 1, 1]);
im2 = double(imread('tennis493.ppm')); im2 = im2(1:2:end, 1:2:end, [1, 1, 1]);
tic; flow = mex_LDOF(im1,im2); toc