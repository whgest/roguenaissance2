# XML Parser/Data Access Object C:\Users\COMPY-MKIII\Desktop\Code\Roguenaissance2.0\skills.py
"""AUTO-GENERATED Source file for C:\\Users\\COMPY-MKIII\\Desktop\\Code\\Roguenaissance2.0\\skills.py"""
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

class continuous_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 4
        self.path = [None, u'skills', u'skill', u'effect']
        Q2API.xml.base_xml.XMLNode.__init__(self, "continuous", attrs, None, [])

class duration_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 4
        self.path = [None, u'skills', u'skill', u'effect']
        Q2API.xml.base_xml.XMLNode.__init__(self, "duration", attrs, None, [])

class magnitude_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 4
        self.path = [None, u'skills', u'skill', u'effect']
        Q2API.xml.base_xml.XMLNode.__init__(self, "magnitude", attrs, None, [])

class modifier_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 4
        self.path = [None, u'skills', u'skill', u'effect']
        Q2API.xml.base_xml.XMLNode.__init__(self, "modifier", attrs, None, [])

class type_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 4
        self.path = [None, u'skills', u'skill', u'effect']
        Q2API.xml.base_xml.XMLNode.__init__(self, "type", attrs, None, [])

class animation_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        Q2API.xml.base_xml.XMLNode.__init__(self, "animation", attrs, None, [])

class aoe_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        Q2API.xml.base_xml.XMLNode.__init__(self, "aoe", attrs, None, [])

class damage_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        Q2API.xml.base_xml.XMLNode.__init__(self, "damage", attrs, None, [])

class effect_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        self.continuous = []
        self.magnitude = []
        self.duration = []
        self.modifier = []
        self.type = []
        Q2API.xml.base_xml.XMLNode.__init__(self, "effect", attrs, None, [])

class mp_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        Q2API.xml.base_xml.XMLNode.__init__(self, "mp", attrs, None, [])

class narration_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        Q2API.xml.base_xml.XMLNode.__init__(self, "narration", attrs, None, [])

class prompt_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        Q2API.xml.base_xml.XMLNode.__init__(self, "prompt", attrs, None, [])

class range_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        Q2API.xml.base_xml.XMLNode.__init__(self, "range", attrs, None, [])

class stat_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        Q2API.xml.base_xml.XMLNode.__init__(self, "stat", attrs, None, [])

class target_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'skills', u'skill']
        Q2API.xml.base_xml.XMLNode.__init__(self, "target", attrs, None, [])

class skill_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'skills']
        self.stat = []
        self.prompt = []
        self.target = []
        self.effect = []
        self.aoe = []
        self.damage = []
        self.range = []
        self.animation = []
        self.mp = []
        self.narration = []
        Q2API.xml.base_xml.XMLNode.__init__(self, "skill", attrs, None, [])

class skills_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 1
        self.path = [None]
        self.skill = []
        Q2API.xml.base_xml.XMLNode.__init__(self, "skills", attrs, None, [])

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

        elif name == "stat":
            self.obj_depth.append(stat_q2class(p_attrs))

        elif name == "prompt":
            self.obj_depth.append(prompt_q2class(p_attrs))

        elif name == "target":
            self.obj_depth.append(target_q2class(p_attrs))

        elif name == "effect":
            self.obj_depth.append(effect_q2class(p_attrs))

        elif name == "skills":
            self.obj_depth.append(skills_q2class(p_attrs))

        elif name == "continuous":
            self.obj_depth.append(continuous_q2class(p_attrs))

        elif name == "aoe":
            self.obj_depth.append(aoe_q2class(p_attrs))

        elif name == "magnitude":
            self.obj_depth.append(magnitude_q2class(p_attrs))

        elif name == "damage":
            self.obj_depth.append(damage_q2class(p_attrs))

        elif name == "range":
            self.obj_depth.append(range_q2class(p_attrs))

        elif name == "animation":
            self.obj_depth.append(animation_q2class(p_attrs))

        elif name == "mp":
            self.obj_depth.append(mp_q2class(p_attrs))

        elif name == "narration":
            self.obj_depth.append(narration_q2class(p_attrs))

        elif name == "duration":
            self.obj_depth.append(duration_q2class(p_attrs))

        elif name == "skill":
            self.obj_depth.append(skill_q2class(p_attrs))

        elif name == "modifier":
            self.obj_depth.append(modifier_q2class(p_attrs))

        elif name == "type":
            self.obj_depth.append(type_q2class(p_attrs))

        self.char_buffer = []
        self.last_processed = "start"

    def endElement(self, name): # need to append the node that is closing in the right place
        """Override base class ContentHandler method"""
        name = clean_node_name(name)

        if (len(self.char_buffer) != 0) and (self.last_processed == "start"):
            self.obj_depth[-1].value = "".join(self.char_buffer)

        if name == "":
            raise ValueError, "XML Node name cannot be empty"

        elif name == "stat":
            self.obj_depth[-2].stat.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "prompt":
            self.obj_depth[-2].prompt.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "target":
            self.obj_depth[-2].target.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "effect":
            self.obj_depth[-2].effect.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "skills":
            # root node is not added to a parent; stays on the "stack" for the return_object
            self.char_buffer = []
            self.last_processed = "end"
            return

        elif name == "continuous":
            self.obj_depth[-2].continuous.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "aoe":
            self.obj_depth[-2].aoe.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "magnitude":
            self.obj_depth[-2].magnitude.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "damage":
            self.obj_depth[-2].damage.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "range":
            self.obj_depth[-2].range.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "animation":
            self.obj_depth[-2].animation.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "mp":
            self.obj_depth[-2].mp.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "narration":
            self.obj_depth[-2].narration.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "duration":
            self.obj_depth[-2].duration.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "skill":
            self.obj_depth[-2].skill.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "modifier":
            self.obj_depth[-2].modifier.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "type":
            self.obj_depth[-2].type.append(self.obj_depth[-1]) #  make this object a child of the next object up...
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


