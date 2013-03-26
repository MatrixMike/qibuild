## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.


""" This is just a set of convenience functions to be used with
`The ElemtTree XML API <http://docs.python.org/library/xml.etree.elementtree.html>`_

"""

HAS_LXML = False
from xml.etree import ElementTree as etree

def indent(elem, level=0):
    """ Poor man's pretty print for elementTree

    """
    # Taken from http://infix.se/2007/02/06/gentlemen-indent-your-xml
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "  "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def raise_parse_error(message, xml_path=None, tree=None):
    """ Raise a nice parsing error about the given
    tree element

    """
    mess = ""
    if xml_path:
        mess += "Error when parsing '%s'\n" % xml_path
    if tree is not None:
        as_str = etree.tostring(tree)
        mess += "Could not parse:\t%s\n" % as_str
    mess += message
    raise Exception(mess)

def parse_bool_attr(tree, name, default=False):
    """ Parse a boolean attribute of an element

      * Return True is the attribute exists and is
        "1" or "true".
      * Returns False if the attribute exist and is
        "0" or "false"
      * If the attribute does not exists and default is given,
        returns `default`
      * Otherwise raise an exception

    """
    res = tree.get(name)
    if res in ["true", "1"]:
        return True
    if res in ["false", "0"]:
        return False
    if res is not None:
        raise_parse_error("Expecting value in [true, false, 0, 1] "
            "for attribute %s" % name,
            tree=tree)
    return default

def parse_int_attr(tree, name, default=None):
    """ Parse a integer from a xml element

    """
    res = tree.get(name)
    if not res:
        if default is None:
            mess = "node %s must have a '%s' attribute" % (tree.tag, name)
            raise_parse_error(mess, tree=tree)
        else:
            return default
    try:
        res = int(res)
    except ValueError:
        mess = "Could not parse attribue '%s' from node %s \n" % (name, tree.tag)
        mess += "Excepting an integer, got: %s" % res
        raise_parse_error(mess, tree=tree)
    return res


def parse_list_attr(tree, name):
    """ Parse a list attribute
    Return an empty list if the attribute is not found

    """
    res = tree.get(name, "")
    return res.split()

def parse_required_attr(tree, name, xml_path=None):
    """ Raise an exception if an attribute it missing in a
    Node
    """
    value = tree.get(name)
    if not value:
        mess = "node %s must have a '%s' attribute" % (tree.tag, name)
        raise_parse_error(mess, xml_path=xml_path)
    return value



def read(xml_path):
    """ Return a etree object from an xml path

    """
    tree = etree.ElementTree()
    try:
        tree.parse(xml_path)
    except Exception, e:
        raise_parse_error(str(e), xml_path=xml_path)
    return tree


def write(xml_obj, output):
    """ Write an xml object to the given path

    If xml_obj is not an ElementTree but an
    Element,  we will build a tree just to write it.

    The result of the writing will always be nicely
    indented
    """
    tree = None
    root = None
    if isinstance(xml_obj, etree.ElementTree):
        tree = xml_obj
        root = xml_obj.getroot()
    else:
        tree = etree.ElementTree(element=xml_obj)
        root = xml_obj
    indent(root)
    tree.write(output)


class XMLParser(object):
    """ This class provides an easy interface to parse XML tags element by element.
    To work with it, you must inherit from this class and define methods on tags
    you want to parse.

    Example:

    .. code-block:: xml

        <foo>
          <bar attr1="fooooooo">Some content!</bar>
          <easy><win>Yes!</win></easy>
          <win>Nooooooooooooooooooooooooooooooooo!</win>
        </foo>

    Root of the XML is foo. When :func:`XMLParser.parse` is called, it
    will try to call ``_parse_TAGNAME`` where tag name is the actual name of the
    tag you want to parse. It takes the element as a parameter.

    You can call parse recursively (from `_parse_TAGNAME` functions) to parse
    sub-trees. You always have :member:`backtrace` to know from where you came
    in ``_parse_TAGNAME``. Here is a complete example of a usage on XML above:

    class Foo(XMLParser):
        def _parse_bar(self, element):
            print 'Attribute attr1:', element.attrib['attr1']
            print 'Content:', element.text

        def _parse_easy(self, element):
            self.parse(element)

        def _parse_win(self, element):
            # We only want to parse win tag in easy tag.
            if 'easy' in self.backtrace:
                print 'Win text:', element.text

    A parser class should not have an attribute with the name of an xml
    attribute unless it wants to grab them.

    """

    def __init__(self, target):
        """ Initialize the XMLParser with a root element.

        :param root: The root element.

        """
        self.target = target
        self._root = None
        self.backtrace = list()

    def parse(self, root):
        """ This function iterates on the children of the element (or the root if an
        element is not given) and call ``_parse_TAGNAME`` functions.

        :param root: The root element that should be parsed.

        """
        self._root = root
        self._parse_prologue()
        self._parse_attributes()
        self.backtrace.append(root.tag)
        for child in root:
            method_name = "_parse_{tagname}".format(tagname = child.tag)
            try:
                method = getattr(self.__class__, method_name)
            except AttributeError as err:
                self._parse_unknown_element(child, err)
                continue
            if method.func_code.co_argcount != 2:
                mess = "Handler for tag `%s' must take" % child.tag
                mess += " two arguments. (method: %s, takes " % method_name
                mess += "%d argument(s))" % method.func_code.co_argcount
                raise TypeError(mess)
            method(self, child)
        self.backtrace.pop()
        self._parse_epilogue()

    def _parse_unknown_element(self, element, err):
        """ This function will by default ignore unknown elements. You can overload
        it to change its behavior.

        :param element: The unknown element.
        :param err: The error message.

        """
        pass

    def _parse_prologue(self):
        """ You can overload this function to do something before the beginning of
        parsing of the file.

        """
        pass

    def _parse_epilogue(self):
        """ You can overload this function to do something after the end of the
        parsing of the file.

        """
        pass

    def _parse_attributes(self):
        """ You can overload this function to get attribute of root before parsing
        its children. Attributes will be a dictionnary.

        """
        for attr in self._root.attrib:
            if hasattr(self.target, attr):
                default_value = getattr(self.target, attr)
                type_value = type(default_value)
                new_value = self._get_value_for_type(type_value,
                        self._root.attrib[attr])
                setattr(self.target, attr, new_value)

        self._post_parse_attributes()

    def _post_parse_attributes(self):
        """ You can overload this function to add post treatment to parsing of
        attributes. Attributes will be a dictionnary.

        """
        pass

    def _get_value_for_type(self, type_value, value):
        if type_value == bool:
            if value.lower() in ["true", "1"]:
                return True
            if value.lower() in ["false", "0"]:
                return False
            mess = "Waiting for a boolean but value is '%s'." % value
            raise Exception(mess)

        return value

    def check_needed(self, attribute_name, node_name=None, value=None):
        if node_name is None:
            node_name = self.target.__class__.__name__.lower()

        if value is None:
            if hasattr(self.target, attribute_name):
                value = getattr(self.target, attribute_name)

        if value is None:
            mess = "Node '%s' must have a '%s' attribute." % (node_name,
                                                               attribute_name)
            raise Exception(mess)