import logging

import sys
import os
from signal import SIGTERM
import errno
import time

from mhtools import project_path

log = logging.getLogger('daemon')

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

if __name__ == '__main__':
    print 'This script is not meant to be run from command line'
    PATH_ROOT = project_path(sys.argv[0])
else:
    PATH_ROOT = project_path(__file__)
    
    FORMAT = "%(asctime)-15s:%(levelname)-3s:%(name)-8s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)