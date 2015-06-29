'''
Created on Sep 11, 2013

Scrapy Item Loaders definition

@author: miguel
'''
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join, \
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

def handle_ks(s):
    ''' This function format big numbers with 'k' in their representation.
    
        Args:
            s(str):    The string witht the number representation
            
        Returns:
            The number replacing ks by its 1000 multiplier
    
        >>> handle_ks('1.1k')
        1100
        
        >>> handle_ks('62k')
        62000
    '''
    if s.find('k') != -1:
        return str(int(float(s.replace('k',''))*1000))        
    else:
        return s

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


def contextualize(url, base_url="https://ifttt.com"):
    ''' This appends the base url at the begining of the url string.
        
        Args:
            url(str):        The relative url
            base_url(str):   The base url. By default it is: https://ifttt.com
        
        Return:
            The absolute url
            
        >>> contextualize('people/JackSparow')
        'https://ifttt.com/people/JackSparow'
        
        >>> contextialize('./channels/youtube')
        'https://ifttt.com/channels/youtube'
        
        >>> contextialize('youtube', base_url="https://ifttt.com/')
        'https://ifttt.com/youtube'
    '''
    return urlparse.urljoin(base_url, url)

def generate_uri(text, base_url="https://ifttt.com", relative_path="", is_prop=False):
    ''' This generates a valid URI for the text given.
        
        Args:
            text(str):             The text to use
            base_url(str):         The base url. By default it is: https://ifttt.com
            relative_path(str):    Relative path to intercalate between the base path and the text
            is_prop(bool):         Indicates if the url represents a property
        
        Return:
            The absolute uri
            
        >>> generate_uri('my uri')
        'https://ifttt.com/MyUri
        
        >>> generate_uri('my uri', relative_path='relative-uris/')
        'https://ifttt.com/relative-uris/MyUri
        
        >>> generate_uri('my uri', relative_path='relative-uris/', is_prop=True)
        'https://ifttt.com/relative-uris/myUri        
        
        And be careful with mising slash
        
        >>> generate_uri('my uri', relative_path='relative-uris')
        'https://ifttt.com/relative-urisMyUri
    '''
    camel_text = ''.join(x for x in text.title() if not x.isspace())
    if is_prop:
        # when it is a prop, first letter should be lowercase
        camel_text = camel_text[:1].lower() + camel_text[1:] if text else ''
        
    path = u"{rel}{text}".format(rel=relative_path, text=camel_text)
    return urlparse.urljoin(base_url, path)


class BaseEweLoader(ItemLoader):
    ''' Base loader that strips all inputs and takes the first element 
        of the list as output.
    '''
    default_input_processor = MapCompose(strip)
    default_output_processor = TakeFirst()
    

class RecipeLoader(BaseEweLoader):
    ''' RecipeItems loader. In addition to BaseEweLoader, it contextualizes 
        user uris. 
    '''
    created_by_in = MapCompose(contextualize)
    times_favorite_in = MapCompose(strip, handle_ks)    
    times_used_in = MapCompose(strip, handle_ks)
    
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