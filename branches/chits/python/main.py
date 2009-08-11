import logging
import ConfigParser

from msgutil import MsgSender
import dbutil

from mhtools import get_config

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
        
        keyword = headers['keyword']
        if keyword == 'default':
            text_content = self.key_default(get_config('chits','main.conf'), contact)
        
        log.debug('\n%s\n%s\n%s\n%s' % (contact, headers, text_content, attachments))
        self.respond_to_msg(contact, headers, text_content, attachments)
    
    def key_default(self, cfg, contact):
        db_params = {'host': cfg.get('database', 'host'),
                     'port': cfg.get('database', 'port'),
                     'user': cfg.get('database', 'user'),
                     'passwd': cfg.get('database', 'passwd'),
                     'db': cfg.get('database', 'db')
                     }
        db = dbutil.DbWrapper(**db_params)
        hcntr = self.db_get_health_center(db, contact)
        dflts = self.db_get_defaults(db, hcntr)
        text_content = "== NThC reporting system ==\nDefaulting patients for %s (by id):\n%s" % (hcntr, ', '.join(dflts))
        
        return text_content
    
    def db_get_health_center(self, db, contact):
        cur = db.conn.cursor()
        qry = db.get('hw_regs', ['health_center', ], {'cell_no': contact})
        cur.execute(*qry)
        x = cur.fetchall()
        if x:
            return x[0][0]
        else:
            raise Exception('%s not in health worker list' % contact)
    
    def db_get_defaults(self, db, health_center):
        cur = db.conn.cursor()
        conds = {'timestampdiff(day, appointment_time, now())': '0'}
        if health_center != 'admin':
            conds['health_center'] = health_center
        qry = db.get('patient_apts JOIN patient_regs ON patient_regs.id=patient_reg_id', ['patient_reg_id', ], conds)
        cur.execute(*qry)
        x = cur.fetchall()
        return tuple(['%s' % elem[0] for elem in x])
    
        #SELECT patient_reg_id FROM patient_apts JOIN patient_regs ON patient_regs.id=patient_reg_id WHERE (patient_reg_id NOT IN (SELECT patient_reg_id FROM patient_apts WHERE timestampdiff(day, appointment_time, now()) < 0)) AND timestampdiff(day, appointment_time, now())=0 AND health_center='SAN PABLO'
    
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
            headers['subject'] = '[caseid-%s] Re: %s' % (headers['caseid'], headers['subject'])
            
            return test1 if (contact==test2) else test2
        else:
            raise Exception('mode %s not supported' % headers['mode'])
    
    def respond_to_msg(self, contact, headers, text_content, attachments):
        """Send msg response using XSender class."""
        x = MsgSender(self.cfg, headers['mode'])
        x.process(contact, headers, text_content, attachments)
