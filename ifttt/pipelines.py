# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from ifttt.items import ChannelItem, ActionItem, EventItem
from scrapy import log
from scrapy.item import Item


class IftttPipeline(object):
    def process_item(self, item, spider):
        return item

class IdRegistryPipeline(object):
    ''' '''
    
    event_ds = {}
    action_ds = {}
    
    def __init__(self, *args, **kwargs):
        # read from file
        pass
    
    def process_item(self, item, spider):
        if isinstance(item, ChannelItem):
            for event in item['events_generated']:
                log.msg("Event:" + str(event), level = log.DEBUG)
                pass
            
            for action in item['actions_provided']:
                log.msg("Action:" + str(action), level = log.DEBUG)
                pass
                
            return item
        
        if isinstance(item, EventItem):
            if self.event_ds.get(item['title'], None):
                log.msg("[IdRegistryPipeline] The Event <" + str(item['title']) + 
                        "> alreay exists on the data map. Current mapping is:" + 
                        str(self.event_ds[item['title']]) + ". New proposal is " + str(item['id']), 
                        log.WARNING)
            else:
                log.msg("[IdRegistryPipeline] The event with name <" + str(item['title']) + 
                        "> has been associated to the id:" + str(item['id']), 
                        level = log.DEBUG)
                self.event_ds[item['title']] = item['id']
                
        elif isinstance(item, ActionItem):
            if self.action_ds.get(item['title'], None):
                log.msg("[IdRegistryPipeline] The Event <" + str(item['title']) + 
                        "> alreay exists on the data map. Current mapping is:" + 
                        str(self.action_ds[item['title']]) + ". New proposal is " + str(item['id']), 
                        log.WARNING)
            else:
                log.msg("[IdRegistryPipeline] The event with name <" + str(item['title']) + 
                        "> has been associated to the id:" + str(item['id']), 
                        level = log.DEBUG)
                self.action_ds[item['title']] = item['id']
        
        return item
    
    def close_spider(self, spider):
        if spider.name == 'channel':
            log.msg('Event Ids:')
            log.msg(str(self.event_ds))
            log.msg('Action Ids')
            log.msg(str(self.action_ds))
                

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
            log.msg("[RemoveEmptyItemsPipeline] Found field " + field + ":" + str(value) ,level=log.DEBUG)
            if isinstance(value, Item):
                item[field] = self._process_item(item) # Field items  re-assign
            elif isinstance(value, list):
                item[field] = [i for i in value if self._process_item(i)] # lists are re-assigned
            elif value or ret: # When value of the field is not None
                ret = item
                
        if not ret:
            log.msg("[RemoveEmptyItemsPipeline] Removed empty item", level=log.DEBUG)
            
        return ret



class LogPipeline(object):
    ''' Dummy logPipeline for learning purposes only '''
    def __init__(self):
        log.msg("[LogPipeline] Initialize...", level=log.DEBUG)
        pass

    def process_item(self, item, spider):
        log.msg("[LogPipeline] Process Item:<" + str(item) + "< found by spider:<" + spider.name + ">", level=log.DEBUG)
        return item
    
    def open_spider(self, spider):
        log.msg("[LogPipeline] Open spider:" + spider.name, level=log.DEBUG)
    
    def close_spider(self, spider):
        log.msg("[LogPipeline] Close spider:" + spider.name, level=log.DEBUG)


class FileExporterPipeline(object):

    def __init__(self):
        log.msg("[FileExporterPipeline] Initialize...", level=log.DEBUG)
        pass

    def process_item(self, item, spider):
        log.msg("[FileExporterPipeline] Process Item:<" + str(item) + "> found by spider:<" + spider.name + ">", level=log.DEBUG)
        filename = 'scraped_data/channels/' + item['title'] + '.rdf'
        with open(filename, 'w') as f:
            f.write('Item:')                
            f.write(str(item))
            f.write('\n')
            f.write('Attributes of item:')
            f.write(getattr(item, 'title_label'))                
            f.write('\n')
            for field in item:
                f.write('Field ')
                f.write(str(type(field)))
                f.write(':')
                f.write(str(field))
                f.write('=')
                value = item[field]
                f.write(str(type(value)))
                f.write(':')
                f.write(str(value))
                f.write('\n')
                
        f.close()
        return item
    
    def open_spider(self, spider):
        log.msg("[FileExporterPipeline] Open spider:" + spider.name, level=log.DEBUG)
    
    def close_spider(self, spider):
        log.msg("[FileExporterPipeline] Close spider:" + spider.name, level=log.DEBUG)