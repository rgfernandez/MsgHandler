import logging

import sys
import os

log = logging.getLogger('mhtools')

#---------- os.path tools
def project_path(cur_path=''):
    """Return path to trunk."""
    if not cur_path:
        cur_path = __file__
    real_path = os.path.realpath(cur_path)
    # path of code directory
    code_path = os.path.split(real_path)[0]
    # path of main application directory
    main_path = os.path.split(code_path)[0]
    # path of root directory
    return os.path.split(main_path)[0]

def add_module(mod_name=''):
    """Return path to module."""
    if not mod_name:
        return False
    MODULE_PATH = os.path.join(project_path(),'modules',mod_name,'python')
    sys.path.append(MODULE_PATH)
    return True

#---------- Exception tools
class ConfigError(Exception):
    """Exception handling for configuration file."""
    # CHITS SMS code from Bowei Du
    configfile = ''

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return ConfigError.configfile + ': ' + self.msg

if __name__ == '__main__':
    print 'This script is not meant to be run from command line'
    PATH_ROOT = project_path(sys.argv[0])
else:
    PATH_ROOT = project_path(__file__)
    
    FORMAT = "%(asctime)-15s:%(levelname)-3s:%(name)-8s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)