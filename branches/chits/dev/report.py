#!/usr/bin/python

import logging
import getopt
import sys
import os

import MySQLdb

from smsutil import SmsSender

log = logging.getLogger('report')

class report:
    def __init__(self, *args, **kwds):
        self.dbparams = dict()
        if 'sql_host' in kwds:
            self.dbparams['host'] = kwds['sql_host']
        if 'sql_port' in kwds:
            self.dbparams['port'] = int(kwds['sql_port'])
        
        self.dbparams['user'] = kwds['sql_user']
        self.dbparams['passwd'] = kwds['sql_pwd']
        self.dbparams['db'] = kwds['sql_db']
        
        log.debug('Using %s' % (str(self.dbparams)))
        #self.dbparams = {'host' : host, 'port' : port, 'user' : user, 'passwd' : passwd, 'db' : db}
        self.connect()
    
    def connect(self):
        """Connect to database."""
        self.conn = MySQLdb.connect(**self.dbparams)
    
#    def get(self, table, cols, conds):
#        """Helper for query."""
#        if not(isinstance(cols, list) and cols):
#            cols = ['*']
#        if conds:
#            conds_spec = []
#            vals = []
#            for (elem, item) in conds.items():
#                conds_spec.append('%s=%%s' % elem)
#                vals.append(item)
#            return "SELECT %s FROM %s WHERE %s" % (','.join(cols), table, ' AND '.join(conds_spec)) , tuple(vals)
#        return "SELECT %s FROM %s" % (','.join(cols), table),
    
    def get(self, table, cols, conds, misc=''):
        """Helper for query."""
        if not(isinstance(cols, list) and cols):
            cols = ['*']
        if conds:
            conds_spec = []
            vals = []
            for (elem, item) in conds.items():
                if not item:
                    conds_spec.append(elem)
                else:
                    conds_spec.append('%s=%%s' % elem)
                    vals.append(item)
            return "SELECT %s FROM %s WHERE %s %s" % (','.join(cols), table, ' AND '.join(conds_spec), misc) , tuple(vals)
        return "SELECT %s FROM %s %s" % (','.join(cols), table, misc),
    
    def get_pre_apt(self, health_center=''):
        """Return contact and body of message from uuid."""
        cur = self.conn.cursor()
        conds = {'timestampdiff(hour, appointment_time, now()) BETWEEN 0 AND 24': ''}
        if health_center:
            conds['health_center'] = health_center
        qry = self.get('patient_apts JOIN patient_regs ON patient_regs.id=patient_reg_id', ['health_center', 'count(health_center)'], conds, 'GROUP BY health_center')
        print qry
        cur.execute(*qry)
        x = cur.fetchall()
        return tuple([elem for elem in filter(None, map((lambda x: x if x[0] else ''), x))])
    
    def get_post_apt(self, health_center=''):
        """Return contact and body of message from uuid."""
        cur = self.conn.cursor()
        conds = {'timestampdiff(hour, appointment_time, now()) BETWEEN 0 AND 24': '',
                 '(patient_reg_id NOT IN (SELECT patient_reg_id FROM patient_apts WHERE timestampdiff(hour, appointment_time, now()) < 0))': ''}
        if health_center:
            conds['health_center'] = health_center
        qry = self.get('patient_apts JOIN patient_regs ON patient_regs.id=patient_reg_id', ['health_center', 'count(health_center)'], conds, 'GROUP BY health_center')
        print qry
        cur.execute(*qry)
        x = cur.fetchall()
        return tuple([elem for elem in filter(None, map((lambda x: x if x[0] else ''), x))])
    
    def db_get_defaults(self, health_center=''):
        cur = self.conn.cursor()
        conds = {'timestampdiff(hour, appointment_time, now()) BETWEEN 0 AND 24': '',
                 '(patient_reg_id NOT IN (SELECT patient_reg_id FROM patient_apts WHERE timestampdiff(hour, appointment_time, now()) < 0))': ''}
        if health_center:
            conds['health_center'] = health_center
        qry = self.get('patient_apts JOIN patient_regs ON patient_regs.id=patient_reg_id', ['patient_reg_id', ], conds)
        cur.execute(*qry)
        x = cur.fetchall()
        return tuple(['T%04d' % elem[0] for elem in x])
    
    def get_post_reg(self, health_center=''):
        """Return contact and body of message from uuid."""
        cur = self.conn.cursor()
        conds = {'timestampdiff(hour, create_time, now()) BETWEEN 0 AND 24': ''}
        if health_center:
            conds['health_center'] = health_center
        qry = self.get('patient_regs', ['health_center', 'count(health_center)'], conds, 'GROUP BY health_center')
        print qry
        cur.execute(*qry)
        x = cur.fetchall()
        return tuple([elem for elem in filter(None, map((lambda x: x if x[0] else ''), x))])
    
    def report(self, mode='post', health_center=''):
        if mode == 'post':
            x = self.get_post_reg(health_center)
            x = ["> %s = %s" % (a,b) for (a,b) in x] if x else ['> None']
            
            y = self.get_post_apt(health_center)
            y = ["> %s = %s" % (a,b) for (a,b) in y] if y else ['> None']
            
            z = self.db_get_defaults(health_center)
            if z:
                z = "\nDefaulting patients(ids):\n> %s" % ', '.join(z)
            else:
                z = ''
            
            return "== NThC report for %s ==\nRegistered patients today:\n%s\nDefaulting patients:\n%s%s" % (health_center if health_center else 'ALL health centers', '\n'.join(x), '\n'.join(y), z)
        elif mode == 'pre':
            x = self.get_pre_apt(health_center)
            x = ["> %s = %s" % (a,b) for (a,b) in x] if x else ['> None']
            
            return "== NThC report for %s ==\nPatients scheduled for today:\n%s" % (health_center if health_center else 'ALL health centers', '\n'.join(x), )
        else:
            return ''
    
def help():
    return """
        use /home/randy/public_html/conn/chits.php as the config file
    """

def main():
    debug_level = logging.INFO
    config_file = '-'   # /home/randy/public_html/conn/chits.php
    test_mode = False
    mode = ''
    FORMAT = "%(asctime)-15s:%(levelname)-3s:%(name)-8s %(message)s"
    
    logging.basicConfig(level=debug_level, format = FORMAT)
    opts, args = getopt.getopt(sys.argv[1:], 'hdtc:m:', ['help', 'debug', 'config-file=', 'test', 'mode='])
    
    for o, a in opts:
        if o in ('-h', '--help'):
            print help()
            sys.exit(0)
        elif o in ('-d', '--debug'):
            debug_level = logging.DEBUG
        elif o in ('-c', '--config-file'):
            config_file = a
        elif o in ('-m', '--mode'):
            mode = a
        elif o in ('-t', '--test'):
            test_mode = True
    
    try:
        contact = args[0]
    except:
        contact = ''
    
    try:
        hc_itm = args[1]
    except:
        hc_itm = ''
    
    y = open(config_file, 'r').read()
    cfg = dict()
    vars = y.split('\r\n')
    for elem in vars:
        if '=' in elem:
            n,o = elem.split('=')
            cfg[n[1:].strip()] = o.strip(' ";')
    
    db = report(**cfg)
    x = db.report(mode, hc_itm)
    print x
    if x and contact:
        SmsSender('/var/spool/sms/outgoing').send_message(contact, {}, x, {})

if __name__ == '__main__':
    main()