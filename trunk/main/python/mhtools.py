import logging

import sys
import os
from signal import SIGTERM
import errno
import time

import xml.dom.minidom as minidom
import MySQLdb

log = logging.getLogger('mhtools')

#---------- os.path tools
def project_path(cur_path=''):
    """Return path to trunk."""
    if not cur_path:
        cur_path = __file__
    real_path = os.path.realpath(cur_path)
    # path of code directory
    code_path = os.path.split(real_path)[0]
    # path of main application directory
    main_path = os.path.split(code_path)[0]
    # path of root directory
    return os.path.split(main_path)[0]

#---------- daemon tools
def stopd(module='', pidfile=''):
    """Kill processes written on pid files."""
    # disclaimer: taken from the internet (will search for the link)
    pidfile = os.path.basename(pidfile)
    if module == 'main':
        pidfile = os.path.join(PATH_ROOT, 'main', 'log', pidfile)
    else:
        pidfile = os.path.join(PATH_ROOT, 'modules', module, 'log', pidfile)
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
    log.info('modified %s' % pidfile)
    return errors

def startd(module='', pidfile=''):
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
    if module == 'main':
        pidfile = os.path.join(PATH_ROOT, 'main', 'log', pidfile)
    else:
        pidfile = os.path.join(PATH_ROOT, 'modules', module, 'log', pidfile)
    if not os.path.exists(pidfile):
        raise ConfigError("%s not found" % pidfile)
    pf = file(pidfile,'r+')
    pf.write("%s\n" % pid)
    pf.close()
    
    log.info('modified %s' % pidfile)
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
def parse_string(s):
    """Parse string s and return it as an XmlWrapper."""
    return XmlWrapper(minidom.parseString(s))

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

#---------- db tools
class DbWrapper:
    """Wrapper for MySQL db"""
    def __init__(self, *args, **kwds):
        self.dbparams = dict()
        if 'sql_host' in kwds:
            self.dbparams['host'] = kwds['sql_host']
        if 'sql_port' in kwds:
            self.dbparams['port'] = int(kwds['sql_port'])
        
        self.dbparams['user'] = kwds['sql_user']
        self.dbparams['passwd'] = kwds['sql_pwd']
        self.dbparams['db'] = kwds['sql_db']
        
        log.debug('Using %s' % (str(self.dbparams)))
        #self.dbparams = {'host' : host, 'port' : port, 'user' : user, 'passwd' : passwd, 'db' : db}
        self.connect()
    
    def connect(self):
        """Connect to database."""
        self.conn = MySQLdb.connect(**self.dbparams)
    
    def get(self, table, cols, conds, misc=''):
        """Helper for query."""
        if not(isinstance(cols, list) and cols):
            cols = ['*']
        if conds:
            conds_spec = []
            vals = []
            for (elem, item) in conds.items():
                if not item:
                    conds_spec.append(elem)
                else:
                    conds_spec.append('%s=%%s' % elem)
                    vals.append(item)
            return "SELECT %s FROM %s WHERE %s %s" % (','.join(cols), table, ' AND '.join(conds_spec), misc) , tuple(vals)
        return "SELECT %s FROM %s %s" % (','.join(cols), table, misc),

if __name__ == '__main__':
    print 'This script is not meant to be run from command line'
    PATH_ROOT = project_path(sys.argv[0])
else:
    PATH_ROOT = project_path(__file__)
    
    FORMAT = "%(asctime)-15s:%(levelname)-3s:%(name)-8s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)