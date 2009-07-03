#!/usr/bin/python

import getopt
import sys
import os
import time
import tempfile
import ConfigParser

import re
import datetime
import email

from MHTools import get_logger
from MHTools import ConfigError
from MHLink import DbLink

class SmsReader:
    def __init__(self, config_file):
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read(config_file)
        
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
    
    def get_message(self, smsfile):
        """Get sms from file and return as email object."""
        return email.message_from_string(open(smsfile, 'r').read())
    
    def test_mode(self, smsfile=''):
        """Send all received sms back to sender. Use 'reply' as sms body."""
        msg = self.get_message(i)
        outp = self._parse(msg)
        self.respond_test(*outp)
    
    def run(self, smsfile=''):
        """Insert received sms into database and send an autoreply."""
        msg = self.get_message(smsfile)
        outp = self._parse(msg)
        self.insert_msg_to_db(outp)
        self.respond_to_msg(*outp)
    
    def _parse(self, msg):
        """Parse sms messages and return as tuple."""
        headers = self.get_headers(msg)
        contact = self.get_contact(headers)
        text_content = self.get_text_content(msg.get_payload())
        attachments = self.get_attachments(msg.get_payload())
        headers['keyword'] = self.get_keyword(text_content)
        
        return (contact, headers, text_content, attachments)
    
    def get_headers(self, msg):
        """Add special headers to existing sms headers."""
        headers = self.get_headers_orig(msg)
        headers = self.get_headers_spl(msg)
        #headers['keyword'] = self.get_keyword(headers)
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
    
    def get_keyword(self, text_content):
        """Return keyword."""
        keys = self.cfg.get('buddyworks', 'keywords')
        keys = keys.split(',')
        vals = self.cfg.items('keywords')
        for (item, elem) in vals:
            if item not in keys:
                continue
            rex = re.compile(elem)
            if rex.match(text_content.lower()):
                return item
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
    
    def respond_to_msg(self, contact, headers, text_content, attachments):
        """Send sms response using SmsSender class."""
        if not self.cfg.has_section('database'):
            raise ConfigError('database not in sections')
        text_content = self.get_db_response(self.cfg.items('database'), headers['keyword'], 'eng')
        
        sms_send = SmsSender(self.cfg)
        sms_send.send_message(contact, headers, text_content, attachments)
    
    def get_db_response(self, config, kw, lang):
        """Get automated response using keyword."""
        db = DbLink(**cfg)
        resp = db.get_response(kw, lang)
        db.close()
        return resp
    
    def insert_msg_to_db(self, outp):
        """Insert received sms into database."""
        if not self.cfg.has_section('database'):
            raise ConfigError('database not in sections')
        cfg = dict(self.cfg.items('database'))
        db = DbLink(**cfg)
        uuid = db.insert_msg(*outp)
        db.close()

class SmsSender:
    # BuddyWorks code from Eric Pareja and Bowei Du
    def __init__(self, config):
        spool = '-'
        
        try:
            if isinstance(spool, str):
                spool = config
            else:
                spool = config.get('sms', 'outgoing')
            if not os.path.exists(spool):
                log.warning('%s smsd outgoing directory does not exist!' % spool)
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
    return 'hello'

def main():
    """Handle command line arguments."""
    # CHITS SMS code from Bowei Du
    opts, args = getopt.getopt(sys.argv[1:], 'hdtc:', ['help', 'debug', 'config-file=', 'test'])
    
    #debug_level = logging.INFO
    config_file = '-'
    test_match = False
    
    for o, a in opts:
        if o in ('-h', '--help'):
            print help()
            sys.exit(0)
        elif o in ('-d', '--debug'):
            #debug_level = logging.DEBUG
            pass
        elif o in ('-c', '--config-file'):
            config_file = a
        elif o in ('-t', '--test'):
            test_match = True
    
    if not os.path.exists(config_file):
        raise ConfigError("%s not found" % config_file)
    
    smsfile = args[0]
    if not os.path.exists(smsfile):
        raise Exception("Can't find smsfile %s" % smsfile)
    
    x = SmsReader(config_file, smsfile)
    x.run()

if __name__ == '__main__':
    smsfile = '-'
    log = get_logger("smshandler")
    try:
        main()
    except Exception, e:
        log.error('Exception processing "%s": %s' % (smsfile, e))
        raise
else:
    log = get_logger("smshandler")