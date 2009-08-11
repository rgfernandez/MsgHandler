import logging
import re

from mhtools import add_module

log = logging.getLogger('msgutil')

class MsgReader:
    def __init__(self, config, test_mode=False):
        self.cfg = config
        self.test_mode = test_mode
    
    def process(self, contact, headers, text_content, attachments):
        headers = self.get_module(headers)
        
        log.debug(headers)
        
        msg_mod = self.import_module(headers['module'])
        msg_mod.process(contact, headers, text_content, attachments)
    
    def get_module(self, headers):
        """Add special headers to existing headers."""
        if 'subject' not in headers:
            headers['module'], headers['keyword'] = '', ''
        else:
            headers['module'], headers['keyword'] = self.get_keyword(headers['subject'])
        
        return headers
    
    def get_keyword(self, subject):
        """Return module and keyword."""
        for handler in self.cfg.get('handlers', 'enabled').split(','):
            keys = self.cfg.get(handler, 'keywords').split(',')
            for (item, elem) in self.cfg.items('keywords'):
                if item not in keys:
                    continue
                rex = re.compile(elem)
                if rex.match(subject.strip().lower()):
                    return (self.cfg.get(handler, 'mod_name'), item)
        return ('', '')
    
    def import_module(self, mod_name):
        """Import module and check for errors."""
        if not mod_name:
            raise Exception("no module match for keyword")
        
        add_module(mod_name)
        try:
            from main import Main
            return Main(self.cfg, self.test_mode)
        except ImportError:
            raise Exception("module '%s' does not exist" % mod_name)
    
class MsgSender:
    def __init__(self, config, mode=''):
        self.cfg = config
        self.mode = mode
        
        if not self.mode:
            raise Exception('no mode given')
        elif (self.mode == 'sms'):
            from smsutil import SmsSender as Sender
        elif (self.mode == 'email'):
            from emailutil import EmailSender as Sender
        else:
            raise Exception('mode %s not supported' % headers['mode'])
        
        self.msg_send = Sender(self.cfg)
    
    def process(self, contact, headers, text_content, attachments):
        if not contact:
            raise Exception('no recipient given')
        if self.msg_send.send_message(contact, headers, text_content, attachments):
            log.info('sent to %s' % contact)
