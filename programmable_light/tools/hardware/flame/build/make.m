%% Script to compile the C++ file to get data from spectometer

%% Java includes
javadir = 'C:/Program Files/Java/jdk1.8.0_191/';
includedir_java = [javadir 'include'];
libdir_java = [javadir 'lib'];
includedir_java_win32 = [javadir 'include/win32'];

%% Our own includes and libraries
libdir = '../Library64/';
includedir = '../Include/';
srcdir = '../src/';

%% Ocean Optics includes
flame_root = 'C:/Program Files/Ocean Optics/OmniDriverSPAM/';
libdir_flame = [flame_root 'OOI_HOME'];
includedir_flame = [flame_root 'include'];

args = {['-I' includedir_java], ['-I' includedir_java_win32], ...
        ['-L' libdir_java], ...
        ['-I' includedir], ['-I' includedir_flame], ['-I' srcdir], ...
        ['-L' libdir], ['-L' libdir_flame], ...
        '-lOmniDriver64', '-lcommon64', '-ljvm', '-DWIN32'};

src = {'../src/flame_get_spectrum.cpp', ...
       '../src/utils.c'};

mex(src{:}, args{:});

