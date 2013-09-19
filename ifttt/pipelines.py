# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from ifttt.items import ChannelItem, ActionItem, EventItem, RecipeItem
from scrapy import log
from scrapy.item import Item
import pickle


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
    ds_filename= 'id_datastore'
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
            log.msg("No ids loaded", level=log.WARNING)
            
    
    def process_item(self, item, spider):
        ''' '''
        if isinstance(item, RecipeItem):
            # Make substitutions
            for field in self.REPLACE_FIELDS:
                replacement = self.id_ds.get(item[field], None)
                if replacement:
                    log.msg("[IdRegistryPipeline] Field " + field + " replaced by:" + replacement, level=log.DEBUG)
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
        
        log.msg("Register_item:" + str(item))
        if type(item) in [ChannelItem, EventItem, ActionItem]:
            # Register new ids
            if not item['title']:
                log.msg("[IdRegistryPipeline] The item consideren has no title field:" + str(item), level=log.WARNING)
            elif type(item['title']) not in [str, unicode]:
                log.msg("[IdRegistryPipeline] Type of title field is:" + str(type(item['title'])), level=log.WARNING)
            elif self.id_ds.get(item['title'], None):
                log.msg("[IdRegistryPipeline] The Item <" + str(item['title']) + 
                        "> alreay exists on the data map. Current mapping is:" + 
                        str(self.id_ds[item['title']]) + ". New proposal is " + str(item['id']), 
                        log.WARNING)
            else:
                log.msg("[IdRegistryPipeline] The Item with title <" + str(item['title']) + 
                        "> has been associated to the id:" + str(item['id']), 
                        level = log.DEBUG)
                self.id_ds[item['title']] = item['id']
            
            
        # Check for field with items as value
        # Here, we consider all items not only those with replacements
        if isinstance(item, Item):
            log.msg("Fields:" + str(item.keys()), level=log.DEBUG)
            for field in item.keys():
                val = item[field]
                log.msg("Field: " + str(field) + ">>" + str(val), level=log.DEBUG)
                if isinstance(val, Item):
                    log.msg("It is item:" + str(val))
                    self._register_item(val)
                elif isinstance(val, list):
                    log.msg("It is a list:" + str(val), level=log.DEBUG)
                    for i in val:
                        log.msg("List member: " + str(i), level=log.DEBUG)
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
        log.msg("[RemoveEmptyItemsPipeline] Initialize...", level=log.DEBUG)

    def process_item(self, item, spider):
        return self._process_item(item)
    
    def _process_item(self, item):
        ''' Remove al not-populated items and nested item stored as fields '''
        
        log.msg("[RemoveEmptyItemsPipeline] Processing item:" + str(item), level=log.DEBUG)
        # Because of recursiveness we may find args that are not items
        if not isinstance(item, Item): 
            return item
        
        # iterate over the fields
        ret = None
        for field, value in item.items():
            log.msg("[RemoveEmptyItemsPipeline] Found field " + str(field) + ":" + repr(value) ,level=log.DEBUG)
            if isinstance(value, Item):
                item[field] = self._process_item(item) # Field items  re-assign
            elif isinstance(value, list):
                item[field] = [i for i in value if self._process_item(i)] # lists are re-assigned
            elif value or ret: # When value of the field is not None
                ret = item
                
        if not ret:
            log.msg("[RemoveEmptyItemsPipeline] Removed empty item", level=log.DEBUG)
            
        return ret

