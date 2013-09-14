'''
Created on Sep 11, 2013

Scrapy Item Loaders definition

@author: miguel
'''
from scrapy import log
from scrapy.contrib.loader import XPathItemLoader
from scrapy.contrib.loader.processor import MapCompose, TakeFirst, Join, Identity
import html2text
import re
import urlparse

def strip(s):
    """ This removes all whitespaces at the beggining or end of the given 
        string. Every textual input is modified using this function. If the
        argument is unicode, it performs some html2text operations before 
        strip to remove all remaining html tags."""
    
    if isinstance(s, str):
        log.msg("[loaders] Call strip with string:" + s,level=log.DEBUG)
        return s.strip().replace('\n','')

    if isinstance(s, unicode):
        converter = html2text.HTML2Text()
        converter.ignore_links = True
        return converter.handle(s).strip().replace('\n','')
    
    return s # If not str or unicode, do nothing

def erase_channel(s):
    """ This function removes the word 'Channel' at the end of the string."""
    
    log.msg("[loaders] Call erase_channel with:" + str(s), level=log.DEBUG)
    return re.sub('\s+Channel$', '', s)  


def make_absolute(url):
    """ This appends the base url at the begining of the url string. """
    
    log.msg("[loaders] Make absolute url of:" + url, level=log.DEBUG)
    return urlparse.urljoin("https://ifttt.com", url)

    
def channel_validator(channel_name):
    """ This validates each the channel name matches any of the names of 
        channels defined. It corrects deviations in channel names, and 
        guaranties there is a single channel name for each channel defined.
    """        
    return channel_name


def log_in(field):
    log.msg("[loaders] Input processor loader for:" + str(field), level=log.DEBUG)
    return field
    
    
class RecipeLoader(XPathItemLoader):
    """ Loader specifically created for handling RecipeItems. 
        By default, it strips all inputs and takes the first element 
        of the list as output.        
        It also performs additional processing
        to assure the channels' names matches any of the defined channels' 
        names. 
    """        
    default_input_processor = MapCompose(log_in, strip)
    default_output_processor = TakeFirst()
    
    action_channel_in = MapCompose(log_in, channel_validator)
    event_channel_in = MapCompose(log_in, channel_validator)
    
    
class ChannelLoader(XPathItemLoader):
    """ 
    """
    
    default_input_processor = MapCompose(log_in, strip)
    default_output_processor = TakeFirst()
    
    title_in = MapCompose(log_in, strip, erase_channel, log_in) # first function applied first
    description_out = Join()
    
    events_generated_in = MapCompose(log_in, strip, make_absolute)
    events_generated_out = Identity()
    actions_provided_in = MapCompose(log_in, strip, make_absolute)
    actions_provided_out = Identity()
    
class EventLoader(XPathItemLoader):
    """
    """
    default_input_processor = MapCompose(log_in, strip)
    default_output_processor = TakeFirst()
    
    input_parameters_out = Identity()
    output_parameters_out = Identity()
    
