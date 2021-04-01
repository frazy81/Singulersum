#!/usr/bin/python3

# 2021-03-26 ph Created

"""
    singulersum_picture.py

    2021-03-26 Created by Philipp Hasenfratz

    loading a Singulersum YAML file and create pictures. If only one picture is needed, set --frames 1. Always add {:d} to the output file name (this is replaced by the current frame number).

    SingulersumPicture is using multiprocessing to speed up picture generation. Currently a total of 32 parallel workers are used to create images.

    Dependencies:
     - python PIL (to create .png files)

    Example usage:

    ./singulersum_picture.py --yaml ../yaml/sphericon_stl.yaml --output ../outputs/sphericon_{:06d}.gif --frames 60

    generates 60 pictures (from time=0.0 to time=1.0/30.0 * 60) and stores them as ../outputs/sphericon_000001.png to ../outputs/sphericon_000060.png
"""

import getopt
import sys
import os

from multiprocessing import Queue, Process
from queue import Empty
from PIL import Image

sys.path.append("..")

from Singulersum.Singulersum import Singulersum
from Singulersum.Debug import Debug

class SingulersumPicture(Debug):

    def __init__(self, width=1024, height=768, yaml="", frames=1, output=""):
        super().__init__()
        self.width = width
        self.height = height
        self.frames = frames
        self.yaml = yaml
        self.output = output
        self.animation_stop = False
        self.cam = None
        self.sg = Singulersum( callback=self.callback )
        if os.path.isfile(yaml):
            self.sg.yaml(yaml)
            self.cam.width = width
            self.cam.height = height
        else:
            self.debug("yaml file '{:s}' does not exist!".format(yaml))

        threads = 32

        task_queue = Queue()
        for frame in range(0, self.frames):
            task_queue.put(frame)

        processes = []
        for i in range(threads):
            p = Process(target=self.worker, args=[task_queue])
            processes.append(p)
            p.start()

        for i in range(threads):
            processes[i].join()

        print("all done.")

    def worker(self, in_queue):
        try:
            while True:
                frame = in_queue.get(block=True, timeout=2)
                self.time = 1.0 / 30.0 * frame
                self.sg.setTime(self.time)
                self.sg.update()
                if self.animation_stop is True:
                    print("animation ended.")
                    return True
                self.debug("build frame for Singulersum time:", self.sg.time)
                rgba = self.cam.image()
                self.sg.frameDone(self.time)
                img = Image.frombytes("RGBA", (self.width, self.height), rgba, decoder_name="raw").convert("RGB")
                output = self.output.format(frame)
                img.save(output)
        except Empty:
            print("Closing parallel worker, the worker has no more tasks to perform")
            return
        except Exception as e:
            print("Parallel worker got unexpected error", str(e))
            sys.exit(1)

    def callback(self, event="", **args):
        print("singulersum_picture(), got callback from Singulersum:", event, args)
        if event=="set":
            setattr(self, args["name"], args["value"])
            if args["name"]=="animated":
                if args["value"]==True:
                    print("TkGUI.callback() got an animated=True, therefore start playing")
                    self.isPlaying=True
                    self.isShowing=True
                else:
                    self.isShowing=True
                    self.isPlaying=False
            if args["name"]=="camera":
                # set the camera, so that the GUI knows which camera to get images from.
                current_width = self.width
                current_height = self.height
                if self.cam is not None:
                    current_width = self.cam.width
                    current_height = self.cam.height
                self.cam = self.sg.cameras[args["value"]]
                # initialize camera with the current canvas width/height
                self.cam.width = current_width
                self.cam.height = current_height
        if event=="animation_stop":
            if "object" in args:
                if args["object"]==self.sg:
                    self.animation_stop = True

def usage():
    print()
    print()
    print("SYNOPSIS: "+sys.argv[0])
    print(" -h                      help")
    print(" -i <yaml-file>          open the yaml file")
    print(" -t <time>               the 'Singulersum' time")
    print(" -o <picture-file>       output picture filename (don't forget {:06d})")
    print(" -f <frames>             how many frames to output")
    return 0

def main():
    verbose             = False
    yaml                = ""
    output              = ""
    frames              = 1
    width               = 1920
    height              = 1920

    try:
        optlist, args = getopt.getopt(sys.argv[1:], "i:hf:o:", ["yaml=", "help", "frames=", "output="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        return 1

    for name, value in optlist:
        if name in ["-i", "--yaml"]:
            yaml = value
        if name in ["-h", "--help"]:
            return usage()
        if name in ["-o", "--output"]:
            output = value
        if name in ["-f", "--frames"]:
            frames = int(value)
        if name in ["-e", "--exit-immediate"]:
            exitImmediate = True

    if yaml=="" or output=="":
        usage()
        return 1

    video = SingulersumPicture(width, height, yaml, frames, output)

if __name__ == "__main__":
    exit(main())
