'''
Created on Jun 29, 2015

@author: miguel
'''
from scrapy.exporters import CsvItemExporter


class CsvExporter(CsvItemExporter):
    ''' Exporter that inherints from scrapy's csv exporter that includes 
        replacement for `;` character (%3B).
    '''    
    
    def export_item(self, item):
        if self._headers_not_written:
            self._headers_not_written = False
            self._write_headers_and_set_fields_to_export(item)

        fields = self._get_serialized_fields(item, default_value='',
                                             include_empty=True)

        values = [x[1].replace(';', '%3B') for x in fields]
        
        self.csv_writer.writerow(values)