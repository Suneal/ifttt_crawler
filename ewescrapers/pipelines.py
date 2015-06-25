# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from ewescrapers import loaders
from ewescrapers.items import ChannelItem, ActionItem, EventItem, RecipeItem
from scrapy.item import Item
import ewescrapers
import pickle
import logging

logger = logging.getLogger(__name__)


class IdRegistryPipeline(object):
    '''  Pipeline that is responsible of gathering the URI of resources 
         scraped, creating a dict that maps them to their title, and using
         that dict to replace the references among objects made to the title 
         with references made to the URI.
         
         Spiders with 'channel' in its name are supposed to fill the id map and
         save it to disk. For each Channel, Event or Action item they find, the
         field with name 'title' is stored as key to the URI of the item.
         
         For instance, consider the item shown:
         >>> print item['title']
         Gmail
         >>> print item['id']
         https://ifttt.com/Gmail
         
         This pipeline will add the following entry to the dict:
         >>> print id_ds['Gmail']
         https://ifttt.com/Gmail
         
         It is important to point out that it also performs the search crawling 
         through the fields of the items.
         
         Spiders with 'rule' in its name are supposed to use the ids collected 
         and replace the references to instances made by title with references
         by URI.
         
         For instance. The field 'event_channel' stores the reference to the 
         channel whose event triggers the rule considered. It should be a URI.
         >>> print item['event_channel'] 
         'Gmail'
         
         After pipeline processing:
         >>> print item['event_channel'] 
         'https://ifttt.com/Gmail'          
    '''
    ds_filename = 'id_datastore'
    REPLACE_FIELDS = ['action', 'action_channel', 'event', 'event_channel']
    id_ds = {}    
    
    def __init__(self, *args, **kwargs):
        try:
            with open(self.ds_filename, 'rb') as f:
                self.id_ds = pickle.load(f)
            f.close()
        except IOError:
            pass
    
    def open_spider(self, spider):
        if 'channel' in spider.name:
            self.id_ds = {}
        elif 'rule' in spider.name and not self.id_ds:
            logger.warning("No ids loaded")
            
    
    def process_item(self, item, spider):
        ''' '''
        if isinstance(item, RecipeItem):
            # Make substitutions
            for field in self.REPLACE_FIELDS:
                replacement = self.id_ds.get(item[field], None)
                if replacement:
                    logger.debug("[IdRegistryPipeline] Field " + field + " replaced by:" + replacement)
                    item[field] = replacement
        else:
            self._register_item(item)
        return item
    
    
    def close_spider(self, spider):
        # save to file
        if 'channel' in spider.name:
            with open(self.ds_filename, 'wt') as f:
                pickle.dump(self.id_ds, f)
            f.close()
        elif 'rule' in spider.name:
            pass


    def _register_item(self, item):
        
        logger.debug("[IdRegistryPipeline] Register_item: {}".format(item))
        if type(item) in [ChannelItem, EventItem, ActionItem]:
            # Register new ids
            if not item['title']:
                logger.warning("[IdRegistryPipeline] The item consideren has no title field:" + str(item))
            elif type(item['title']) not in [str, unicode]:
                logger.warning("[IdRegistryPipeline] Type of title field is:" + str(type(item['title'])))
            elif self.id_ds.get(item['title'], None):
                logger.warning("[IdRegistryPipeline] The Item <" + str(item['title']) + 
                        "> alreay exists on the data map. Current mapping is:" + 
                        str(self.id_ds[item['title']]) + ". New proposal is " + str(item['id']))
            else:
                logger.debug("[IdRegistryPipeline] The Item with title <" + str(item['title']) + 
                        "> has been associated to the id:" + str(item['id']))
                self.id_ds[item['title']] = item['id']
            
            
        # Check for field with items as value
        # Here, we consider all items not only those with replacements
        if isinstance(item, Item):
            logger.debug("[IdRegistryPipeline] Fields:{}".format(item.keys()))
            for field in item.keys():
                val = item[field]
                logger.debug("[IdRegistryPipeline] Field: {} >> {}".format(field, val))
                if isinstance(val, Item):
                    logger.debug("[IdRegistryPipeline] It is item:{}".format(val))
                    self._register_item(val)
                elif isinstance(val, list):
                    logger.debug("[IdRegistryPipeline] It is a list:{}".format(val))
                    for i in val:
                        logger.debug("List member: {}".format(i))
                        self._register_item(i)
                    

class RemoveEmptyItemsPipeline(object):
    ''' This pipeline removes all those items scraped where all fields are 
        empty. This particular situation can occur due to the xpath specific 
        formater 'text()' does not extract the text from child nodes. Thus,
        it may be that we fill all fields in the item but all those fields are 
        empty.
        
        Usually, this task usually is quite simple. However, some spider 
        implementations neste items -including them as values of other item 
        fields- In that case, all fields need to be validated because for those
        nested items no scraped_item signal is triggered. 
        
        This pipeline has high priority since there is no need to keep 
        processing those items that will be removed.
    '''    
    def __init__(self):
        logger.debug("[RemoveEmptyItemsPipeline] Initialize...")

    def process_item(self, item, spider):
        return self._process_item(item)
    
    def _process_item(self, item):
        ''' Remove al not-populated items and nested item stored as fields '''
        
        # Because of recursiveness we may find args that are not items
        if not isinstance(item, Item): 
            return item
        
        # iterate over the fields
        ret = None
        for field, value in item.items():
            if isinstance(value, Item):
                item[field] = self._process_item(item)  # Field items  re-assign
            elif isinstance(value, list):
                item[field] = [i for i in value if self._process_item(i)]  # lists are re-assigned
            elif value or ret:  # When value of the field is not None
                ret = item
                
        if not ret:
            logger.debug("[RemoveEmptyItemsPipeline] Removed empty item")
            
        return ret


class PopulateParameterIds(object):
    ''' This pipeline, for each channel scrapeed, iterates over its events and 
        actions, and then over their params. No channel objects are skipped. 
        
        For each of those params it adds the id field, constructed from the 
        title. To do so, it uses a function that always generates the same URI
        given a title.
    '''    
    def __init__(self):
        logger.debug("[PopulateParameterIds] Initialize...")

    def process_item(self, item, spider):
        
        if type(item) is ewescrapers.items.ChannelItem:
            # Process channel
            for event in item.get('events_generated', []):
                for param in event.get('input_parameters', []):
                    if 'title' in param:
                        param['id'] = self._generate_uri(param['title'])
                for param in event.get('output_parameters', []):
                    if 'title' in param:
                        param['id'] = self._generate_uri(param['title'])
            for action in item.get('actions_provided', []):
                for param in action.get('input_parameters', []):
                    if 'title' in param:
                        param['id'] = self._generate_uri(param['title'])
        return item
    
    def _generate_uri(self, title):
        """ Auxiliar method called to generate the uris """
        return loaders.generate_uri(title, relative_path="properties/", is_prop=True)