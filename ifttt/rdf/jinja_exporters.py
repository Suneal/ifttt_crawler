'''
Created on Sep 17, 2013

@author: miguel
'''
from ifttt.items import RecipeItem
from jinja2 import Environment, PackageLoader
from os.path import dirname, abspath, splitext
from scrapy import log
from scrapy.contrib.exporter import BaseItemExporter
from urlparse import urlparse
import os
import re

import logging
logger = logging.getLogger(__name__)

class JinjaExporterMultifile(BaseItemExporter):
    ''' 
        Args:
            file(File) - a file
    '''
    def __init__(self, file, **kwargs):
        # This should extract the name of the package automatically
        self.file = file
        self.env = Environment(loader=PackageLoader('ifttt', 'templates'))
        # self.env = Environment(loader=PackageLoader('ifttt', 'templates'), 
        #                        trim_blocks=True, 
        #                        lstrip_blocks=True)
        self.folder = dirname(abspath(file.name))
        self.extension = splitext(file.name)[1]

    def export_item(self, item):
        ''' This method is called each time the scrapped_item signal is 
            received (as usual). It is responsible of invoking the template 
            renderer with the appropriate arguments.
            
            Args:
                item(Item):    The item scraped            
        '''
        logger.debug("[JinjaExporter] Exporting item " + str(item))
        
        # manage utf-8
        import sys
        reload(sys)
        sys.setdefaultencoding('utf-8')
        
        if not item.template:
            logger.warning("No template attribute for item:" + str(item))
            return
        
        # Generate item representation
        template = self.env.get_template('{}{}'.format(item.template, self.extension))
        logger.debug("[JinjaExporter] Template loaded")        
        out = template.render(item=item)
        logger.debug("[JinjaExporter] Template rendered")
        
        # Save to file
        # fpath = os.path.join(os.path.abspath(self.file), self.get_valid_name(item))
        fpath = os.path.join(self.folder, self.get_valid_name(item))
        with open(fpath, 'wt') as fw:        
            fw.write(out)
        fw.close()
    
    def get_valid_name(self, item):
        ''' Common method used to get the name of each file used. 
            The policy is as follows. 
            
            If the item given is of type RecipeItem, the numerical id
            is taken preceded by the TaskAutomationServiced use to 
            orquestrate the rule. 
            
            If it fails or the items is not of type RecipeITem, 'title' is 
            used as name.
            
            The extension used is the extension of the file given when 
            creating the exporter.
        '''
        if isinstance(item, RecipeItem):
            try:
                id = re.search("\d+$", item['id']).group()
                tas = urlparse(item['supported_by']).netloc
                return 'Rule_' + tas + '_' + id + self.extension
            except:
                pass
        
        name = str(item['title']) + self.extension
        return str.replace(name, ' ', '_')
        
        
