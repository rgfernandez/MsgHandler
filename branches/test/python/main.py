import logging
import ConfigParser

from msgutil import MsgSender

log = logging.getLogger('test-main')

class Main:
    def __init__(self, cfg, test_mode=False):
        self.cfg = cfg
        self.test_mode = test_mode
    
    def process(self, contact, headers, text_content, attachments):
        if self.test_mode:
            pass
        
        if headers['keyword'] == 'smstest':
            contact = headers['subject'].split()[1]
            headers['mode'] = 'sms'
        if headers['keyword'] == 'emailtest':
            contact = headers['subject'].split()[1]
            headers['mode'] = 'email'
        self.respond_to_msg(contact, headers, text_content, attachments)
        
        log.debug('\n%s\n%s\n%s\n%s' % (contact, headers, text_content, attachments))
    
    def respond_to_msg(self, contact, headers, text_content, attachments):
        """Send msg response using XSender class."""
        x = MsgSender(self.cfg, headers['mode'])
        x.process(contact, headers, text_content, attachments)
