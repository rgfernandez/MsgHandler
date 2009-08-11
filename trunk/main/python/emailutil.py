#!/usr/bin/python

import logging
import getopt
import sys
import os
import time
import tempfile
import ConfigParser

from daemon import stopd, startd
from mhtools import get_config, ConfigError
import msgutil

import re
import datetime

import smtplib
import email
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

log = logging.getLogger('emailutil')

class Reader:
    def __init__(self, config):
        self.cfg = config
        try:
            self.mode = self.cfg.get('email', 'mode')
            
            if not self.cfg.has_section('headers'):
                raise ConfigParser.NoSectionError
        except ConfigParser.NoSectionError, e:
            raise ConfigError(str(e))
        except ConfigParser.NoOptionError, e:
            raise ConfigError(str(e))
    
    def get_message(self, msgtext):
        """Get email from file and return as email object."""
        return email.message_from_string(msgtext)
    
    def run(self, emailtext='', test_mode=False):
        """If test mode, forward message. Else, call appropriate module."""
        msg = self.get_message(emailtext)
        outp = self._parse(msg)
        log.info(outp)
        (contact, headers, text_content, attachments) = outp
        
        x = msgutil.MsgReader(self.cfg, test_mode)
        x.process(*outp)
    
    def _parse(self, msg):
        """Parse email messages and return as tuple."""
        headers = self.get_headers(msg)
        contact = self.get_contact(headers)
        text_content = self.get_text_content(msg.get_payload())
        attachments = self.get_attachments(msg.get_payload())
        
        return (contact, headers, text_content, attachments)
    
    def get_headers(self, msg):
        """Add special headers to existing email headers."""
        headers = self.get_headers_orig(msg)
        headers = self.get_headers_spl(msg)
        #headers['module'], headers['keyword'] = self.get_keyword(headers)
        headers['caseid'] = self.get_caseid(headers)
        headers['subject'] = self.get_subject(headers)
        headers['references'] = self.get_references(headers)
        headers['date'] = self.get_date(headers)
        headers['mode'] = self.mode
        
        return headers
    
    def get_headers_orig(self, msg):
        """Get email headers and return as dictionary."""
        headers = [(elem.lower(), item) for (elem, item) in msg.items()]
        log.info(headers)
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
        """Return email address of sender."""
        if 'from' in headers:
            return email.utils.parseaddr(headers['from'])[1]
        return ''
    
    def get_caseid(self, headers):
        """Return case id."""
        if 'caseid' in headers:
            return headers['caseid']
        if 'subject' in headers:
            # search for caseid in subject header
            str_search = re.search('(?<=\[caseid-).*(?=\].*)', headers['subject'])
            if str_search is not None:
                return str_search.group()
        return ''
    
    def get_subject(self, headers):
        """Return subject with case id information removed."""
        if 'subject' in headers:
            subj = headers['subject']
            cid = re.search('(\[caseid-.*\])', subj)
            if cid:
                # remove caseid information from subject
                subj = ' '.join([elem.strip() for elem in subj.split(cid.group())])
            return ' '.join(filter(self.filt_subject, subj.split()))
        return ''
    
    def filt_subject(self, elem):
        """Remove Re and Fwd from subject."""
        if elem in ('Re:', 'Fwd:'):
            return ''
        else:
            return elem
    
    def get_references(self, headers):
        """Return references."""
        if 'references' in headers:
            refs = headers['references'].split()
            refs.append(headers['message-id'])
            return ' '.join(refs)
        else:
            return headers['message-id']
    
    def get_keyword(self, headers):
        """Return keyword."""
        if 'caseid' in headers:
            keyphrase = 'followup'
        else:
            keyphrase = headers['subject']
        
        for handler in self.cfg.get('handlers', 'enabled').split(','):
            keys = self.cfg.get(handler, 'keywords').split(',')
            for (item, elem) in self.cfg.items('keywords'):
                if item not in keys:
                    continue
                rex = re.compile(elem)
                if rex.match(keyphrase.strip().lower()):
                    return (self.cfg.get(handler, 'mod_name'), item)
        return ('', '')
    
    def get_date(self, headers, date_fmt="%m-%d-%Y %H:%M:%S"):
        """Return formatted date as string."""
        if 'date' in headers:
            val = email.utils.parsedate(headers['date'])
            # unpack tuple and get year, month, day, hr, min, sec
            #return datetime.datetime(*val[:6])
            val = datetime.datetime(*val[:6])
        else:
            val = datetime.datetime.now()
        
        return val.strftime(date_fmt)
    
    def get_text_content(self, content):
        """Return body of email as string."""
        try:
            return self.get_text_content(content[0].get_payload())
        except AttributeError:
            return content
    
    def get_attachments(self, content):
        """Return email attachments as dictionary."""
        if not isinstance(content, list):
            return dict()
        res = dict()
        for elem in content[1:]:
            fname = elem.get_filename()
            if fname:
                res[fname] = elem.get_payload(decode=True)
        return res
    
class Sender:
    def __init__(self, config):
        self.cfg = config
        try:
            self.email_user = self.cfg.get('email', 'user')
        except ConfigParser.NoSectionError, e:
            raise ConfigError(str(e))
        except ConfigParser.NoOptionError, e:
            raise ConfigError(str(e))
    
    def send_message(self, contact, headers, text_content, attachments):
        """Construct email message to send and return True."""
        # http://snippets.dzone.com/posts/show/757
        # http://python.active-venture.com/lib/node510.html
        if attachments:
            msg = MIMEMultipart()
            msg.attach(MIMEText(text_content))
        else:
            msg = MIMEText(text_content)
        
        msg.add_header('To', contact)
        for (elem, item) in headers.items():
            if elem.lower() not in ('subject', 'in-reply-to', 'references'):
                elem = 'X-Eccs-%s' % elem
            # capitalize words separated by dashes '-'
            elem = '-'.join([x.capitalize() for x in elem.split('-')])
            msg.add_header(elem, item)
        
        for (elem, item) in attachments.items():
            part = MIMEBase('application', "octet-stream")
            part.set_payload(item)
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % elem)
            msg.attach(part)
        
        self.send(contact, msg.as_string())
        return True
    
    def send(self, contact, msg):
        """Send email message using SMTP."""
        serv = smtplib.SMTP('localhost')
        serv.sendmail(self.email_user, contact, msg)
        serv.quit()

def main():
    """Handle command line arguments."""
    debug_level = logging.INFO
    config_file = '-'
    test_file = ''
    test_mode = False
    FORMAT = "%(asctime)-15s:%(levelname)-3s:%(name)-8s %(message)s"
    
    logging.basicConfig(level=debug_level, format = FORMAT)
    opts, args = getopt.getopt(sys.argv[1:], 'hdtc:', ['help', 'debug', 'config-file=', 'test'])
    
    for o, a in opts:
        if o in ('-h', '--help'):
            print 'hello'
            sys.exit(0)
        elif o in ('-d', '--debug'):
            debug_level = logging.DEBUG
        elif o in ('-c', '--config-file'):
            config_file = a.split(':')
        elif o in ('-t', '--test'):
            test_mode = True
        elif o in ('-f', '--file'):
            test_file = a
    
    cfg = get_config(*config_file)
    emailfile = args[0]
    if not os.path.exists(emailfile):
        raise Exception("Can't find emailfile %s" % emailfile)
    emailtext = open(emailfile, 'r').read()
    
    x = Reader(cfg)
    x.run(emailtext, test_mode)

if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        log.error('%s' % (e,))
else:
    pass