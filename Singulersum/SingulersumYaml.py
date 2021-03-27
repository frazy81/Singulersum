# 2021-03-22 ph Created

"""
    class Singulersum.SingulersumYaml()

    2021-03-22 ph Created by Philipp Hasenfratz

    an importer for yaml based Singulersum scenery definition files.

    NOTE: callback event's are fired from Singulersum.py (when sg.yaml() is called)
"""

# TODO: still all in Singulersum instead of object(Miniverse)!
# TODO: bad coding. yaml object must be defined in specific order. Eg. animation must
#       preceed the camera, otherwise the update function is not known when camera is
#       processed.

import struct
import yaml

from Singulersum.Debug import Debug

class SingulersumYaml(Debug):

    def __init__(self, parent, file=None, data=None):
        super().__init__()
        self.file = file
        self.data = data
        self.parent = parent
        self.namespace = { "sg":parent, "gui":{} }
        self.document = self.read(file=file, data=data)

    def read(self, file=None, data=None):
        content = None
        if file is not None:
            content = open(file, "r")
        if data is not None:
            content = data
        if content is None:
            self.debug("SingulversumYaml() did not content. file or data parameter missing or file empty?")
            exit(0)
        self.document = yaml.load(content, Loader=yaml.FullLoader)
        self.namespace["gui"]=self.document.pop("gui", None)
        self.singulersum_build([], self.parent, self.document)
        return self.namespace

    def singulersum_build(self, name, parent, document):
        sg = self.namespace["sg"]
        for item, value in document.items():
            nname = []
            nname.extend(name)
            nname.append(item)
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
        objtype = namespace["type"]
        namespace.pop("type", None)    # delete the type

        if objtype=="function":
            obj=parent.function(**namespace)

        elif objtype=="point":
            point = namespace.pop("point", None)
            if point is None:
                self.debug("point needs a variable 'point'!")
                exit(0)
            obj = parent.object(**namespace)
            obj=obj.point( (point[0], point[1], point[2]), **namespace)

        elif objtype=="camera":
            position = namespace.pop("position", None)
            lookat = namespace.pop("lookat", None)
            update = namespace.pop("update", None)
            if position is None:
                self.debug("camera needs a 'position'")
                exit(0)
            if lookat is None:
                self.debug("camera needs a 'lookat'")
                exit(0)
            if update is not None:
                namespace["update"]=self.namespace[update]
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

        elif objtype=="stl":
            """
            type: stl
            file: ../stl/Utah_teapot.stl
            place: [-1.0, -1.0, 0]
            """
            file = namespace.pop("file", None)
            if file is None:
                self.debug("stl needs at least 'file'!")
                exit(0)
            obj=parent.stl(file=file, **namespace)

        elif objtype=="lines":
            """
            type: lines
            points: [ [0,0,0], [1,0,0], [1,1,0], [1,1,1] ]
            #OR
            lines: [ [0,0,0], [1,0,0], [1,0,0], [1,1,0], [1,1,0], [1,1,1] ]
            """
            lines = namespace.pop("lines", None)
            points = namespace.pop("points", None)
            obj = parent.object(**namespace)
            if lines is not None:
                for i in range(0, len(lines), 2):
                    obj.line(lines[i], lines[i+1])
            if points is not None:
                p0 = points[0]
                pl = p0
                for i in range(1, len(points)-1):
                    obj.line(pl, points[i])
                    pl=points[i]
                obj.line(points[-1], pl)

        elif objtype=="cube":
            obj = parent.cube(**namespace)

        elif objtype=="sphere":
            obj = parent.sphere(**namespace)

        elif objtype=="polygon":
            polygon = namespace.pop("points", None)
            obj = parent.object(**namespace)
            obj = obj.polygon(*polygon, **namespace)

        elif objtype=="coordinatesystem":
            obj = parent.coordinateSystem(**namespace)

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
