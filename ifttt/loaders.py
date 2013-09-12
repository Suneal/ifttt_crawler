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

def strip(s):
    """ This removes all whitespaces at the beggining or end of the given 
        string. Every textual input is modified using this function. If the
        argument is unicode, it performs some html2text operations before 
        strip to remove all remaining html tags."""
    
    if isinstance(s, str):
        log.msg("Call strip with string:" + s,level=log.DEBUG)
        return s.strip().replace('\n','')
    try:
        log.msg("Call strip with object of type:" + str(type(s)) + ": " + str(s) ,level=log.DEBUG)
    except UnicodeEncodeError:
        pass
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    return converter.handle(s).strip().replace('\n','')

def erase_channel(s):
    """ This function removes the word 'Channel' at the end of the string."""
    
    log.msg("Call erase_channel with:" + str(s), level=log.DEBUG)
    return re.sub('\w+Channel$', '', s)  
    
def channel_validator(channel_name):
    """ This validates each the channel name matches any of the names of 
        channels defined. It corrects deviations in channel names, and 
        guaranties there is a single channel name for each channel defined.
    """        
    return channel_name
    
    
class RecipeLoader(XPathItemLoader):
    """ Loader specifically created for handling RecipeItems. 
        By default, it strips all inputs and takes the first element 
        of the list as output.        
        It also performs additional processing
        to assure the channels' names matches any of the defined channels' 
        names. 
    """        
    default_input_processor = MapCompose(strip)
    default_output_processor = TakeFirst()
    
    action_channel_in = MapCompose(channel_validator)
    event_channel_in = MapCompose(channel_validator)
    
    
class ChannelLoader(XPathItemLoader):
    """ """
    
    default_input_processor = MapCompose(strip)
    default_output_processor = TakeFirst()
    
    title_in = MapCompose(strip, erase_channel) # last function applied first
    description_out = Join()
    events_generated_out = Identity()
    actions_provided_out = Identity()