'''
Created on Sep 11, 2013

Scrapy Item Loaders definition

@author: miguel
'''
from scrapy.contrib.loader import XPathItemLoader
from scrapy.contrib.loader.processor import MapCompose, TakeFirst, Join, \
    Identity
import html2text as h2t
import re
import unicodedata
import urlparse

def strip(s):
    ''' This performs some html2text operations to remove html tags before 
        stripping all remaining all whitespaces at the beggining or end of the given 
        string. If there are sone line breaks inside the string they are also removed.
        Unicode arguments are encoded as 'utf8'. All error are ignored. 
        
        Args:
            s(str):    The string to format
            
        Returns:
            The formatted string free of leading whitespaces.
            
        >>> strip('   hello world   ')
        'hello world'
        
        >>> strip('Hi\n there')
        'hi there'
        
        >>> strip(u'<span>hello <b>friends</b></span>')
        'hello friends'
        '''
    
    if isinstance(s, str):
        try:
            converter = h2t.HTML2Text()
            converter.ignore_links = True
            plain = converter.handle(s)
        except UnicodeDecodeError:
            plain = s
        
        return plain.strip().replace('\n', '')
#         return s.strip().replace('\n','')

    if isinstance(s, unicode):
#         s = unicodedata.normalize('NFKD', s)
        return strip(s.encode('ascii', 'ignore'))
#         return strip(str(s))
    
    return s  # If not str or unicode, do nothing

def erase_channel(s):
    ''' This function removes the word 'Channel' at the end of the string given.
    
        Args:
            s(str):    The string to format
        
        Returns:
            The tidy string
            
        >>> erase_channel('Google Drive Channel')
        'Google Drive0
        
        >>> erase_channel('Disovery Channel Channel')
        'Discovery Channel'
        
        >>> erase_channel('Use the channel')
        'Use the channel'
    '''
    return re.sub('\s+Channel$', '', s)  


def contextualize(url):
    ''' This appends the base url at the begining of the url string.
        
        Args:
            url(str):    The relative url
        
        Return:
            The absolute url
            
        >>> contextualize('people/JackSparow')
        'https://ifttt.com/people/JackSparow'
        
        >>> contextialize('./channels/youtuve')
        'https://ifttt.com/channels/youtuve'
    '''    
    return urlparse.urljoin("https://ifttt.com", url)


class BaseEweLoader(XPathItemLoader):
    ''' Base loader that strips all inputs and takes the first element 
        of the list as output.
    '''
    default_input_processor = MapCompose(strip)
    default_output_processor = TakeFirst()
    

class RecipeLoader(BaseEweLoader):
    ''' RecipeItems loader. In addition to BaseEweLoader, it contextualizes 
        user uris. '''
    created_by_in = MapCompose(contextualize)
    
    
class ChannelLoader(BaseEweLoader):
    ''' ChannelItems loader. In addition to BaseEweLoader it formats the 
        title, contextualizes the logo uri and keep the list of events and 
        actions in the output.
    '''
    title_in = MapCompose(strip, erase_channel)  # first function applied first
    description_out = Join()
    logo_in = MapCompose(contextualize)
    
    events_generated_out = Identity()
    actions_provided_out = Identity()
    
class EventActionLoader(BaseEweLoader):
    ''' EventItem and Action item loaders. In addition to BaseEweLoader, 
        it keeps the list of input and output parameters in the output.
    '''
    input_parameters_out = Identity()
    output_parameters_out = Identity()
    
