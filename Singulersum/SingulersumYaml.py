# 2021-03-22 ph Created
# 2021-04-02 ph version check for Singulersum and SingulersumYaml
# 2021-06-30 ph constants (constants section, all str, imported into sg)

"""
    class Singulersum.SingulersumYaml()

    2021-03-22 ph Created by Philipp Hasenfratz

    an importer for yaml based Singulersum scenery definition files.

    all yaml files should start with:
    yaml:
        application: Singulersum
        min-version: <singulersum-version-it's-made-for>
        min-yaml-specification: <yaml-class-version-it's-made-for>

    NOTE: callback event's are fired from Singulersum.py (when sg.yaml() is called)

    2021-06-30: new section "constants" that will import constants into sg namespace. All of them must be specified as string (and will be run through eval())
"""

# TODO: bad coding. yaml object must be defined in specific order. Eg. animation must
#       preceed the camera, otherwise the update function is not known when camera is
#       processed.
# TODO: same class version as yaml version currently displays error.

import struct
import yaml

from Singulersum.Debug import Debug

class SingulersumYaml(Debug):

    version = "2021-06-30"

    def __init__(self, parent, file=None, data=None):
        super().__init__()
        self.file = file
        self.data = data
        self.parent = parent
        self.namespace = { "yaml":{}, "sg":parent, "gui":{} }
        self.read(file=file, data=data)

    def read(self, file=None, data=None):
        content = None
        file_h = None
        if file is not None:
            file_h = open(file, "r")
            content = file_h
        if data is not None:
            content = data
        if content is None:
            self.debug("SingulversumYaml() did not get any content. file or data parameter missing or file empty?")
            exit(0)
        self.document = yaml.load(content, Loader=yaml.FullLoader)
        self.namespace["gui"]=self.document.pop("gui", None)
        self.namespace["constants"]=self.document.pop("constants", None)
        # import contants into sg (TODO: this should be done differently)
        for name in self.namespace["constants"]:
            val = self.namespace["constants"][name]
            val = eval(val, globals())
            setattr(self.parent.sg, name, val)
            self.debug("constant", name, "imported into SG with value:", val)
        if "gui" in self.namespace and self.namespace["gui"] is not None:
            self.namespaceSet(["gui", "versionOk"], True)
        self.namespace["yaml"]=self.document.pop("yaml", None)
        if self.checkVersion() is False:
            if "gui" in self.namespace and self.namespace["gui"] is not None:
                self.namespaceSet(["gui", "versionOk"], False)
        self.singulersum_build([], self.parent, self.document)
        self.debug("yaml file processed and objects initialized.")
        if file is not None:
            file_h.close()
        return self.namespace

    def singulersum_build(self, name, parent, document):
        sg = self.namespace["sg"]
        for item, value in document.items():
            nname = []
            nname.extend(name)
            nname.append(item)
            self.debug("nname", nname, "parent", str(parent))
            if isinstance(value, dict):
                if "type" in value:
                    self.namespaceSet(nname, self.singulersum_object(item, parent, value))
                else:
                    if item=="sg":
                        # parent stays parent
                        pass
                    else:
                        parent = getattr(parent, item)
                    self.singulersum_build(nname, parent, value)
            else:
                self.namespaceSet(nname, value)

    def singulersum_object(self, name, parent, value):
        sg = self.namespace["sg"]
        namespace = value
        namespace["name"] = name
        obj = None
        assert("type" in namespace)
        objtype = namespace.pop("type", None)    # delete the type
        update = namespace.pop("update", None)
        if update is not None:
            # update for all Miniverse objects (including Camera)
            # TODO: make this able to be non-sequential, so that update in yaml can be
            #       defined LATER than the object using it. Currently this brakes.
            namespace["update"]=self.namespace[update]

        # simple objects (inherit from BasicObject, don't have scale/size/x/y/z)
        # simple objects are directly imported into the parent context! So their
        # point definitions (like x,y,z for Dot or x1,y1,z1,x2,y2,z2 for Line) are in
        # scale of their parent context!
        if objtype=="dot":
            point = namespace.pop("point", None)
            if point is not None:
                namespace["x"] = point[0]
                namespace["y"] = point[1]
                namespace["z"] = point[2]
            obj=parent.dot( **namespace)

        elif objtype=="polygon":
            polygon = namespace.pop("points", None)
            obj = parent.polygon(*polygon, **namespace)

        elif objtype=="lines":
            """
            type: lines
            points: [ [0,0,0], [1,0,0], [1,1,0], [1,1,1] ]
            #OR
            lines: [ [0,0,0], [1,0,0], [1,0,0], [1,1,0], [1,1,0], [1,1,1] ]
            """
            lines = namespace.pop("lines", None)
            points = namespace.pop("points", None)
            if lines is not None:
                for i in range(0, len(lines), 2):
                    obj = parent.line(*lines[i], *lines[i+1])
            if points is not None:
                p0 = points[0]
                pl = p0
                for i in range(1, len(points)-1):
                    obj = parent.line(*pl, *points[i])
                    pl=points[i]
                obj=parent.line(*points[-1], *pl)

        elif objtype=="coordinatesystem":
            obj = parent.coordinateSystem(**namespace)

        # Miniversum objects (they have their own scale and are translated by x,y,z into
        # the parent context. They also have a "size" which is then scaled to the parent
        # into the parent context; this means: if parent scaleX/Y/Z=5.0 and the object
        # here is created with a scale: 3.0, then it covers 3/5 of the space of the
        # parent)

        elif objtype=="stl":
            """
            type: stl
            file: ../stl/Utah_teapot.stl
            x: -1.0
            y: -1.0
            z: 0.0
            """
            file = namespace.pop("file", None)
            if file is None:
                self.debug("stl needs at least 'file'!")
                exit(0)
            obj=parent.stl(file=file, **namespace)

        elif objtype=="function":
            obj=parent.function(**namespace)

        elif objtype=="object":
            obj=parent.object(**namespace)

        elif objtype=="cube":
            obj = parent.cube(**namespace)

        elif objtype=="sphere":
            obj = parent.sphere(**namespace)

        elif objtype=="point":
            obj = parent.point(**namespace)

        elif objtype=="plane":
            obj = parent.plane(**namespace)

        # camera and animations:

        elif objtype=="camera":
            position = namespace.pop("position", None)
            lookat = namespace.pop("lookat", None)
            if position is None:
                self.debug("camera needs a 'position'")
                exit(0)
            if lookat is None:
                self.debug("camera needs a 'lookat'")
                exit(0)
            obj=parent.camera(position[0], position[1], position[2], lookat[0], lookat[1], lookat[2], **namespace)
            pass

        elif objtype=="animation":
            """
                type: animation
                stop: time>1.0
                begin: [1.2, 2.0, 1.0]
                end: [1.6, 0.1, 0.5]
                x: begin[0] + (time*(end[0] - begin[0]))
                y: begin[1] + (time*(end[1] - begin[1]))
                z: begin[2] + (time*(end[2] - begin[2]))
            """
            obj=lambda animate_object: animate_object.animation(**namespace)

        else:
            self.debug("SingulversumYaml() got object type "+str(objtype)+" which it can't handle. Must be one of ['stl', 'animation', 'camera', 'point']")
            exit(0)
        return obj

    def namespaceSet(self, name=[], value=None):
        container = self.namespace
        for i in range(len(name)-1):
            if isinstance(container, dict):
                container = container[name[i]]
            else:
                container = getattr(container, name[i])
        if isinstance(container, dict):
            container[name[-1]] = value
        else:
            setattr(container, name[-1], value)

    def getVersion(self):
        return SingulersumYaml.version

    def checkVersion(self):
        ok=True
        if "yaml" not in self.namespace or self.namespace["yaml"] is None:
            return True
        yaml = self.namespace["yaml"]
        if "min-yaml-version" in yaml:
            fileversion = str(yaml["min-yaml-version"])
            if fileversion>self.getVersion():
                self.debug("WARN: yaml file needs SingulersumYaml class to be at least "+fileversion+", but class is version "+self.getVersion())
                ok=False
        else:
            self.debug("INFO: yaml file does not have a min-yaml-version identifier.")
        if "min-version" in yaml:
            fileversion = str(yaml["min-version"])
            if fileversion>self.parent.getVersion():
                self.debug("WARN: yaml-file is made for a newer version of Singulersum! Class needs to be at least "+fileversion+", but class is version "+self.getVersion())
                ok=False
        else:
            self.debug("INFO: yaml file does not have a min-version identifier.")
        if "application" in yaml:
            if yaml["application"].lower()!="singulersum":
                self.debug("WARNING: is this yaml made for Singulersum? There's no application identifier in yaml")

        return ok
