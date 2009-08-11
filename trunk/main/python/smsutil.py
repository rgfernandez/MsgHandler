#!/usr/bin/python

import logging
import getopt
import sys
import os
import time
import tempfile
import ConfigParser

import re
import datetime
import email

from mhtools import get_config, ConfigError
import msgutil

log = logging.getLogger('smsutil')

class Reader:
    def __init__(self, config):
        self.cfg = config
        try:
            self.mode = self.cfg.get('sms', 'mode')
            if not self.cfg.has_section('headers') or not self.cfg.has_section('buddyworks') or \
                    not self.cfg.has_section('keywords'):
                raise ConfigParser.NoSectionError
            if not self.cfg.has_option('buddyworks', 'keywords'):
                raise ConfigParser.NoOptionError
        except ConfigParser.NoSectionError, e:
            raise ConfigError(str(e))
        except ConfigParser.NoOptionError, e:
            raise ConfigError(str(e))
    
    def get_message(self, msgtext):
        """Get sms from file and return as email object."""
        return email.message_from_string(msgtext)
    
    def run(self, smstext='', test_mode=False):
        """If test mode, forward message. Else, call appropriate module."""
        msg = self.get_message(smstext)
        outp = self._parse(msg)
        log.info(outp)
        (contact, headers, text_content, attachments) = outp
        
        x = msgutil.MsgReader(self.cfg, test_mode)
        x.process(*outp)
    
    def _parse(self, msg):
        """Parse sms messages and return as tuple."""
        headers = self.get_headers(msg)
        contact = self.get_contact(headers)
        text_content = self.get_text_content(msg.get_payload())
        attachments = self.get_attachments(msg.get_payload())
        
        headers['subject'] = text_content
        
        return (contact, headers, text_content, attachments)
    
    def get_headers(self, msg):
        """Add special headers to existing sms headers."""
        headers = self.get_headers_orig(msg)
        headers = self.get_headers_spl(msg)
        headers['date'] = self.get_date(headers)
        headers['mode'] = self.mode
        
        return headers
    
    def get_headers_orig(self, msg):
        """Get sms headers and return as dictionary."""
        headers = [(elem.lower(), item) for (elem, item) in msg.items()]
        #log.info(headers)
        return dict(headers)
    
    def get_headers_spl(self, headers):
        """Get headers used by the system and return as dictionary."""
        res = dict()
        vals = self.cfg.items('headers')
        for (item, elem) in vals:
            for obj in elem.split(','):
                obj = obj.lower().strip()
                if obj in headers:
                    res[item] = headers[obj]
                    break
        return res
    
    def get_contact(self, headers):
        """Return number of sender."""
        if 'from' in headers:
            return email.utils.parseaddr(headers['from'])[1]
        return ''
    
    def get_date(self, headers, date_fmt="%m-%d-%Y %H:%M:%S"):
        """Return formatted date as string."""
        if 'date' in headers:
            val = datetime.datetime.strptime(headers['date'], '%y-%m-%d %H:%M:%S')
        else:
            val = datetime.datetime.now()
        
        return val.strftime(date_fmt)
    
    def get_text_content(self, content):
        """Return body of sms as string."""
        try:
            return self.get_text_content(content[0].get_payload())
        except AttributeError:
            return content
    
    def get_attachments(self, content):
        """Return sms attachments as dictionary."""
        return dict()
    
class Sender:
    # BuddyWorks code from Eric Pareja and Bowei Du
    def __init__(self, config):
        spool = '-'
        
        try:
            if isinstance(config, str):
                spool = config
            else:
                spool = config.get('sms', 'outgoing')
            if not os.path.exists(spool):
                log.error('%s smsd outgoing directory does not exist!' % spool)
                spool = '-'
        except ConfigParser.NoSectionError, e:
            raise ConfigError(str(e))
        except ConfigParser.NoOptionError, e:
            raise ConfigError(str(e))
        
        self.spool = spool
    
    def send_message(self, contact, headers, text_content, attachments):
        """Construct email message to send and return True if successful."""
        msg = "To: %s\n\n%s\n" % (contact, text_content)
        
        if self.spool != '-':
            self.send(contact, msg)
            return True
        else:
            return False
    
    def send(self, contact, msg):
        """Send SMS msg to cell_no by writing in the spool directory."""
        #outfile = os.tempnam(self.spool,'send_')
        outfile = tempfile.mkstemp(prefix='send_', dir=self.spool)
        f = open(outfile[1], "w")
        f.write(msg)
        f.close()
        os.chmod(f.name,0666)
        log.debug('sent SMS to %s: %s, file = %s' % (contact, msg, outfile))

def help():
    """Return usage of module."""
    return 'config file format --> module:file. if no : is detected, assume exact path is given'

def main():
    """Handle command line arguments."""
    # CHITS SMS code from Bowei Du
    debug_level = logging.INFO
    config_file = '-'
    test_mode = False
    FORMAT = "%(asctime)-15s:%(levelname)-3s:%(name)-8s %(message)s"
    
    logging.basicConfig(level=debug_level, format = FORMAT)
    opts, args = getopt.getopt(sys.argv[1:], 'hdtc:', ['help', 'debug', 'config-file=', 'test'])
    
    for o, a in opts:
        if o in ('-h', '--help'):
            print help()
            sys.exit(0)
        elif o in ('-d', '--debug'):
            debug_level = logging.DEBUG
        elif o in ('-c', '--config-file'):
            config_file = a.split(':')
        elif o in ('-t', '--test'):
            test_mode = True
    
    cfg = get_config(*config_file)
    smsfile = args[0]
    if not os.path.exists(smsfile):
        raise Exception("Can't find smsfile %s" % smsfile)
    smstext = open(smsfile, 'r').read()
    
    x = Reader(cfg)
    x.run(smstext, test_mode)

if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        log.error('%s' % (e,))
else:
    pass