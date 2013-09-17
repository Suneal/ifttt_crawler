'''
Created on Sep 17, 2013

@author: miguel
'''
from jinja2 import Environment, PackageLoader
from scrapy.contrib.exporter import BaseItemExporter
from scrapy import log


class RdfExporter(BaseItemExporter):
    
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
