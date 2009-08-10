import logging

from mhtools import add_module

log = logging.getLogger('msgutil')

class MsgReader:
    def __init__(self, config, mod_name='', test_mode=False):
        self.cfg = config
        self.mod_name = mod_name
        self.test_mode = test_mode
        
        add_module(mod_name)
        try:
            from main import Main
            self.msg_mod = Main(self.cfg, test_mode)
        except ImportError:
            raise Exception("module '%s' does not exist" % mod_name)
    
    def process(self, contact, headers, text_content, attachments):
        self.msg_mod.process(contact, headers, text_content, attachments)
    
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
