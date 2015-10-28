# XML Parser/Data Access Object C:\Users\wgest\Desktop\ProjectR\Roguenaissance\sound.py
"""AUTO-GENERATED Source file for C:\\Users\\wgest\\Desktop\\ProjectR\\Roguenaissance\\sound.py"""
import xml.sax
import Queue
import Q2API.xml.base_xml

rewrite_name_list = ("name", "value", "attrs", "flatten_self", "flatten_self_safe_sql_attrs", "flatten_self_to_utf8", "children")

def process_attrs(attrs):
    """Process sax attribute data into local class namespaces"""
    if attrs.getLength() == 0:
        return {}
    tmp_dict = {}
    for name in attrs.getNames():
        tmp_dict[name] = attrs.getValue(name)
    return tmp_dict

def clean_node_name(node_name):
    clean_name = node_name.replace(":", "_").replace("-", "_").replace(".", "_")

    if clean_name in rewrite_name_list:
        clean_name = "_" + clean_name + "_"

    return clean_name

class filename_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'sounds', u'sound']
        Q2API.xml.base_xml.XMLNode.__init__(self, "filename", attrs, None, [])

class ident_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'sounds', u'sound']
        Q2API.xml.base_xml.XMLNode.__init__(self, "ident", attrs, None, [])

class music_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'sounds']
        self.ident = []
        self.filename = []
        Q2API.xml.base_xml.XMLNode.__init__(self, "music", attrs, None, [])

class sound_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'sounds']
        self.ident = []
        self.filename = []
        Q2API.xml.base_xml.XMLNode.__init__(self, "sound", attrs, None, [])

class sounds_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 1
        self.path = [None]
        self.sound = []
        self.music = []
        Q2API.xml.base_xml.XMLNode.__init__(self, "sounds", attrs, None, [])

class NodeHandler(xml.sax.handler.ContentHandler):
    """SAX ContentHandler to map XML input class/object"""
    def __init__(self, return_q):     # overridden in subclass
        self.obj_depth = [None]
        self.return_q = return_q
        self.last_processed = None
        self.char_buffer = []
        xml.sax.handler.ContentHandler.__init__(self)   # superclass init

    def startElement(self, name, attrs): # creating the node along the path being tracked
        """Override base class ContentHandler method"""
        name = clean_node_name(name)
        p_attrs = process_attrs(attrs)

        if name == "":
            raise ValueError, "XML Node name cannot be empty"

        elif name == "sound":
            self.obj_depth.append(sound_q2class(p_attrs))

        elif name == "sounds":
            self.obj_depth.append(sounds_q2class(p_attrs))

        elif name == "ident":
            self.obj_depth.append(ident_q2class(p_attrs))

        elif name == "music":
            self.obj_depth.append(music_q2class(p_attrs))

        elif name == "filename":
            self.obj_depth.append(filename_q2class(p_attrs))

        self.char_buffer = []
        self.last_processed = "start"

    def endElement(self, name): # need to append the node that is closing in the right place
        """Override base class ContentHandler method"""
        name = clean_node_name(name)

        if (len(self.char_buffer) != 0) and (self.last_processed == "start"):
            self.obj_depth[-1].value = "".join(self.char_buffer)

        if name == "":
            raise ValueError, "XML Node name cannot be empty"

        elif name == "sound":
            self.obj_depth[-2].sound.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "sounds":
            # root node is not added to a parent; stays on the "stack" for the return_object
            self.char_buffer = []
            self.last_processed = "end"
            return

        elif name == "ident":
            self.obj_depth[-2].ident.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "music":
            self.obj_depth[-2].music.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "filename":
            self.obj_depth[-2].filename.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        self.last_processed = "end"


    def characters(self, in_chars):
        """Override base class ContentHandler method"""
        self.char_buffer.append(in_chars)

    def endDocument(self):
        """Override base class ContentHandler method"""
        self.return_q.put(self.obj_depth[-1])

def obj_wrapper(xml_stream):
    """Call the handler against the XML, then get the returned object and pass it back up"""
    try:
        return_q = Queue.Queue()
        xml.sax.parseString(xml_stream, NodeHandler(return_q))
        return (True, return_q.get())
    except Exception, e:
        return (False, (Exception, e))


