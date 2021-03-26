# Singulersum - 3D graphics rendering engine - QUICK START

Singulersum is written in python. python must be installed in order to run Singulersum.

## first steps:

### install dependencies
python module dependencies for Singulersum:
* python (version 3) itself
* pyyaml (used to read .yaml files)
* Tkinter (used for building the Frontend/GUIs)
* PIL (used for Tkinter Image display, the 2D graphics are done in Singulersum/Draw2D.py)

Singulersum has not many dependencies, since it's purpose was to create the whole 3D and 2D pipeline in itself and without any external libraries (with the exception to the operating system interface and PIL for the Tkinter picture interaction and ffmpeg for creating videos).

non python dependencies to run Singulersum:
* ffmpeg is needed for video export
* it's currently developed for linux. Some things may not work on Windows/Mac. For example the video export in singulersum_video.py is using "ffmpeg" while on windows it would need to be "ffmpeg.exe".

### cloning the repository

git clone https://github.com/frazy81/Singulersum.git

### try it youself

cd Singulersum/scripts

./singulersum_gui.py

or

python3 ./singulersum_gui.py

## singulersum_gui - QUICK GUIDE

singulersum_gui.py has the menu "Examples" with some predefined examples (all stored as .yaml files in the /yaml directory). All of them are animated, how ever the animations are slow. You may want to pause the animation using the "pause/play" button at the bottom of the window.

singulersum_gui has a mouse interface. If you grab the screen by pushing the left mouse button (without release) and shifting the mouse left or right, the coordinate system begins to rotate (change the azimuth). Same is possible with up and down to change the "altitude". The second mouse button is used to scale in or out. This is the way to control the camera position in the GUI.

in singulersum_video.py these camera animations can be done by giving the camera an update animator (see .yaml files).

## singulersum_video - QUICK QUIDE

singulersum_video.py takes a .yaml file as input, renders the scene and outputs it as a video.

### example:
./singulersum_video.py -h

./singulersum_video.py -i ../yaml/cube.yaml -o ./testing.mov
