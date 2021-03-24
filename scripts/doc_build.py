#!/usr/bin/python3

# 2021-03-24 ph Created

"""
    quick and dirty tool to build the videos in ./doc

    scans through all .yaml files in ../yaml and creates equally named files with .mkv
    extension in /doc.
"""

import os

for file in os.listdir("../yaml"):
    print("yaml file", file)
    i=file.find(".yaml")
    if i!=-1:
        output = "../outputs/"+file[0:i]+".mov"
        file = "../yaml/"+file
        print("calling: python3 ./singulersum_video.py -i "+file+" -o "+output)
        os.system("python3 ./singulersum_video.py -i "+file+" -o "+output)
