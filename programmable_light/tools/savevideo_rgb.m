function savevideo_rgb(imstk, savename, framerate)
	% Tiny function to save video
	
	vid_obj = VideoWriter(savename);
	vid_obj.FrameRate = framerate;
	vid_obj.open()
	
	for idx = 1:size(imstk, 4)
		vid_obj.writeVideo(imstk(:, :, :, idx));
	end
	vid_obj.close()
end
