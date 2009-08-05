#!/usr/bin/python

import unittest
import xml.dom.minidom as minidom

import os.path
import ConfigParser
import cPickle
import email

from MHTools import project_path
from MHTools import XmlWrapper
from SmsHandler import SmsReader, SmsSender

class SmsReaderTest(unittest.TestCase):
    """SmsReader tests."""
    
    def setUp(self):
        self.reader = SmsReader(config_file)
        self.xml = XmlWrapper(minidom.parse(os.path.join(PATH, 'test', "sms1.test")))
        self.msg = email.message_from_file(open(os.path.join(PATH, 'test', "sms1.txt"), 'r'))
    
    def tearDown(self):
        pass
    
    def test_get_headers_spl(self):
        """get_headers_spl() should return dictionary containing headers defined in config file"""
        headers = self.reader.get_headers_orig(self.msg)
        header_asrt = self.reader.get_headers_spl(headers)
        
        header_file = self.xml.test.headers.get_text()
        header_file = '<'.join(header_file.split('&lt;'))
        header_file = '>'.join(header_file.split('&gt;'))
        header_file = cPickle.loads(str(header_file))
        self.assertEqual(header_asrt, header_file)
    
    def test_get_keyword(self):
        """get_keyword() should return string containing keyword of the transaction"""
        text_content = self.reader.get_text_content(self.msg.get_payload())
        self.assertEqual(self.reader.get_keyword(text_content), self.xml.test.keyword.get_text())
        
    def test_get_contact(self):
        """get_contact() should return string containing sender of sms"""
        headers = self.reader.get_headers_orig(self.msg)
        headers = self.reader.get_headers_spl(headers)
        self.assertEqual(self.reader.get_contact(headers), self.xml.test.contact.get_text())
    
    def test_get_date(self):
        """get_date() should return string containing when sms was sent"""
        headers = self.reader.get_headers_orig(self.msg)
        headers = self.reader.get_headers_spl(headers)
        self.assertEqual(self.reader.get_date(headers), self.xml.test.date.get_text())
    
    def test_get_text_content(self):
        """get_text_content() should return string containing body of sms"""
        tc_file = self.xml.test.text_content.get_text()
        tc_file = '<'.join(tc_file.split('&lt;'))
        tc_file = '>'.join(tc_file.split('&gt;'))
        self.assertEqual(self.reader.get_text_content(self.msg.get_payload()), str(tc_file))
    
    def test_get_attachments(self):
        """get_attachments() should return dictionary containing sms/mms attachments"""
        attach_file = self.xml.test.attachments.get_text()
        attach_file = cPickle.loads(str(attach_file))
        self.assertEqual(self.reader.get_attachments(self.msg.get_payload()), attach_file)

if __name__ == "__main__":
    PATH = project_path()
    config_file = os.path.join(PATH, 'config', "triage.conf")
    unittest.main()