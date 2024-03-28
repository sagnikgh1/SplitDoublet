function cube = decode_hadamard(data_p, data_n, Hmat)
    % Small wrapper to decode Hadamard data
    
    [H, W, T] = size(data_p);
    hsmat = reshape(data_p - data_n, H*W, T);
    
    % Invert
    hsmat_decoded = hsmat*Hmat;
    
    % Correct for abnormality
    t = sum(hsmat_decoded, 1);

    [~, bad_idx] = max(t);
    hsmat_decoded(:, bad_idx) = hsmat_decoded(:, bad_idx+1);
    
    cube = reshape(hsmat_decoded, H, W, T);
    
end