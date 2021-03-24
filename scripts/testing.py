#!/usr/bin/python3

# 2021-03-05 ph Created
# 2021-03-12 ph bug fix: RGB Camera Picture KeyError Exception resolved
# 2021-03-15 ph new RGBA and Draw2D image return type (RGBA)
# 2021-03-15 ph GUI update

"""
    testing.py

    testing.py is "almost" the same GUI as singulersum_gui.py ("the main viewer"). Use it
    to quickly setup a scene and test it.
"""

import sys
sys.path.append("..")
from Singulersum.Singulersum import Singulersum
from tkinter import *
from PIL.ImageTk import PhotoImage, Image
from math import *
import time

class SingulersumGUI(Tk):

    def __init__(self):
        super().__init__()

        self.isPaused=False

        sg = Singulersum(scale=(5,5,5), callback=self.callback)
        self.sg = sg

        #sg.yaml("../yaml/sine_waves.yaml")
        #sg.yaml("../yaml/tiny_house.yaml")
        #sg.yaml("../yaml/sphericon_ascii_stl.yaml")
        #sg.yaml("../yaml/utah_teapot_stl.yaml")
        #sg.yaml("../yaml/millennium_falcon_stl.yaml")
        #sg.yaml("../yaml/heart_curve.yaml")
        #sg.yaml("../yaml/sink.yaml")
        #sg.yaml("../yaml/cube.yaml")
        sg.yaml("../yaml/lighttest.yaml")

        self.cam = self.sg.cameras[self.camera]

        self.createWidgets()

        print("show initial image, for debugging")
        self.showSingle()

        print("sleep(2), showSingle for debugging()")
        #time.sleep(2)

        if "lighttest" in sg.objects:
            print("normalvector", pg.normalvector)
            print("view vector", self.cam.vec_mul_scalar(self.cam.V, 1/self.cam.vec_len(self.cam.V)))
            normalvector = pg.normalvector
            if normalvector[0]==0 and normalvector[1]==0 and normalvector[2]==0:
                normalvector=(1e-06, 0.0, 0.0)
            dot = self.cam.dot_product(self.cam.V, normalvector) / (self.cam.vec_len(self.cam.V)*self.cam.vec_len(normalvector) )
            print("dot product", dot)
            angle = acos( dot )
            print("angle in degree", angle/pi*180)
            colorize = abs(pi/2-angle)/(pi/2)
            print("=> colorize-factor", colorize)

        # animate and rotate the poly around the Y-axis
        while (True):
            nx = lambda x,y,z: x+y+z
            break
            pass

        self.mainloop_singulversum()

    def setImage(self):
        imgdata = self.cam.image()
        self.sg.debug("Tk picture import")
        timeit = self.sg.timeit()
        image = Image.frombuffer("RGBA", (self.cam.draw2d.width,self.cam.draw2d.height), imgdata, decoder_name="raw").convert("RGB")
        self.img = PhotoImage(image)
        self.sg.debug("Tk picture import complete.", timeit=timeit)

    def show(self):
        self.setImage()
        self.canvas.create_image(0, 0, anchor=NW, image=self.img)
        timeit = self.sg.timeit()
        self.sg.debug("update Tk Tasks")
        self.updateWidgets()
        self.update()
        self.update_idletasks()
        self.sg.debug("Tk Tasks updated, picture outlined", timeit=timeit)

    def showSingle(self):
        self.cam.setupCamera()
        self.show()

    def callback(self, event, **args):
        print("TkGUI, got callback from Singulersum:", event, args)
        if event=="set":
            setattr(self, args["name"], args["value"])
        elif event=="animation_start":
            self.isPlaying=True
            self.isShowing=True
        elif event=="animation_stop":
            self.isPlaying=False
            print("sleep (end of animation). Press play to play again.")
            self.isPaused=True
            self.pauseVar.set('play')
            self.sg.setTime(0.0)
            self.update()
            self.update_idletasks()
            time.sleep(1)
        pass

    def mainloop_singulversum(self):
        if self.animated is True:
            print("TkGUI(): got YAML animated=True")
            self.isPlaying=True
        while True:
            if self.isPaused is True:
                print("sleep (pause)")
                self.update()
                self.update_idletasks()
                time.sleep(1)
                continue

            self.sg.update()
            self.cam.setupCamera()
            self.show()

    def pauseplay(self):
        print("TkGUI: pause/play clicked")
        if self.isPaused is True:
            print("end pause")
            self.isPaused=False
            self.pauseVar.set('pause')
        else:
            print("begin pause")
            self.isPaused=True
            self.pauseVar.set('play')

    def rewind(self):
        print("TkGUI: rewind clicked")
        self.sg.setTime(0.0)
        print("end pause")
        self.isPaused=False
        self.pauseVar.set('pause')

    def createWidgets(self):
        self.resizable( height=True, width=True )
        self.geometry( "{:d}x{:d}".format(2048, int(2048/4*3)) )
        self.title("Philipp's Singulersum V1.0")
        self.functionbar = Frame(self, highlightbackground="black", highlightthickness=1)
        self.functionbar.pack(side=TOP)
        self.content = Frame(self, highlightbackground="black", highlightthickness=1)
        self.content.pack(side=TOP, fill=BOTH, expand=True)
        self.controlls = Frame(self, highlightbackground="black", highlightthickness=1)
        self.controlls.pack(side=TOP)
        # pause
        self.pauseVar = StringVar()
        self.pauseVar.set("pause")
        self.pauseBtn = Button(self.controlls, textvariable=self.pauseVar, command=lambda: self.pauseplay())
        self.pauseBtn.pack(side=LEFT)
        self.rewindBtn = Button(self.controlls, text="rewind", command=lambda: self.rewind())
        self.rewindBtn.pack(side=LEFT)

        self.status = Frame(self)
        self.status.pack(side=TOP)
        self.statusLine = Label(self.status, text="Status: Ready")
        self.statusLine.pack(side=LEFT)
        self.fpsNum = StringVar()
        self.fps = Label(self.status, textvariable=self.fpsNum)
        self.fps.pack(side=LEFT)
        self.camPos = StringVar()
        self.lcamPos = Label(self.status, textvariable=self.camPos)
        self.lcamPos.pack(side=LEFT)
        self.viewVec = StringVar()
        self.lviewVec = Label(self.status, textvariable=self.viewVec)
        self.lviewVec.pack(side=LEFT)
        self.createViewer()

    def updateWidgets(self):
        self.fpsNum.set("fps="+"{:0.2f}".format(self.sg.fps))
        self.camPos.set("cam=[{:0.2f}, {:0.2f}, {:0.2f}]".format(self.cam.x, self.cam.y, self.cam.z))
        self.viewVec.set("view at [{:0.2f}, {:0.2f}, {:0.2f}]".format(self.cam.V[0], self.cam.V[1], self.cam.V[2]))
        self.update()
        self.update_idletasks()

    def configureCanvas(self, event):
        width = self.winfo_width()-2
        height = self.winfo_height()-2
        pass

    def createViewer(self):
        canvas = Canvas(self.content)
        self.canvas = canvas
        self.content.bind("<Configure>", self.configureCanvas)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        pass

def main():
    gui = SingulersumGUI()
    gui.mainloop()

exit(main())
