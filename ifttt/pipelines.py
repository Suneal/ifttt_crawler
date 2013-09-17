# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from ifttt.items import ChannelItem, ActionItem, EventItem
from scrapy import log


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