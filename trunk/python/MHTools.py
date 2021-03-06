import logging
import logging.config

import sys
import os
from signal import SIGTERM
import errno
import time

import xml.dom.minidom as minidom

#---------- os.path tools
def project_path(cur_path=''):
    """Return path to trunk."""
    if not cur_path:
        cur_path = __file__
    real_path = os.path.realpath(cur_path)
    # path of upper-level directory
    upper_folder = os.path.split(real_path)[0]
    # path of topmost-level directory (trunk)
    return os.path.split(upper_folder)[0]

#---------- logging tools
def get_logger(logger_name):
    """Return object for logging."""
    logger_path = os.path.join(PATH, 'config', "logging.conf")
    if os.path.exists(logger_path):
        logging.config.fileConfig(logger_path)
        logging.info("%s started" % logger_name)
    return logging.getLogger(logger_name)

#---------- daemon tools
def stopd(pidfile=''):
    """Kill processes written on pid files."""
    # disclaimer: taken from the internet (will search for the link)
    pidfile = os.path.basename(pidfile)
    pidfile = os.path.join(PATH, 'log', pidfile)
    if not os.path.exists(pidfile):
        raise ConfigError("%s not found" % pidfile)
    pf = file(pidfile, 'r')
    pids = pf.read().split()
    log.debug('stopping pids %s' % ' '.join(pids))
    pf.close()
    
    errors = []
    for elem in pids:
        pid = int(elem.strip())
        try:
            while 1:
                os.kill(pid,SIGTERM)
                time.sleep(1)
            pids.remove(elem)
        except OSError, e:
            errors.append(str(e))
            if e.errno == errno.ESRCH:
                # process not found
                pids.remove(elem)
        except ValueError:
            # elem not in pids. do nothing
            pass
    pf = file(pidfile, 'w')
    pf.write('\n'.join(pids)+'\n')
    pf.close()
    return errors

def startd(pidfile=''):
    """Daemonize process and write pid into file."""
    # do the UNIX double-fork magic, see Stevens' "Advanced 
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    # http://code.activestate.com/recipes/66012/
    # CHITS SMS code from Bowei Du
    try:
        pid = os.fork()
        if pid > 0:
            log.info("Daemon PID %d" % pid)
            sys.exit(0)
    except OSError, e:
        log.error("fork #1 failed: %d (%s)" % (e.errno, e.strerror))
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    # os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print eventual PID before
            log.info("Daemon PID %d" % pid)
            sys.exit(0)
    except OSError, e:
        log.error("fork #2 failed: %d (%s)" % (e.errno, e.strerror))
        sys.exit(1)
    
    pid = os.getpid()
    pidfile = os.path.basename(pidfile)
    pidfile = os.path.join(PATH, 'log', pidfile)
    if not os.path.exists(pidfile):
        raise ConfigError("%s not found" % pidfile)
    pf = file(pidfile,'r+')
    pf.write("%s\n" % pid)
    pf.close()
    
    return pid

#---------- Exception tools
class ConfigError(Exception):
    """Exception handling for configuration file."""
    # CHITS SMS code from Bowei Du
    configfile = ''

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return ConfigError.configfile + ': ' + self.msg

#---------- xml tools
class XmlWrapper:
    # CHITS SMS code from Bowei Du
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
        rc = ""
        for node in self.node.childNodes:
            if node.nodeType == node.TEXT_NODE:
                rc = rc + node.data
        return rc

if __name__ == '__main__':
    print 'This script is not meant to be run from command line'
    PATH = project_path(sys.argv[0])
    log = get_logger("mhtools")
else:
    PATH = project_path(__file__)
    log = get_logger("mhtools")