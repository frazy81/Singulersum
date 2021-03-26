# Singulersum - 3D graphics rendering engine

Singulersum is a prototype 3D graphics rendering engine. It aims to be able to visualize STL files, freely defined 3D functions and other objects (like points, lines, planes, spheres, polygons) in a 3D environment. It's a pure python software pipeline for 3D and 2D graphics to do what normally a GPU would do.

First some important notes:
 * this software is SLOW! It runs on the CPU (not a GPU) and is single threaded! Performance was NOT intended.
 * this software is BUGGY and incomplete. It's a prototype!
 * this software is not meant for production use

If you're looking for a 3D computer graphics software to create or visualize projects, I assume that you're better suited with something like [Blender](https://www.blender.org/), GLC Player, Meshlab, Viewstl or something alike. For mathematical illustration you may want to look at [Geogebra](https://www.geogebra.org/)

Why did I create Singulersum
 * it is and was fun to create. And a challenge!
 * a graphics card and it's libraries offer all of that functionality out of the box. How ever: I wanted to see HOW it actually works, doing it all myself.
 * it's cool to see what one can achieve
 * main aim is to share and/or create interest. You can do something if you like to! Anything you want!
 * in case you're interested in computer graphics or 3D graphics or projections. Take a look at the source code. But don't take it as ground truth! I'm not a graphics expert. I was just curious if I can do it with as little help as possible...

Some examples, videos and pictures:

/scripts/singulersum_gui.py, a Tkinter based GUI for Singulersum 3D rendering engine
![singulersum_gui.py](/docs/singulersum_gui.png)

Visualize binary and textual STL files (currently without color support):
![STL-Viewer](/docs/falcon.png)

Creation of animation videos using yaml configuration files (/scripts/singulersum_gui.py, using /yaml/sphericon_ascii_stl.yaml)
![YAML](/docs/yaml.png)

here some videos, created using Singulersum (/scripts/singulersum_video.py)
[![Millennium Falcon](https://img.youtube.com/vi/CSX7vUux068/0.jpg)](https://www.youtube.com/watch?v=CSX7vUux068)

video of the function z=sin(x)+sin(y):
[![z=sin(x)+sin(y)](https://img.youtube.com/vi/QPDUIITXlK4/0.jpg)](https://www.youtube.com/watch?v=QPDUIITXlK4)

Creating graphical representations of mathematical functions
![heart-curve](/docs/heart.png)

math calculus behind this software (one out of 16 pages):
![math](/docs/original_note_example.jpg)

Feature-Set of Singulersum:
 * 3D objects that may contain other objects (recursive structure)
 * z-Buffering
 * different cameras (all with their own position and view angles in space)
 * camera and object animation (currently only camera animation)
   * either through mouse in GUI or
   * configured in yaml
 * light sources (not yet supported)
 * luminescence (by comparing normal vector of polygons with view vector of camera)
 * object browser (not yet supported) to change properties of objects

My name is Philipp Hasenfratz (philipp.hasenfratz at protonmail.com). I'm a software developer based in Switzerland. This project was a fun side project of mine. I was wondering if I still had the mathematical skills to create and develop a 3D rendering engine prototype without any external tools, libraries, help or a GPU.
After 20 years out of school I was a bit rusty doing the math (vector geometry, matrix calculation, dot and vector product (luminescence calculus), linear equation systems, linear algebra), but I got it back again with some help of wikipedia of course. But the main objective was to develop the whole math myself and for most part I did exactly that. So the math behind Singulersum is most probably not the same as in commonly used 3D software...

After two weeks and roughly 200 hours of work the prototype was ready and worked (more or less)...
