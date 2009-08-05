#!/usr/bin/python

import unittest
import xml.dom.minidom as minidom

import os.path
import ConfigParser
import cPickle
import email

from MHTools import project_path
from MHTools import XmlWrapper
from MHLink import DbLink, WsLink

class DbLinkTest(unittest.TestCase):
    """DbLink tests."""
    
    def setUp(self):
        self.xml = XmlWrapper(minidom.parse(os.path.join(PATH, 'test', "mhlink.test")))
        tags = self.xml.test.database.children()
        
        db_params = {}
        for elem in tags:
            elem_name = str(elem.__str__().strip())
            if not elem_name:
                continue
            db_params[elem_name] = str(elem.get_text())
        
        self.reader = DbLink(**db_params)
    
    def tearDown(self):
        self.reader.close()
    
    def test_set_uuid(self):
        """set_uuid() should return a string containing uuid (without spatial uniqueness)"""
        uuid = self.reader.set_uuid()
        print uuid
        print self.reader.set_uuid()
        self.assertTrue(isinstance(uuid, str))
    
    def test_get(self):
        pass#print self.reader.set_uuid()
    
    def test_insert(self):
        pass
    
    def test_delete(self):
        pass
    
    def test_get_response(self):
        pass
    
    def test_get_earliest_msg(self):
        print self.reader.get_earliest_msg()
    
    def test_get_msg(self):
        pass
    
    def test_get_contents(self):
        pass
    
    def test_get_headers(self):
        pass
    
    def test_get_attachments(self):
        pass
    
    def test_set_uuid(self):
        pass
    
    def test_insert_response(self):
        pass
    
    def test_insert_msg(self):
        pass
    
    def test_insert_contents(self):
        pass
    
    def test_insert_headers(self):
        pass
    
    def test_insert_attachments(self):
        pass
    
    def test_del_response(self):
        pass
    
    def test_del_msg(self):
        pass
    
    def test_del_contents(self):
        pass
        
    def test_del_headers(self):
        pass
    
    def test_del_attachments(self):
        pass

if __name__ == "__main__":
    PATH = project_path()
    config_file = os.path.join(PATH, 'config', "triage.conf")
    unittest.main()