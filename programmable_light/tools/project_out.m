function cube_proj = project_out(cube, spec)
    % Remove contribution from a given spectrum
    %
    % Inputs:
    %   cube: Input hyperspectral cube
    %   spec: Spectral profile whose contribution is to be removed
    %
    % Outputs
    %   cube_proj: Cube with spec projected out.
    
    spec = spec(:);
    
    [H, W, T] = size(cube);
    hsmat = reshape(cube, H*W, T);
    
    hsmat_proj = hsmat - (hsmat*spec*spec')/(spec'*spec);
    
    cube_proj = reshape(hsmat_proj, H, W, T);    
end