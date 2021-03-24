#!/usr/bin/python3

# 2021-03-24 ph Created

"""
    singulersum_video.py

    loading a Singulersum YAML file and create a video from it.
    This script currently needs ffmpeg to create the videos.

    CAUTION:
     - this script overwrites files named /tmp/singulersum_video_*
     - this script can not run in parallel (it first removes temporary pictures, hence a second process running in parallel would loose it's images)
     - this is a "quick and dirty" program, I just used it to generate videos quickly.

    Dependencies:
     - python PIL (to create .png files)
     - ffmpeg (to create video out of .png files)
     - system command rm to delete old files

    Example usage:

    ./singulersum_video.py --yaml ../yaml/millennium_falcon_stl.yaml --output ../outputs/millennium_falcon.mov
"""

# TODO: iPhone capable default export

import getopt
import sys
import os

from PIL import Image

sys.path.append("..")

from Singulersum.Singulersum import Singulersum
from Singulersum.Debug import Debug

class SingulersumVideo(Debug):

    def __init__(self, width=1024, height=768, yaml="", output=""):
        super().__init__()
        self.width = width
        self.height = height
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
        self.frames = 0
        self.debug("delete old temporary files")
        os.system("rm /tmp/singulersum_video_*.png")    # TODO: this is bad, fix me
        while self.animation_stop is False:
            # self.animation_stop is changed by an event callback from singulersum
            # (event="animation_stop", object=<Singulersum>) which is fired if
            # Singulersum does not detect anymore changes in it's update() cycle.
            self.sg.update()
            self.debug("current Singulersum time:", self.sg.time)
            rgba = self.cam.image()
            img = Image.frombytes("RGBA", (self.width, self.height), rgba, decoder_name="raw").convert("RGB")
            img.save("/tmp/singulersum_video_{:07d}.png".format(self.frames))

            self.frames += 1
        self.debug("frames written:", self.frames)
        self.debug("calling ffmpeg to concat the images to a video")
        os.system("ffmpeg -hide_banner -y -r 30 -i /tmp/singulersum_video_%07d.png -vf 'scale=1920:-2' -c:v libx264 -profile:v main -level 3.1 -pix_fmt yuv420p -preset medium -crf 20 -x264-params ref=4 -movflags +faststart "+str(output))

    def callback(self, event="", **args):
        print("singulersum_video(), got callback from Singulersum:", event, args)
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
    print(" -i yaml-file            open the yaml file")
    print(" -o video-file           save the video in this file")
    print(" --exit-immediately      exits straight after rendering the page (for testing)")
    return 0

def main():
    verbose             = False
    exitImmediate       = False
    yaml                = ""
    output              = ""
    width               = 1920
    height              = int(1920/16*9)

    try:
        optlist, args = getopt.getopt(sys.argv[1:], "i:ho:", ["yaml=", "help", "output=", "exit-immediate"])
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
        if name in ["-e", "--exit-immediate"]:
            exitImmediate = True

    video = SingulersumVideo(width, height, yaml, output)


exit(main())
