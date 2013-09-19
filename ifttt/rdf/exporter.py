'''
Created on Sep 15, 2013

@author: miguel
'''
from lxml import etree
from scrapy import log
from scrapy.conf import settings
from scrapy.contrib.exporter import XmlItemExporter, CsvItemExporter
from urlparse import urlparse


class RdfExporter(XmlItemExporter):
    ''' This exporter requieres that each item has for each field an 
        additional attribute with the same name ending by "_label" that 
        representes the tag label used. Samely, if the field is to be 
        a reference instead of a value use an additionsl field ending
        by "_asAttr" whose value is True is needed
        
        This exporter is deprecated in favour of jinja exporter 
        '''
    
    NS = {'owl' : 'http://www.w3.org/2002/07/owl#', 
          'rdf' : 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
          'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
          'xsd' : 'http://www.w3.org/2001/XMLSchema#',
          'dcterms' : 'http://purl.org/dc/terms/',
          'foaf' : 'http://xmlns.com/foaf/0.1/',
          'tags' : 'http://www.holygoat.co.uk/owl/redwood/0.1/tags/',
          'ewe' : 'http://gsi.dit.upm.es/ontologies/ewe/ns/',
          None : 'http://gsi.dit.upm.es/ontologies/ewe/ns/'
    }
    
    def __init__(self, file, **kwargs):
        self.file = file

    def start_exporting(self):
        self.root_element = etree.Element(self._parse_tagname('rdf:RDF'), nsmap=self.NS)

    def export_item(self, item, append_to=None):
        ''' '''
        log.msg("Export item with 'item':" + str(item) + " and 'append_to':" + str(append_to))        
        
        # Extract class string
        if not item.ewe_class:
            log.msg("Cannot find ewe_class", level=log.DEBUG)            
            elem_name = None
        else:
            elem_name = item.ewe_class
              
        # Item root element and subClass entry
        item_root = etree.Element(self._parse_tagname('owl:Class'), nsmap=self.NS)        
        subClass = etree.Element(self._parse_tagname('rdfs:SubClassOf'), nsmap=self.NS)
        subClass.set(self._parse_tagname('rdf:resource'), 
                     self._expand_tagname(elem_name))        
        item_root.append(subClass)
          
        ## iterate over the fields
        for field in item.keys():
            # Continue for fields not populated
            if not field in item:
                log.msg('[RdfExporter] Found EMPTY field:\"' + field + '\".', level=log.DEBUG)
                continue
            
            #   
            value = item[field]
            value_type = type(value)
            log.msg('[RdfExporter] Found field:\"' + field + '\" of type:' + str(value_type), level=log.DEBUG)
            
            # Give 'id' field special treatment              
            if field == 'id':
                if value_type not in [str, unicode]:
                    log.msg("Id value cannot be of type " + str(value_type), level=log.ERROR)
                    continue
                if not is_uri(value):
                    log.msg("Id is not a valud uri:" + str(value) , level=log.ERROR)
                    continue
                item_root.set(self._parse_tagname('rdf:about'), value)
                continue
              
            # Fields whose content is unicode or str is use as...
            if value_type in [str, unicode]:
                elem = etree.SubElement(item_root, self._parse_tagname(getattr(item, field + '_label')), nsmap=self.NS)
                if getattr(item, field + 'asAttr', False): 
                    elem.set(self._parse_tagname('rdfs:resource'), value) # ...either resource...
                else: 
                    elem.text = value # ...or content
            
            # Iterate over the lists
            elif value_type in [list]:
                log.msg("Exporting list field:" + field, level=log.WARNING)
                for ith_value in value:
                    log.msg(">>" + str(type(ith_value)) + "-"+ str(ith_value), level=log.WARNING)
                    elem = etree.SubElement(item_root, self._parse_tagname(getattr(item, field + '_label')), nsmap=self.NS)
                    if type(ith_value) in [str, unicode]:
                        if getattr(item, field + 'asAttr', False): 
                            elem.set(self._parse_tagname('rdfs:resource'), ith_value) # ...either resource...
                        else:
                            elem.text = ith_value # ...or content
                    else:
                        pass
                        self.export_item(ith_value, elem)
            
            else:
                log.msg("By now " + str(value_type) + " are not exported:" + field, level=log.WARNING)
        
        # Append generated element to either the parent element (if given) or the root_elem
        if append_to is None:
            log.msg("Used root element since append_to is " + str(append_to), level=log.DEBUG)    
            self.root_element.append(item_root)
        else:
            log.msg("Used append to " + str(append_to), level=log.DEBUG)
            append_to.append(item_root)
              
        print etree.tostring(item_root, pretty_print=True)
         
#         tree = xml.ElementTree(item_root)
#         self.file.write(etree.toprettyxml())         

    def finish_exporting(self):
        self.file.write(etree.tostring(self.root_element, pretty_print=True))
        self.file.close

    def _export_xml_field(self, name, serialized_value):
        pass

    
    
    
    def _expand_tagname(self, tagname):
        ''' This expands the tagname, in case it shows namespace abbreviation, 
            to the full quialified form   
            
            Args:
                tagname (str|unicode):    The abbreviated tagname to use
              
            Returns:
                string|unicode    The expanded tagname according to the NS dict
              
            Raises:
                KeyError    If the namespage abbreviation is not defined in NS
              
            >>> print _expand_tagname('owl:Class')
            http://www.w3.org/2002/07/owl#Class
            
            >>> print _expand_tagname('http://gsi.dit.upm.es/ontologies/ewe/ns/Channel')
            http://gsi.dit.upm.es/ontologies/ewe/ns/Channel
        '''
        split = str.split(tagname, ':')
        if len(split) == 1:
            return tagname
        if len(split) == 2:
            return ''.join([self.NS[split[0]], split[1]])
        # TODO
        log.msg("The tag provided is not valid:" + str(tagname), level=log.ERROR)


    def _parse_tagname(self, tagname):
        ''' This expands the tagname, in case it shows namespace abbreviation,
            to the lxml namespace and element form
            
            Args:
                tagname (str|unicode):    The abbreviated tagname to use
              
            Returns:
                string|unicode.    The expanded string according to the NS dict
              
            Raises:
                KeyError    If the namespage abbreviation is not defined in NS
              
            >>> print _expand_tagname('owl:Class')
            {http://www.w3.org/2002/07/owl#}Class
            
            >>> print _expand_tagname('http://gsi.dit.upm.es/ontologies/ewe/ns/Channel')
            http://gsi.dit.upm.es/ontologies/ewe/ns/Channel
        '''
        split = str.split(tagname, ':')
        if len(split) == 1:
            return tagname
        if len(split) == 2:
            return '{%s}%s' % (self.NS[split[0]], split[1])
        # TODO
        log.msg("The tag provided is not valid:" + str(tagname), level=log.ERROR)


def is_uri(string):
    ''' This checks wheater a string is a valid uri.
        It is considered a string is a valid uri if after parsing it using
        the urlparse function a scheme and a netloc are extracted.
        
        Args:
            string (str|unicode):    The string to check
        
        Returns:
            bool.    True if the argument is a valid uri. False in other case.
            
        >>> id_uri("http://www.w3.org/2002/07/owl")
        True
        
        >>> id_uri("http://www.w3.org/2002/07/owl#Class")
        True
        
        >>> id_uri("www.w3.org")
        False
    '''
    url = urlparse(string)
    if url.scheme and url.netloc:
        return True
    return False

