'''
Created on Sep 17, 2013

@author: miguel
'''
from ifttt.rdf.errors import ExporterException
from jinja2 import Environment, PackageLoader
from scrapy import log
from scrapy.contrib.exporter import BaseItemExporter
import os


class JinjaExporter(BaseItemExporter):
    
    def __init__(self, file, **kwargs):
        # This should extract the name of the package automatically
        self.env = Environment(loader=PackageLoader('ifttt', 'templates'))
        self.file = file

    def start_exporting(self):
        pass
    
    def export_item(self, item):
        ''' This method is called each time the scrapped_item signal is 
            received (as usual). It is responsible of invoking the template 
            renderer with the appropriate arguments.
            
            Args:
                item(Item):    The item scraped            
        '''
        log.msg("[JinjaExporter] Exporting item " + str(item), level=log.DEBUG)
        
        if not item.template:
            log.msg("No template attribute for item:" + str(item), level=log.WARNING)
            return
        
        template = self.env.get_template(item.template + '.rdf')
        log.msg("[JinjaExporter] Template loaded", level=log.DEBUG)        
        out = template.render(item=item)
        log.msg("[JinjaExporter] Template rendered", level=log.DEBUG)        
        self.file.write(out)
        
    
    def finish_exporting(self):
        self.file.close()


class JinjaExporterMultifile(JinjaExporter):
    '''
        Args:
            file(File) - a folder that points 
    '''
    def __init__(self, file, **kwargs):
        # This should extract the name of the package automatically
        self.env = Environment(loader=PackageLoader('ifttt', 'templates'))
#         if not os.path.isdir(file):
#             raise ExporterException("JinjaExporterMultifile file argument representa a folder instead of a simple file")
#         if not os.path.exists(file):
#             raise ExporterException("The given folder does not exist")
        self.file = file

    def export_item(self, item):
        ''' This method is called each time the scrapped_item signal is 
            received (as usual). It is responsible of invoking the template 
            renderer with the appropriate arguments.
            
            Args:
                item(Item):    The item scraped            
        '''
        log.msg("[JinjaExporter] Exporting item " + str(item), level=log.DEBUG)
        
        if not item.template:
            log.msg("No template attribute for item:" + str(item), level=log.WARNING)
            return
        
        # Generate item representation
        template = self.env.get_template(item.template + '.rdf')
        log.msg("[JinjaExporter] Template loaded", level=log.DEBUG)        
        out = template.render(item=item)
        log.msg("[JinjaExporter] Template rendered", level=log.DEBUG)
        
        # Save to file
        #fpath = os.path.join(os.path.abspath(self.file), self.get_valid_name(item))
        fpath = os.path.join('scraped_data/channels/', self.get_valid_name(item))
        with open(fpath, 'w') as fw:        
            fw.write(out)
        fw.close()
    
    def get_valid_name(self, item):
        return "%s.rdf" % str(item['title'])