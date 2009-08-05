#!/usr/bin/python

import getopt
import sys
import os
import time
import tempfile
import ConfigParser

import re
import datetime
import email

from mhtools import get_logger, project_path
from mhtools import ConfigError
from mhtools import parse_string

import logging
"""Logging in mhtest is shown in stdout, as opposed to those in other modules.

"""

class UnitTest:
    def __init__(self, xmlfile=None, xmlstr=None, debug=False):
        if xmlfile is None and xmlstr is None:
            raise Exception, "Need to specify either a file or a string!"
        if xmlfile:
            xmlstr = open(xmlfile, "r").read()
        self.xml = parse_string(xmlstr)
        self.debug = debug
    
    def _load_conf(self):
        conf = ''
        includes = self.xml.test.conf.get_by_tag("include")
        for inc in includes:
            f = open(inc.get_text().strip(), "r")
            conf = conf + "\n" + f.read()
        conf = conf + "\n" + self.xml.test.conf.get_text().strip()
        return conf

    def _load_db(self):
        self.dbparams = {'host' : self.xml.test.db.host,
                         'user' : self.xml.test.db.user,
                         'passwd' : self.xml.test.db.passwd,
                         'port' : int(self.xml.test.db.port),
                         'db'   : self.xml.test.db.db}
        log.debug('DB = \n%s' % str(self.dbparams))
        
        try:
            conn = MySQLdb.connect(**self.dbparams)
        except Exception, e:
            print "Can't connect to DB. Make sure you have created a "
            print "database for running unit tests." 
            print "Error was: %s" % e
            sys.exit(1)
    
    def run(self):
        for elem in self.xml.test.conf.get_by_tag("file"):
            elem.get_text()
            x = open(elem.get_text(), 'r')
            print x.read()
        sys.exit(0)
        self.tempdir = tempfile.mkdtemp(prefix = "mhtest-")
        self.indir = os.path.join(self.tempdir, 'in')
        self.outdir = os.path.join(self.tempdir, 'out')

        self.in_count = 0
        self.out_count = 0
        
        try:
            os.mkdir(self.indir)
            os.mkdir(self.outdir)
            conf = self._load_conf()
            self._load_db()
            conf = conf + '\n[database]'
            for k in self.dbparams:
                conf = conf + '\n%s: %s' % (k, self.dbparams[k])
            conf = conf + '\n[smsd]'
            conf = conf + '\noutgoing: %s' % self.outdir
            log.debug('CONF = \n%s' % conf)

            self.conffile = os.path.join(self.tempdir, 'smsapp.conf')
            
            f = open(self.conffile, 'w')
            f.write(conf)
            f.write('\n')
            f.close()
            log.debug('wrote conf %s', self.conffile)

            for action in self.xml.test.run:
                f = getattr(self, 'action_%s' % action)
                f(action)
        finally:
            # os.system("rm -rf %s" % self.tempdir)
            pass

    # actions
    def action_sms_in(self, xml):
        log.debug('wrote sms %s', xml.id)
        smstext = "From: %s\nSubject: %s\n\n%s\n" % \
                  (xml.sender, xml.subject, xml.get_text().strip())
        f = open(os.path.join(self.indir, xml.id), 'w')
        f.write(smstext)
        f.close()

    def action_system(self, xml):
        cmd = xml.get_text().strip()
        log.debug('run "%s"' % cmd)
        system(cmd)

    def action_run_smsreminder(self, xml):
        if self.debug:
            cmd = "python python/smsreminder.py -u -c %s -d %s" % \
                (self.conffile, os.path.join(self.indir, xml.sms_id))
        else:
            cmd = "python python/smsreminder.py -u -c %s %s 2>/dev/null" % \
                (self.conffile, os.path.join(self.indir, xml.sms_id))            
        log.debug('run "%s"' % cmd)
        os.system(cmd)

    def action_run_daemon(self, xml):
        if self.debug:
            cmd = "python python/daemon.py -u -c %s -d" % (self.conffile)
        else:
            cmd = "python python/daemon.py -u -c %s" % (self.conffile)
        log.debug('run "%s"' % cmd)
        os.system(cmd)

    def action_assert_sms_out(self, xml):
        try:
            f = open(os.path.join(self.outdir, xml.id), 'r')
            res = f.read().strip()
            exp = xml.get_text().strip()
            if res != exp:
                print "UNIT TEST FAILED: expected\n\n%s\n\nbut got:\n\n%s\n" % \
                      (prefix_lines(exp, '| '), prefix_lines(res, '| '))
                sys.exit(1)
        except IOError:
                print "UNIT TEST FAILED: expected sms output file %s, but it doesn't exist" % \
                    xml.id
                sys.exit(1)
        log.debug("assert_sms_out OK")

    def action_init_db(self, xml):
        self._run_sql_file('sql/reset.sql')
        self._run_sql_file('sql/schema.sql')
        self._run_sql_file('sql/data.sql')
        self._run_sql_file('sql/tr.sql')
        self._run_sql_file('sql/tr_texts.sql')

    def action_sql_file(self, xml):
        self._run_sql_file(xml.get_text().strip())

    def action_run_sql(self, xml):
        conn = MySQLdb.connect(**self.dbparams)
        cursor = conn.cursor()
        cursor.execute(xml.get_text().strip())
        conn.commit()

    def action_assert_db(self, xml):
        conn = MySQLdb.connect(**self.dbparams)
        cursor = conn.cursor()
        cursor.execute(xml.query)
        rows = cursor.fetchall()
        expected = xml.get_text().split('\n')
        expected = [i for i in expected if i != '']
        if len(rows) != len(expected):
            print "UNIT TEST FAILED: SQL query='%s' expected %d SQL rows got %d rows" % \
                (xml.query, len(rows), len(expected))
            print "Expected: %s" % str(expected)
            print "Got: %s" % str(rows)
            sys.exit(1)
        for i in xrange(len(rows)):
            e = expected[i].strip()
            r = string.join(map(str, rows[i]), ' ').strip() 
            if e != r:
                print "UNIT TEST FAILED: SQL query='%s' expected '%s' got '%s'" % \
                    (xml.query, e, r)
                sys.exit(1)
        log.debug('assert_db OK "%s"' % xml.query)
        
    def _run_sql_file(self, fn):
        log.debug('running SQL file %s' % fn)
        passwd = ''
        if self.dbparams['passwd'] != '':
            passwd = '-p%s' % self.dbparams['passwd']
        os.system('mysql -u %s %s %s < %s' % 
                  (self.dbparams['user'], passwd, self.dbparams['db'], fn))
        
#------------------------------------------------------------------------------
def prefix_lines(lines, prefix):
    """Add a prefix to lines, which makes the printed output look good."""
    if lines[-1] == '\n':
        end = '\n'
        lines = lines[:-1]
    else:
        end = ''
    return prefix + lines.replace('\n', '\n' + prefix) + end

def print_usage():
    print """mhtest [-d] [-h] <test xml>

SUMMARY

    Runs the unit test described by <test xml>.

OPTIONS

    -d | --debug Print extra debugging information
    -h | --help  Print this help message
"""

def main():
    """Handle command line arguments."""
    # CHITS SMS code from Bowei Du
    opts, args = getopt.getopt(sys.argv[1:], 'hd', ['help', 'debug'])
    debug_level = logging.INFO
    
    for o, a in opts:
        if o in ('-h', '--help'):
            print_usage()
            sys.exit(0)
        elif o in ('-d', '--debug'):
            debug_level = logging.DEBUG
    logging.basicConfig(level=debug_level)
    
    if len(args) < 1:
        print_usage()
        print "ERROR: Need to specify test file!"
        sys.exit(1)

    u = UnitTest(xmlfile=args[0], debug=(debug_level==logging.DEBUG))
    u.run()

if __name__ == '__main__':
    main()