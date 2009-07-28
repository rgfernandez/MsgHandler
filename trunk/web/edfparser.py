#!/usr/bin/python

import ConfigParser
import MySQLdb
import edf

def main():
    """Handle command line arguments."""
    opts, args = getopt.getopt(sys.argv[1:], 'hdtc:', ['help', 'debug', 'config-file=', 'test'])
    
    ecg_file = args[0]
    #debug_level = logging.INFO
    
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
    
    if not os.path.exists(config_file) or not os.path.exists(ecg_file):
        raise
    
    try:
        db_params = {'host': self.cfg.get('database', 'host'),
                    'port': self.cfg.get('database', 'port'),
                    'username': self.cfg.get('database', 'username'),
                    'passwd': self.cfg.get('database', 'passwd'),
                    'db': self.cfg.get('database', 'db')}
    except ConfigParser.NoSectionError, e:
        raise ConfigError(str(e))
    except ConfigParser.NoOptionError, e:
        raise ConfigError(str(e))
    
    cfg = ConfigParser.ConfigParser()
    cfg.read(config_file)
    
    x = edf.EDFSignal(ecg_file,'ecg.txt','II',15,50).extract_ECG()
    
    conn = MySQLdb.connect(**db_params)
    cur = conn.cursor()
    cur.execute("""INSERT INTO edfs (val) VALUES ('%s')""" % (','.join([str(elem) for elem in data])))
    conn.close()

if __name__ == '__main__':
    main()