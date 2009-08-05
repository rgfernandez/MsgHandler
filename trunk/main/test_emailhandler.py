#!/usr/bin/python

import unittest
import xml.dom.minidom as minidom

import os.path
import ConfigParser
import cPickle
import email

from MHTools import project_path
from MHTools import XmlWrapper
from EmailHandler import EmailReader, EmailSender

class EmailReaderTest(unittest.TestCase):
    """EmailReader tests."""
    
    def setUp(self):
        self.reader = EmailReader(config_file)
        self.xml = XmlWrapper(minidom.parse(os.path.join(PATH, 'test', "email1.test")))
        self.msg = email.message_from_file(open(os.path.join(PATH, 'test', "email1.txt"), 'r'))
    
    def tearDown(self):
        pass
    
    def test_get_unread(self):
        """get_unread() should return an integer containing number of unread email messages"""
        #self.assertTrue(isinstance(self.reader.get_unread(), int))
        pass
    
    def test_get_headers(self):
        """get_headers should return dictionary containing email headers"""
        headers = self.reader.get_headers(self.msg)
        
        header_file = self.xml.test.headers.get_text()
        header_file = '<'.join(header_file.split('&lt;'))
        header_file = '>'.join(header_file.split('&gt;'))
        header_file = cPickle.loads(str(header_file))
        self.assertEqual(headers, header_file)
    
    def test_get_caseid(self):
        """get_caseid() should return string containing caseid of the transaction"""
        headers = self.reader.get_headers_orig(self.msg)
        headers = self.reader.get_headers_spl(headers)
        self.assertEqual(self.reader.get_caseid(headers), self.xml.test.caseid.get_text())
    
    def test_get_keyword(self):
        """get_keyword() should return string containing keyword of the transaction"""
        headers = self.reader.get_headers_orig(self.msg)
        headers = self.reader.get_headers_spl(headers)
        self.assertEqual(self.reader.get_keyword(headers), self.xml.test.keyword.get_text())
        
    def test_get_contact(self):
        """get_contact() should return string containing sender of email"""
        headers = self.reader.get_headers_orig(self.msg)
        headers = self.reader.get_headers_spl(headers)
        self.assertEqual(self.reader.get_contact(headers), self.xml.test.contact.get_text())
    
    def test_get_date(self):
        """get_date() should return string containing when email was sent"""
        headers = self.reader.get_headers_orig(self.msg)
        headers = self.reader.get_headers_spl(headers)
        self.assertEqual(self.reader.get_date(headers), self.xml.test.date.get_text())
    
    def test_get_text_content(self):
        """get_text_content() should return string containing body of email"""
        tc_file = self.xml.test.text_content.get_text()
        tc_file = '<'.join(tc_file.split('&lt;'))
        tc_file = '>'.join(tc_file.split('&gt;'))
        self.assertEqual(self.reader.get_text_content(self.msg.get_payload()), str(tc_file))
    
    def test_get_attachments(self):
        """get_attachments() should return dictionary containing email attachments"""
        attach_file = self.xml.test.attachments.get_text()
        attach_file = cPickle.loads(str(attach_file))
        self.assertEqual(self.reader.get_attachments(self.msg.get_payload()), attach_file)

'''
class EmailSenderTest(unittest.TestCase):
    """EmailSender tests."""
    
    def setUp(self):
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        
        self.sender = EmailSender(config)
        self.xml = XmlWrapper(minidom.parse(os.path.join(PATH, 'test', "email1.test")))
        self.msg = email.message_from_file(open(os.path.join(PATH, 'test', "email1.txt"), 'r'))
    
    def tearDown(self):
        pass
'''

if __name__ == "__main__":
    PATH = project_path()
    config_file = os.path.join(PATH, 'config', "triage.conf")
    unittest.main()