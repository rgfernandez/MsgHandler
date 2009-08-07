import logging
import ConfigParser

log = logging.getLogger('_template-main')

class Main:
    def __init__(self, cfg, test_mode=False):
        self.cfg = cfg
        self.test_mode = test_mode
    
    def process(self, contact, headers, text_content, attachments):
        # contact - string
        # headers - dictionary
        # text_content - string
        # attachments - dictionary
        
        if self.test_mode:
            # do processing for test here
            return
        
        # do processing for production here
    
    # add other methods here
