'''
Created on Sep 18, 2013

@author: miguel
'''

class ExporterException(Exception):
    '''  '''
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
    