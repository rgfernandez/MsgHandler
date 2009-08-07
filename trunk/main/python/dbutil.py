import logging

import MySQLdb

log = logging.getLogger('dbutil')

#---------- db tools
class DbWrapper:
    """Wrapper for MySQL db"""
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
