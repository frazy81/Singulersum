#!/usr/bin/python3

# 2021-03-05 ph Created

"""
    singulersum_draw_test.py

    Testing and debugging the Draw2D() class.
"""

import sys
sys.path.append("..")
from Singulersum.Draw2D import Draw2D
from tkinter import *
from PIL.ImageTk import PhotoImage, Image
import math
import time

class Draw(Tk):

    def __init__(self):
        super().__init__()
        self.createWidgets()
        self.draw2d = Draw2D(1024, 768)
        self.draw2d.point(5, 5)
        for x in range(0,1024):
            for y in range(0,768):
                self.draw2d.point(x,y, "#555555")
        for x in range(100,200):
            self.draw2d.point(x,100)
            self.draw2d.point(x,200)
        for y in range(100,200):
            self.draw2d.point(100,y)
            self.draw2d.point(200,y)
        self.draw2d.line(97,97,203,97, "white")
        self.draw2d.line(203,97,203,203, "white")
        self.draw2d.line(203,203,97,203, "white")
        self.draw2d.line(97,203,97,97, "white")
        self.draw2d.line(100,100,200,200, "white")
        self.draw2d.line(100,200,200,100, "white")

        poly = (
            (400,400),
            (450,410),
            (430,450),
            (350,460)
        )
        self.draw2d.polygon(*poly, fill="white", stroke="white", alpha=0)

        poly = (
            (400,100),
            (400,150),
            (450,150),
            (450,100),
            (400,100)
        )

        self.draw2d.polygon(*poly, fill="white", stroke="#ff0000", alpha=0.2, zIndex=3.5)

        poly = (
            (420,120),
            (420,140),
            (480,120)
        )

        self.draw2d.polygon(*poly, fill="red", stroke="#ff0000", alpha=0.2, zIndex=4.5)

        val = self.draw2d.zIndex(405,105)
        if math.isclose(val, 3.5)==False:
            print("assertion error: 105x105 should have zIndex: 3.5, but is", val)
            exit(0)
        val = self.draw2d.zIndex(399,99)
        if val<1e300:
            print("assertion error: 99x99 should have zIndex: 0.0, but is", val)
            exit(0)

        val = self.draw2d.zIndex(425,120)
        if math.isclose(val, 3.5)==False:
            print("assertion error: 425x120 should have zIndex: 2.5, but is", val)
            exit(0)
        val = self.draw2d.zIndex(480,120)
        if math.isclose(val, 4.5)==False:
            print("assertion error: 480x120 should have zIndex: 4.5, but is", val)
            exit(0)

        self.showSingle()

    def showSingle(self):
        imgdata = self.draw2d.image()
        image = Image.frombuffer("RGBA", (self.draw2d.width,self.draw2d.height), imgdata, decoder_name="raw").convert("RGB")
        self.img = PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=NW, image=self.img)
        self.update()
        self.update_idletasks()

    def createWidgets(self):
        self.resizable( height=True, width=True )
        self.geometry( "{:d}x{:d}".format(1024,768) )
        self.title("Draw2D testing")
        self.functionbar = Frame(self, highlightbackground="black", highlightthickness=1)
        self.functionbar.pack(side=TOP)
        self.content = Frame(self, highlightbackground="black", highlightthickness=1)
        self.content.pack(side=TOP, fill=BOTH, expand=True)
        self.status = Frame(self)
        self.status.pack(side=TOP)
        self.statusLine = Label(self.status, text="Status: Ready")
        self.statusLine.pack(side=TOP)
        self.createViewer()

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
    draw = Draw()
    draw.mainloop()

exit(main())
