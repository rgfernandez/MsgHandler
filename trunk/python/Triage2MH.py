#!/usr/bin/python

import getopt
import sys
import os
import time
import ConfigParser
import MySQLdb

from MHTools import stopd, startd
from MHTools import get_logger
from MHTools import ConfigError
from MHLink import WsLink

from EmailHandler import EmailSender
from SmsHandler import SmsSender

class MsgGenerator:
    def __init__(self, config_file):
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read(config_file)
        
        try:
            self.sleep = int(self.cfg.get('triage', 'sleep'))
        except ConfigParser.NoSectionError:
            raise ConfigError("'triage' section not in config file")
        except ConfigParser.NoOptionError:
            raise ConfigError("'sleep' option missing in 'triage' section")
    
    def run(self):
        """Check web services from time to time."""
        is_sent = False
        while True:
            msg = WsLink().msg_is_sent(is_sent)
            is_sent = self.send_msg(msg)
            time.sleep(self.sleep)
    
    def send_msg(self, msg):
        """Send message using sms or email depending on the mode."""
        try:
            if not cmp(msg[1]['Mode'], 'sms'):
                msgsender = SmsSender(self.cfg)
            elif not cmp(msg[1]['Mode'], 'email'):
                msgsender = EmailSender(self.cfg)
        except:
            msgsender = EmailSender(self.cfg)
        
        return msgsender.send_message(*msg)
    
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
    
    pidfile = 'triage2mh.pid'
    if not cmp(action, 'stop') or not cmp(action, 'restart'):
        for elem in stopd(pidfile):
            log.error(elem)
        if not cmp(action, 'restart'):
            action = 'start'
    if not cmp(action, 'start'):
        x = MsgGenerator(config_file)
        log.info("Daemon PID %d" % startd(pidfile))
        x.run()

if __name__ == '__main__':
    smsfile = '-'
    log = get_logger("triage2mh")
    try:
        main()
    except Exception, e:
        log.error('Exception processing "%s": %s' % (smsfile, e))
        raise
else:
    log = get_logger("triage2mh")