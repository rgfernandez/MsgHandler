import logging
import ConfigParser

log = logging.getLogger('chits-main')

class Main:
    def __init__(self, cfg, test_mode=False):
        self.cfg = cfg
        self.test_mode = test_mode
    
    def process(self, contact, headers, text_content, attachments):
        if self.test_mode:
            contact = self.get_reply_addr(headers, contact)
            if contact:
                self.respond_to_msg(contact, headers, text_content, attachments)
            return
        
        log.debug('\n%s\n%s\n%s\n%s', (contact, headers, text_content, attachments))
    
    def get_reply_addr(self, headers, contact=''):
        try:
            send_mode = headers['mode']
        except:
            raise Exception('mode not specified')
        
        if (send_mode == 'sms'):
            return self.cfg.get('sms', 'test')
        elif (send_mode == 'email'):
            try:
                test1 = self.cfg.get('email', 'test1')
                test2 = self.cfg.get('email', 'test2')
                upload_url = self.cfg.get('email', 'testurl')
            except ConfigParser.NoOptionError, e:
                raise ConfigError(str(e))
            
            if not headers['caseid']:
                headers['caseid'] = '100'
                headers['uploadurl'] = upload_url
            return test1 if (contact==test2) else test2
        else:
            raise Exception('mode %s not supported' % headers['mode'])
    
    def respond_to_msg(self, contact, headers, text_content, attachments):
        """Send msg response using XSender class."""
        if (headers['mode'] == 'sms'):
            from smsutil import SmsSender as Sender
        elif (headers['mode'] == 'email'):
            from emailutil import EmailSender as Sender
        else:
            raise Exception('mode %s not supported' % headers['mode'])
        
        sms_send = Sender(self.cfg)
        headers['subject'] = '[caseid-%s] Re: %s' % (headers['caseid'], headers['subject'])
        
        if sms_send.send_message(contact, headers, text_content, attachments):
            log.info('sent to %s' % contact)