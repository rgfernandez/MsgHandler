#!/usr/bin/python

import getopt
import sys
import os
import time
import tempfile
import ConfigParser
import MySQLdb

from MHTools import stopd, startd
from MHTools import get_logger
from MHTools import ConfigError
from MHLink import DbLink, WsLink

class MsgProcess:
    def __init__(self, config_file):
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read(config_file)
        
        try:
            self.sleep = int(self.cfg.get('database', 'sleep'))
            cfg = dict(self.cfg.items('database'))
            self.db = DbLink(**cfg)
        except ConfigParser.NoSectionError:
            raise ConfigError("'database' section not in config file")
        except ConfigParser.NoOptionError:
            raise ConfigError("'sleep' option missing in 'database' section")
    
    def run(self):
        """Check database from time to time. Send contents to triage using web services."""
        cfg = dict(self.cfg.items('database'))
        while True:
            try:
                msg = self.db.get_earliest_msg()
            except MySQLdb.OperationalError:
                self.db = DbLink(**cfg)
                msg = self.db.get_earliest_msg()
            if msg:
                res = WsLink().push_msg(*msg)
                if not res:
                    try:
                        self.db.del_msg(uuid)
                    except MySQLdb.OperationalError:
                        self.db = DbLink(**cfg)
                        self.db.del_msg(uuid)
                else:
                    log.error(res)
            time.sleep(self.sleep)
    
    def close(self):
        """Close database connection."""
        self.db.close()

def main():
    """Handle command line arguments."""
    opts, args = getopt.getopt(sys.argv[1:], 'hdtc:', ['help', 'debug', 'config-file=', 'test'])
    
    action = args[0]
    #debug_level = logging.INFO
    config_file = '-'
    test_match = False
    
    for o, a in opts:
        if o in ('-h', '--help'):
            print 'hello'
            sys.exit(0)
        elif o in ('-d', '--debug'):
            pass#debug_level = logging.DEBUG
        elif o in ('-c', '--config-file'):
            config_file = a
        elif o in ('-t', '--test'):
            test_match = True
            return
    
    if not os.path.exists(config_file):
        raise ConfigError("%s not found" % config_file)
    
    pidfile = 'mh2triage.pid'
    if not cmp(action, 'stop') or not cmp(action, 'restart'):
        for elem in stopd(pidfile):
            log.error(elem)
        if not cmp(action, 'restart'):
            action = 'start'
    if not cmp(action, 'start'):
        x = MsgProcess(config_file)
        log.info("Daemon PID %d" % startd(pidfile))
        x.run()

if __name__ == '__main__':
    smsfile = '-'
    log = get_logger("mh2triage")
    try:
        main()
    except Exception, e:
        log.error('Exception processing "%s": %s' % (smsfile, e))
        raise
else:
    log = get_logger("mh2triage")