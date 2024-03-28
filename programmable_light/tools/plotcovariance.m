function fig = plotcovariance(covmat, labels)
    % Function to plot a given covariance matrix.
    %
    % Inputs:
    %   covmat: Covariance matrix
    %   labels: Labels of each class
    %
    % Outputs:
    %   fig: Figure handle
    
    fig = figure('units','normalized','outerposition',[0 0 1 1]);
    imagesc(covmat);
    colormap(gray);
    
    numlabels = numel(labels);
    
    set(gca,'XTick',1:numlabels,...
    'XTickLabel',labels,...
    'YTick',1:numlabels,...
    'YTickLabel',labels,...
    'TickLength',[0 0]);
end
