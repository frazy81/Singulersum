#!/usr/bin/python3

# 2021-03-05 ph Created
# 2021-03-12 ph bug fix: RGB Camera Picture KeyError Exception resolved
# 2021-03-15 ph new RGBA and Draw2D image return type (RGBA)
# 2021-03-15 ph GUI updates (fps, play/pause, rewind)
# 2021-03-16 ph First Mouse interaction: fly around the scenery
# 2021-03-17 ph writing to singulversum.log
# 2021-03-21 ph camera "walk-in" (2nd Button) kind of working now
# 2021-03-24 ph from tests, created .yaml files
# 2021-03-24 ph corrected CanvasInteraction so that it works with new loaded yaml also
#               new camera needed to be setup in CanvasInteract, so that updateFunction
#               can be removed on mouse action

"""
    class SingulersumGUI() and program singulersum_gui.py

    2021-03-05 ph Created by Philipp Hasenfratz

    the SingulersumGUI class and the singulersum_gui.py script implement a "viewer" for
    Singulersum using Tkinter.

    It "features" left mouse click and hold interaction to fly around the scene (in x, y and z-axis). It also features a 2nd mouse click and hold interaction to move closer into the scene or move out.

    Almost all menu items are not yet implemented...

    To see some other examples, go into the examples menu and choose one.
"""

# TODO: maybe checkout pyautogui for absolute mouse coords
# TODO: export currently shown frame as .png
# TODO: export current scenery as .stl
# TODO: after mouse operation the updateFunction might be reinitialized so that rewind/
#       play works again.

import sys
sys.path.append("..")
from Singulersum.Singulersum import Singulersum
from tkinter import *
from PIL.ImageTk import PhotoImage, Image
from math import *
import time
import struct

class SingulersumGUI(Tk):

    def __init__(self):
        super().__init__()

        # configureCanvas is changing these to the actual canvas size
        self.width = 2048
        self.height = 2048
        self.cam = None

        self.isShowing = True      # self.show() running?
        self.isTerminating = False
        self.animated = False       # this is set by a yaml. calling callback()
        self.framesShown = 0
        self.isPlaying = True
        self.objectBrowser = False
        self.settingsBrowser = False
        self.selectedItem = None    # sg def first

        self.canvasInteract = CanvasInteract(self, None)

        self.sg = Singulersum(scale=(5.0, 5.0, 5.0), callback=self.callback)
        self.sg.logfile("./singulersum_gui.log")

        self.sg.yaml("../yaml/lighttest.yaml")

        self.cam = self.sg.cameras[self.camera]
        self.canvasInteract.camera(self.cam)    # same in callback()!!!

        self.selectedItem = self.sg

        self.sg.setTime(0)

        self.createWidgets()

        self.show()

    def callback(self, event, **args):
        print("TkGUI, got callback from Singulersum:", event, args)
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
                # singulversum updated it's default camera, so we need to setup the new
                # camera and make a new CanvasInteract for mouse operations.
                self.cam = self.sg.cameras[args["value"]]
                # initialize camera with the current canvas width/height
                self.cam.width = current_width
                self.cam.height = current_height
                self.canvasInteract.camera(self.cam)
        elif event=="animation_start":
            # TODO: this is nowhere fired!
            self.play()
        elif event=="animation_stop":
            self.pause()
            print("sleep (end of animation). Press play to play again.")
            self.isPaused=True
            self.pauseVar.set('play')
            self.sg.setTime(0.0)
            self.update()
            self.update_idletasks()
        pass

    def showImage(self):
        self.framesShown += 1
        imgdata = self.cam.image()
        self.sg.debug("Tk picture import")
        timeit = self.sg.timeit()
        image = Image.frombuffer("RGBA", (self.cam.draw2d.width,self.cam.draw2d.height), imgdata, decoder_name="raw").convert("RGB")
        self.img = PhotoImage(image)
        self.sg.debug("Tk picture import complete.", timeit=timeit)

        timeit = self.sg.timeit()
        self.canvas.create_image(0, 0, anchor=NW, image=self.img)
        self.updateWidgets()
        self.sg.debug("update Tk Tasks")
        self.sg.debug("Tk Tasks updated, picture outlined", timeit=timeit)

    # show(), the mainloop for SingulversumGUI!
    def show(self):
        while True:
            print("state: isShowing=", self.isShowing, "isPlaying=", self.isPlaying)
            if self.isTerminating is True:
                # terminating is stepping out of this while!
                print("show(): received terminate instruction. Finish work and close application") # needs to be done here, since everything else is async and only this method is actually always running. Therefore a sleep() in quit() does not change anything... Kind of. Well it's strange...
                print(self.framesShown, "frames shown.")
                self.destroy()
                return True
            if self.isShowing is False:
                print("idle")
                self.update()
                self.update_idletasks()
                print("sleep 0.5")
                time.sleep(0.5)
                continue
            else:
                print()
            if self.isPlaying is False:
                self.isShowing=False        # set early! if mouse event occurs in between
                print("stop playing")
                self.showImage()
                self.update()
                self.update_idletasks()

            self.sg.update()
            self.showImage()

    def play(self):
        print("TkGUI: play clicked")
        # TODO: reinitialize camera update function which might have been destroyed by
        # CanvasInteract() class
        if self.isPlaying is False:
            self.isShowing=True
            self.isPlaying=True
            self.pauseVar.set('pause')

    def pause(self):
        self.isPlaying=False
        self.pauseVar.set('play')

    def rewind(self):
        print("TkGUI: rewind clicked")
        # TODO: reinitialize camera update function which might have been destroyed by
        # CanvasInteract() class
        self.isPlaying=False
        self.sg.setTime(0.0)
        self.sg.update()
        print("start to play again")
        self.isPlaying=True
        self.isShowing=True
        self.pauseVar.set('pause')

    def repaint(self):
        print("TkGUI: repaint clicked")
        self.isShowing=True

    def createWidgets(self):
        self.resizable( height=True, width=True )
        self.geometry( "{:d}x{:d}".format(self.width, self.height) )
        self.title("Singulersum V{:0.1f}".format(Singulersum.version))

        # to minimize on close
        #self.protocol("WM_DELETE_WINDOW", self.iconify)
        self.protocol("WM_DELETE_WINDOW", self.quit)

        # menu
        menubar = Menu(self)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=lambda: self.newFile())
        filemenu.add_command(label="Open", command=lambda: self.openFile())
        filemenu.add_command(label="Save", command=lambda: self.notImpl())
        filemenu.add_command(label="Save as...", command=lambda: self.notImpl())
        filemenu.add_command(label="Close", command=lambda: self.newFile())

        filemenu.add_separator()

        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Undo", command=lambda: self.notImpl())

        editmenu.add_separator()

        editmenu.add_command(label="Cut", command=lambda: self.notImpl())
        editmenu.add_command(label="Copy", command=lambda: self.notImpl())
        editmenu.add_command(label="Paste", command=lambda: self.notImpl())
        editmenu.add_command(label="Delete", command=lambda: self.notImpl())
        editmenu.add_command(label="Select All", command=lambda: self.notImpl())
        menubar.add_cascade(label="Edit", menu=editmenu)

        examplesmenu = Menu(menubar, tearoff=0)
        examplesmenu.add_command(label="tiny house", command=lambda: self.openYaml("../yaml/tiny_house.yaml"))
        examplesmenu.add_command(label="lighttest", command=lambda: self.openYaml("../yaml/lighttest.yaml"))
        examplesmenu.add_command(label="cube", command=lambda: self.openYaml("../yaml/cube.yaml"))
        examplesmenu.add_command(label="sine waves", command=lambda: self.openYaml("../yaml/sine_waves.yaml"))
        examplesmenu.add_command(label="sphericon", command=lambda: self.openYaml("../yaml/sphericon_ascii_stl.yaml"))
        examplesmenu.add_command(label="utah teapot", command=lambda: self.openYaml("../yaml/utah_teapot_stl.yaml"))
        examplesmenu.add_command(label="millennium falcon", command=lambda: self.openYaml("../yaml/millennium_falcon_stl.yaml"))
        examplesmenu.add_command(label="heart curve", command=lambda: self.openYaml("../yaml/heart_curve.yaml"))
        examplesmenu.add_command(label="sink", command=lambda: self.openYaml("../yaml/sink.yaml"))

        menubar.add_cascade(label="Examples", menu=examplesmenu)

        settings = Menu(menubar, tearoff=0)
        settings.add_command(label="Singulersum", command=lambda: self.configSingulersum(Toplevel(self)))

        settings.add_separator()

        menubar.add_cascade(label="Settings", menu=settings)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help Index", command=lambda: self.notImpl())
        helpmenu.add_command(label="About...", command=lambda: self.help())
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.config(menu=menubar)

        # main panel
        self.functionbar = Frame(self, highlightbackground="black", highlightthickness=1)
        self.functionbar.pack(side=TOP, anchor=W)

        self.center = Frame(self)
        self.center.pack(side=TOP, fill=BOTH, expand=True)
        self.objectBrowserPanel = Frame(self)
        self.content = Frame(self.center, highlightbackground="black", highlightthickness=1)
        self.content.pack(side=LEFT, fill=BOTH, expand=True)
        self.settingsBrowserPanel = Frame(self)

        # function bar (top)
        bar = self.functionbar
        Button(bar, text="objects", command=lambda: self.guiUpdate("objectBrowser") ).pack(side=LEFT, anchor=W)
        Button(bar, text="settings", command=lambda: self.guiUpdate("settingsBrowser") ).pack(side=LEFT, anchor=W)

        # controlls
        self.controlls = Frame(self, highlightbackground="black", highlightthickness=1)
        self.controlls.pack(side=TOP)

        self.pauseVar = StringVar()
        self.pauseVar.set("pause")
        self.pauseBtn = Button(self.controlls, textvariable=self.pauseVar, command=lambda: self.pause() if self.isPlaying else self.play())
        self.pauseBtn.pack(side=LEFT)
        self.rewindBtn = Button(self.controlls, text="rewind", command=self.rewind)
        self.rewindBtn.pack(side=LEFT)
        self.repaintBtn = Button(self.controlls, text="repaint", command=self.repaint)
        self.repaintBtn.pack(side=LEFT)

        # status
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
        self.sphericalVec = StringVar()
        self.lsphericalVec = Label(self.status, textvariable=self.sphericalVec)
        self.lsphericalVec.pack(side=LEFT)
        self.createViewer()

    def guiUpdate(self, name=None):
        if name is not None:
            val = getattr(self, name)
            if val is False:
                val = True
            else:
                val = False
            setattr(self, name, val)

        if self.objectBrowser is True:
            self.objectBrowserPanel.place(anchor=NW, x=0, y=100, relwidth=0.4, relheight=0.9)
        else:
            for child in self.settingsBrowserPanel.winfo_children():
                child.destroy()
            self.objectBrowserPanel.place_forget()
        if self.settingsBrowser is True:
            self.settingsBrowserPanel.place(anchor=NE, relx=1, y=100, relwidth=0.4, relheight=0.9)
            f=Frame(self.settingsBrowserPanel)
            f.pack(side=TOP, anchor=NW)
            if self.selectedItem==self.sg:
                self.configSingulersum(f)
        else:
            self.settingsBrowserPanel.place_forget()
            for child in self.settingsBrowserPanel.winfo_children():
                child.destroy()

    def quit(self):
        print("terminating the application")
        self.isTerminating=True
        self.sg.quit()
        print("wait for show() to finish.")
        self.update()
        self.update_idletasks()

    def updateWidgets(self):
        self.fpsNum.set("fps="+"{:0.2f}".format(self.sg.fps))
        self.camPos.set("cam=[{:0.2f}, {:0.2f}, {:0.2f}]".format(self.cam.x, self.cam.y, self.cam.z))
        self.viewVec.set("view at [{:0.2f}, {:0.2f}, {:0.2f}]".format(self.cam.V[0], self.cam.V[1], self.cam.V[2]))
        self.sphericalVec.set("sherical [{:0.2f}, {:0.2f}, {:0.2f}]".format(self.cam.azimuth, self.cam.altitude, self.cam.radius))
        self.update()
        self.update_idletasks()

    def openYaml(self, file):
        print("TkGUI(): open yaml file", file)
        self.sg.reset()
        self.sg.yaml(file)
        self.isPlaying=True

    def newFile(self):
        self.isPaused=True
        sg = Singulersum(scalex=1.0, scaley=1.0, scalez=1.0)
        self.sg = sg
        #sg.light(0,0,-1,"parallel",1)
        self.cam = sg.camera( 1.3, 0.2, 0.3, 0.0, 0.0, 0.0, fov=140, width=2048, height=int(2048/4*3))
        sg.coordinateSystem()

        sg.setTime(0)

        self.animate()

    def notImpl(self):
        top = Toplevel(self)
        top.bind('<Escape>', lambda e: top.destroy())
        top.title("Not Implemented")
        top.geometry( "{:d}x{:d}".format(600, int(600/4*2)) )
        label = Label(top, text="")
        label.pack(side=TOP)
        label = Label(top, text="Not yet implemented.")
        label.pack(side=TOP)
        label = Label(top, text="")
        label.pack(side=TOP)
        button = Button(top, text="Cancel", command=lambda: top.destroy())
        button.pack(side=TOP)

    def help(self):
        top = Toplevel(self)
        top.bind('<Escape>', lambda e: top.destroy())
        top.title("Singulersum help")
        top.geometry( "{:d}x{:d}".format(600, int(600/4*2)) )
        label = Label(top, text="")
        label.pack(side=TOP)
        label = Label(top, text="2021-03-05 Philipp Hasenfratz")
        label.pack(side=TOP)
        label = Label(top, text="Singulersum is a prototype for a")
        label.pack(side=TOP)
        label = Label(top, text="3D rendering engine")
        label.pack(side=TOP)
        label = Label(top, text="")
        label.pack(side=TOP)
        button = Button(top, text="Cancel", command=lambda: top.destroy())
        button.pack(side=TOP)

    def configSingulersum(self, top):
        row = 0
        column = 0

        if top!=self and isinstance(top, Toplevel) is True:
            # coming from menu, settings placed in a Toplevel (new Window)
            top.title("configure Singulersum object")
            top.geometry( "{:d}x{:d}".format(800, int(800/4*2)) )
            top.bind('<Escape>', lambda e: top.destroy())
        else:
            # in settingsPanel, set title
            l=Label(top, text="settings panel")
            l.grid(row=row, column=column, sticky=W)
            row+=2

        entries = []

        label = Label(top, text="")
        label.grid(row=row, column=column, sticky=W)
        row+=1
        label = Label(top, text="set time")
        label.grid(row=row, column=column, sticky=W)
        column+=1
        time = Entry(top)
        time.insert(0, self.sg.time)
        entries.append( { "object":self.sg, "name":"time", "value":time, "type":"f" } )
        time.grid(row=row, column=column, sticky=W)
        column=0
        row+=1
        label = Label(top, text="show coordinate system")
        label.grid(row=row, column=column, sticky=W)
        column+=1
        coord = IntVar()
        coord.set(self.sg.showCoordinateSystem)
        coordck = Checkbutton(top, variable=coord)
        entries.append( { "object":self.sg, "name":"showCoordinateSystem", "value":coord, "type":"b" } )
        coordck.grid(row=row, column=column, sticky=W)
        column=0
        row+=1

        button = Button(top, text="Apply", command=lambda: self.apply(top, entries, True))
        button.grid(row=row, column=column, sticky=W)
        column+=1
        button = Button(top, text="Cancel", command=lambda: self.apply(top, entries, False))
        button.grid(row=row, column=column, sticky=W)

    def apply(self, top, entries, apply=False):
        if apply is True:
            for entry in entries:
                value = entry["value"].get()
                if entry["type"]=="f":
                    value = float(value)
                elif entry["type"]=="b":
                    value = bool(value)
                elif entry["type"]=="s":
                    value = str(value)
                setattr(entry["object"], entry["name"], value)
                val=getattr(entry["object"], entry["name"])
                print("set", entry["name"], "to", val)
        if isinstance(top, Frame):
            self.settingsBrowser=False
        top.destroy()
        self.guiUpdate()

    def configureCanvas(self, event):
        self.width = self.winfo_width()-2
        self.height = self.winfo_height()-2
        print("TkGUI(): reinitialize camera width/height")
        self.cam.width = self.width
        self.cam.height = self.height
        pass

    def createViewer(self):
        canvas = Canvas(self.content)
        self.canvas = canvas
        self.content.bind("<Configure>", self.configureCanvas)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        canvas.bind("<Button-1>", self.canvasInteract.start)
        canvas.bind("<Button-2>", self.canvasInteract.start)
        canvas.bind("<B1-Motion>", self.canvasInteract.rotate)
        canvas.bind("<B2-Motion>", self.canvasInteract.walk)
        canvas.bind("<ButtonRelease-1>", self.canvasInteract.release)
        canvas.bind("<ButtonRelease-2>", self.canvasInteract.release)
        pass

class CanvasInteract():

    def __init__(self, gui, cam):
        self.cam=cam
        self.gui=gui
        self.initial=[]
        self.sg=None
        # we did not yet get a camera
        if cam is None or cam.parent is None:
            return
        else:
            self.camera(cam)

    def camera(self, cam):
        self.cam=cam
        self.sg=cam.parent

    def state(self):
        self.zBuffering=self.sg.zBuffering
        self.polyOnlyGrid=self.sg.polyOnlyGrid
        self.polyOnlyPoint=self.sg.polyOnlyPoint
        self.camUpdate=self.cam.updateFunction

    def restore(self):
        print("restore, zBuffering", self.zBuffering, "polyOnlyGrid", self.polyOnlyGrid)
        self.sg.zBuffering=self.zBuffering
        self.sg.polyOnlyGrid=self.polyOnlyGrid
        self.sg.polyOnlyPoint=self.polyOnlyPoint
        # do not update camera update function! - if user moved the camera, the camera
        # should be fix there and animation can't continue.
        #self.cam.updateFunction=self.camUpdate
        self.isShowing=True

    def start(self, event=None):
        print("start")
        if event is not None:
            self.state()
            self.sg.zBuffering=False
            self.sg.polyOnlyGrid=True
            # deactivate camera update function (used when playing):
            self.cam.updateFunction=None
            widget = event.widget # Get handle to canvas
            # Convert screen coordinates to canvas coordinates
            x = event.x
            y = event.y
            self.camInitialX = self.cam.x
            self.camInitialY = self.cam.y
            self.camInitialZ = self.cam.z
            self.azimuth     = atan2(self.cam.y, self.cam.x)
            self.initial = (x, y)
            print("select:", x, y)
            self.gui.isPlaying=False
            self.gui.isShowing=True

    # attention: these event calls do NOT die on errors! Must use try & exit
    def rotate(self, event=None):
        print("rotate")
        if event is not None:
            widget = event.widget
            x = event.x
            y = event.y
            dx = (x-self.initial[0])/800*90
            dy = (y-self.initial[1])/600*90
            (self.cam.x, self.cam.y, self.cam.z) = self.cam.rotate( (self.camInitialX, self.camInitialY, self.camInitialZ), -1*dx, -1*dy )
            print("rotate delta:", dx, dy)
            self.gui.isShowing=True

    # attention: these event calls do NOT die on errors! Must use try & exit
    def walk(self, event=None):
        print("walk")
        if event is not None:
            widget = event.widget
            x = event.x
            y = event.y
            dx = (x-self.initial[0])/1000.0
            dy = (y-self.initial[1])/1000.0
            if abs(dy)>1e-06:     # otherwise div/0
                # something crashed the app here... - async new set of self.cam.XYZ?
                # I think more that one poligone is going crazy and almost reaches
                # infinity + or - and therefore polyfill has a lot of work to do.
                # kind of works now as of 2021-03-21 ph
                self.cam.x = (-1*dy)*self.camInitialX+(self.camInitialX-self.cam.x0)      # TODO: old, but need to check: div-0 at (2,0.4,0.0)
                self.cam.y = (-1*dy)*self.camInitialY+(self.camInitialY-self.cam.y0)
                self.cam.z = (-1*dy)*self.camInitialZ+(self.camInitialZ-self.cam.z0)
                pass
            print("walk delta:", dx, dy)
            self.gui.isShowing=True

    def release(self, event=None):
        print("release")
        self.restore()
        self.gui.isShowing=True

def main():
    gui = SingulersumGUI()
    gui.mainloop()

exit(main())
