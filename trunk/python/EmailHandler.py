#!/usr/bin/python

import getopt
import sys
import os
import time
import tempfile
import ConfigParser

from MHTools import stopd, startd
from MHTools import get_logger
from MHTools import ConfigError
from MHLink import DbLink

import re
import datetime
import imaplib
import smtplib

import email
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

class EmailReader:
    def __init__(self, config_file):
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read(config_file)
        
        try:
            self.email_params = {'server': self.cfg.get('email', 'imapserver'),
                                'user': self.cfg.get('email', 'user'),
                                'passwd': self.cfg.get('email', 'passwd')}
            self.sleep = int(self.cfg.get('email', 'sleep'))
            self.mode = self.cfg.get('email', 'mode')
            
            if not self.cfg.has_section('headers'):
                raise ConfigParser.NoSectionError
        except ConfigParser.NoSectionError, e:
            raise ConfigError(str(e))
        except ConfigParser.NoOptionError, e:
            raise ConfigError(str(e))
    
    def login(self):
        """Login to email address via secure IMAP4."""
        self.serv = imaplib.IMAP4_SSL(self.email_params['server'])
        try:
            self.serv.login(self.email_params['user'], self.email_params['passwd'])
            self.serv.select()
        except imaplib.error:
            self.logout()
            raise
    
    def logout(self):
        """Logout email."""
        try:
            self.serv.close()
        except imaplib.error:
            pass
        self.serv.logout()
    
    def get_unread(self):
        """Return number of unread messages."""
        self.serv.recent()
        resp = self.serv.search(None, "UNSEEN")
        if resp[0]!='OK':
            return []
        resp = resp[1][0].split()
        if resp:
            log.info("%d message(s) unread" % len(resp))
        return resp
    
    def get_message(self, msgnum):
        """Get email, set as seen, and return as email object."""
        msg = self.serv.fetch(msgnum, "RFC822")
        if msg[0]!='OK':
            return ''
        self.serv.store(msgnum, '+FLAGS', '\\Seen')
        return email.message_from_string(msg[1][0][1])
    
    def test_mode(self):
        """Send all received email back to sender. Use 'reply' as email body."""
        log.debug('Using %s' % (str(self.email_params)))
        try:
            test1 = self.cfg.get('email', 'test1')
            test2 = self.cfg.get('email', 'test2')
        except ConfigParser.NoOptionError, e:
            raise ConfigError(str(e))
        
        self.login()
        while True:
            for i in self.get_unread():
                msg = self.get_message(i)
                if not msg:
                    continue
                outp = self._parse(msg)
                
                (contact, headers, text_content, attachments) = outp
                if not headers['caseid']:
                    headers['caseid'] = '100'
                    headers['uploadurl'] = 'http://parakeeto.ath.cx:60080/web/upload_file.php'
                contact = test1 if (contact==test2) else test2
                self.respond_to_msg(contact, headers, text_content, attachments)
            time.sleep(self.sleep)
        self.logout()
    
    def run(self):
        """Check email from time to time. Insert into database and send an autoreply."""
        log.debug('Using %s' % (str(self.email_params)))
        
        self.login()
        while True:
            for i in self.get_unread():
                msg = self.get_message(i)
                outp = self._parse(msg)
                self.insert_msg_to_db(outp)
                self.respond_to_msg(*outp)
            time.sleep(self.sleep)
        self.logout()
    
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
        headers['keyword'] = self.get_keyword(headers)
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
            return 'followup'
        else:
            return 'refer'
    
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
    
    def respond_to_msg(self, contact, headers, text_content, attachments):
        """Send email response using EmailSender class."""
        email_send = EmailSender(self.cfg)
        headers['subject'] = '[caseid-%s] Re: %s' % (headers['caseid'], headers['subject'])
        if email_send.send_message(contact, headers, text_content, attachments):
            log.info('sent to %s' % contact)
    
    def insert_msg_to_db(self, outp):
        """Insert received email into database."""
        cfg = dict(self.cfg.items('database'))
        db = DbLink(**cfg)
        uuid = db.insert_msg(*outp)
        db.close()

class EmailSender:
    def __init__(self, config):
        self.cfg = config
        
        try:
            self.email_params = {'server': self.cfg.get('email', 'smtpserver'),
                                'user': self.cfg.get('email', 'user'),
                                'passwd': self.cfg.get('email', 'passwd')}
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
        serv = smtplib.SMTP(self.email_params['server'])
        serv.ehlo()
        serv.starttls()
        serv.ehlo()
        serv.login(self.email_params['user'], self.email_params['passwd'])
        
        serv.sendmail('', contact, msg)
        serv.quit()

def main():
    """Handle command line arguments."""
    opts, args = getopt.getopt(sys.argv[1:], 'hdtc:', ['help', 'debug', 'config-file=', 'test'])
    
    action = args[0]
    #debug_level = logging.INFO
    config_file = '-'
    test_mode = False
    
    for o, a in opts:
        if o in ('-h', '--help'):
            print 'hello'
            sys.exit(0)
        elif o in ('-d', '--debug'):
            pass#debug_level = logging.DEBUG
        elif o in ('-c', '--config-file'):
            config_file = a
        elif o in ('-t', '--test'):
            test_mode = True
    
    if not os.path.exists(config_file):
        raise ConfigError("%s not found" % config_file)
    
    pidfile = 'email.pid'
    if not cmp(action, 'stop') or not cmp(action, 'restart'):
        for elem in stopd(pidfile):
            log.error(elem)
        if not cmp(action, 'restart'):
            action = 'start'
    if not cmp(action, 'start'):
        x = EmailReader(config_file)
        log.info("Daemon PID %d" % startd(pidfile))
        if test_mode:
            x.test_mode()
        else:
            x.run()

if __name__ == '__main__':
    smsfile = '-'
    log = get_logger("emailhandler")
    try:
        main()
    except Exception, e:
        log.error('Exception processing "%s": %s' % (smsfile, e))
        raise
else:
    log = get_logger("emailhandler")