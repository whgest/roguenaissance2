# XML Parser/Data Access Object C:\Users\COMPY-MKIII\Desktop\Code\Roguenaissance2.0\actors.py
"""AUTO-GENERATED Source file for C:\\Users\\COMPY-MKIII\\Desktop\\Code\\Roguenaissance2.0\\actors.py"""
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

class agility_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "agility", attrs, None, [])

class ai_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "ai", attrs, None, [])

class armor_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "armor", attrs, None, [])

class attack_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "attack", attrs, None, [])

class character_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "character", attrs, None, [])

class color_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "color", attrs, None, [])

class defense_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "defense", attrs, None, [])

class descr_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "descr", attrs, None, [])

class immunities_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "immunities", attrs, None, [])

class magic_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "magic", attrs, None, [])

class maxhp_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "maxhp", attrs, None, [])

class maxmp_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "maxmp", attrs, None, [])

class move_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "move", attrs, None, [])

class resistance_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "resistance", attrs, None, [])

class skills_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "skills", attrs, None, [])

class weapon_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 3
        self.path = [None, u'actors', u'heroclass']
        Q2API.xml.base_xml.XMLNode.__init__(self, "weapon", attrs, None, [])

class actor_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'actors']
        self.agility = []
        self.move = []
        self.magic = []
        self.descr = []
        self.color = []
        self.maxmp = []
        self.character = []
        self.attack = []
        self.resistance = []
        self.ai = []
        self.defense = []
        self.maxhp = []
        self.skills = []
        self.immunities = []
        Q2API.xml.base_xml.XMLNode.__init__(self, "actor", attrs, None, [])

class heroclass_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 2
        self.path = [None, u'actors']
        self.agility = []
        self.move = []
        self.magic = []
        self.descr = []
        self.color = []
        self.maxmp = []
        self.weapon = []
        self.armor = []
        self.character = []
        self.attack = []
        self.resistance = []
        self.ai = []
        self.defense = []
        self.maxhp = []
        self.skills = []
        self.immunities = []
        Q2API.xml.base_xml.XMLNode.__init__(self, "heroclass", attrs, None, [])

class actors_q2class(Q2API.xml.base_xml.XMLNode):
    def __init__(self, attrs):
        self.level = 1
        self.path = [None]
        self.actor = []
        self.heroclass = []
        Q2API.xml.base_xml.XMLNode.__init__(self, "actors", attrs, None, [])

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

        elif name == "agility":
            self.obj_depth.append(agility_q2class(p_attrs))

        elif name == "move":
            self.obj_depth.append(move_q2class(p_attrs))

        elif name == "magic":
            self.obj_depth.append(magic_q2class(p_attrs))

        elif name == "descr":
            self.obj_depth.append(descr_q2class(p_attrs))

        elif name == "color":
            self.obj_depth.append(color_q2class(p_attrs))

        elif name == "maxmp":
            self.obj_depth.append(maxmp_q2class(p_attrs))

        elif name == "weapon":
            self.obj_depth.append(weapon_q2class(p_attrs))

        elif name == "armor":
            self.obj_depth.append(armor_q2class(p_attrs))

        elif name == "character":
            self.obj_depth.append(character_q2class(p_attrs))

        elif name == "attack":
            self.obj_depth.append(attack_q2class(p_attrs))

        elif name == "actor":
            self.obj_depth.append(actor_q2class(p_attrs))

        elif name == "resistance":
            self.obj_depth.append(resistance_q2class(p_attrs))

        elif name == "heroclass":
            self.obj_depth.append(heroclass_q2class(p_attrs))

        elif name == "ai":
            self.obj_depth.append(ai_q2class(p_attrs))

        elif name == "defense":
            self.obj_depth.append(defense_q2class(p_attrs))

        elif name == "actors":
            self.obj_depth.append(actors_q2class(p_attrs))

        elif name == "maxhp":
            self.obj_depth.append(maxhp_q2class(p_attrs))

        elif name == "skills":
            self.obj_depth.append(skills_q2class(p_attrs))

        elif name == "immunities":
            self.obj_depth.append(immunities_q2class(p_attrs))

        self.char_buffer = []
        self.last_processed = "start"

    def endElement(self, name): # need to append the node that is closing in the right place
        """Override base class ContentHandler method"""
        name = clean_node_name(name)

        if (len(self.char_buffer) != 0) and (self.last_processed == "start"):
            self.obj_depth[-1].value = "".join(self.char_buffer)

        if name == "":
            raise ValueError, "XML Node name cannot be empty"

        elif name == "agility":
            self.obj_depth[-2].agility.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "move":
            self.obj_depth[-2].move.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "magic":
            self.obj_depth[-2].magic.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "descr":
            self.obj_depth[-2].descr.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "color":
            self.obj_depth[-2].color.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "maxmp":
            self.obj_depth[-2].maxmp.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "weapon":
            self.obj_depth[-2].weapon.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "armor":
            self.obj_depth[-2].armor.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "character":
            self.obj_depth[-2].character.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "attack":
            self.obj_depth[-2].attack.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "actor":
            self.obj_depth[-2].actor.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "resistance":
            self.obj_depth[-2].resistance.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "heroclass":
            self.obj_depth[-2].heroclass.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "ai":
            self.obj_depth[-2].ai.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "defense":
            self.obj_depth[-2].defense.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "actors":
            # root node is not added to a parent; stays on the "stack" for the return_object
            self.char_buffer = []
            self.last_processed = "end"
            return

        elif name == "maxhp":
            self.obj_depth[-2].maxhp.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "skills":
            self.obj_depth[-2].skills.append(self.obj_depth[-1]) #  make this object a child of the next object up...
            self.obj_depth[-2].children.append(self.obj_depth[-1]) #  put a reference in the children list as well
            self.obj_depth.pop() # remove this node from the list, processing is complete
            self.char_buffer = []

        elif name == "immunities":
            self.obj_depth[-2].immunities.append(self.obj_depth[-1]) #  make this object a child of the next object up...
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


