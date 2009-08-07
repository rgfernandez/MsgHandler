import logging

import xml.dom.minidom as minidom

log = logging.getLogger('xmlutil')

#---------- xml tools
def parse_string(s):
    """Parse string s and return it as an XmlWrapper."""
    return XmlWrapper(minidom.parseString(s))

#------------------------------------------------------------------------------
class XmlWrapper:
    """Simple wrapper to make it easy to deal with XML junk.

    XmlWrapper let you access Xml DOM structure as attributes of the
    node. For example:

    <parent>
        <child>child_text</child>
    </parent>

    x = XmlWrapper(minidom.parseString(...))
    x.parent.child.get_text() -> "child_text"
    """
    def __init__(self, node):
        self.node = node

    def __str__(self):
        if self.node.nodeType == self.node.TEXT_NODE:
            return self.node.data
        else:
            return self.node.nodeName

    def __iter__(self):
        return iter([XmlWrapper(i) 
                     for i in self.node.childNodes 
                     if i.nodeType == i.ELEMENT_NODE])
    
    def __getattr__(self, name):
        if self.node.attributes is not None and self.node.attributes.has_key(name):
            return self.node.attributes[name].value
        elts = self.node.getElementsByTagName(name)
        if len(elts) == 1:
            return XmlWrapper(elts[0])
        raise AttributeError()

    def __contains__(self, name):
        if (self.node.attributes is not None and \
            self.node.attributes.has_key(name)):
            return True
        elts = self.node.getElementsByTagName(name)
        if len(elts) == 1:
            return True
        return False
        
    def children(self):
        """Returns a list of all of the child tags."""
        l = []
        n = self.node.firstChild
        while n:
            l.append(XmlWrapper(n))
            n = n.nextSibling
        return l

    def ancestors(self):
        """Returns a list of all of the ancestors, root last."""
        l = []
        n = self.node.parentNode
        while n:
            l.append(XmlWrapper(n))
            n = n.parentNode
        return l
                
    def get_by_tag(self, name):
        """returns a list of all of the tag elements"""
        return [XmlWrapper(i) for i in self.node.getElementsByTagName(name)]

    def get_text(self):
	"""Get the text in between the tags."""
        rc = ""
        for node in self.node.childNodes:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
        return rc
