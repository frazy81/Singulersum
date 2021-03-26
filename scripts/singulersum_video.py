#!/usr/bin/python3

# 2021-03-24 ph Created
# 2021-03-26 ph now internally using singulersum_picture.py (SingulersumPicture class)
# 2021-03-26 ph now parallelizable and faster because singulersum_picture now uses
#               threading

"""
    singulersum_video.py

    2021-03-24 ph Created by Philipp Hasenfratz

    loading a Singulersum YAML file and create a video from it.
    This script currently needs ffmpeg to create the videos.

    CAUTION:
     - this script overwrites files named /tmp/singulersum_video_*
     - this is a "quick and dirty" program, I just used it to generate videos quickly.

    Dependencies:
     - python PIL (to create .png files)
     - ffmpeg (to create video out of .png files)
     - system command rm to delete old files

    Example usage:

    ./singulersum_video.py -i ../yaml/sphericon_ascii_stl.yaml -o ../outputs/sphericon_ascii_stl.mov
"""

import getopt
import sys
import os

from PIL import Image
from singulersum_picture import SingulersumPicture

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
        if os.path.isfile(yaml) is False:
            self.debug("yaml file '{:s}' does not exist!".format(yaml))
            exit(0)

        frames = 2000       # define an absolute maximum, SingulersumPicture
                            # automatically stopps when the animation ends.
        pic_output = "/tmp/singulersum_video_"+str(os.getpid())+"_{:07d}.png"
        ffmpeg_input = "/tmp/singulersum_video_"+str(os.getpid())+"_%07d.png"
        sg = SingulersumPicture(width, height, yaml, frames, pic_output)

        print("all processed...")

        self.debug("calling ffmpeg to concat the images to a video")
        os.system("ffmpeg -hide_banner -y -r 30 -i "+ffmpeg_input+" -vf 'scale=1920:-2' -c:v libx264 -profile:v main -level 3.1 -pix_fmt yuv420p -preset medium -crf 20 -x264-params ref=4 -movflags +faststart "+str(output))

        print("delete temporary files")
        os.system("rm /tmp/singulersum_video_"+str(os.getpid())+"*.png")

def usage():
    print()
    print()
    print("SYNOPSIS: "+sys.argv[0])
    print(" -h                      help")
    print(" -i yaml-file            open the yaml file")
    print(" -o video-file           save the video in this file")
    #print(" --exit-immediately      exits straight after rendering the page (for testing)")
    return 0

def main():
    verbose             = False
    exitImmediate       = False
    yaml                = ""
    output              = ""
    width               = 1920
    height              = 1920      # TODO: video otherwise distorted.

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
