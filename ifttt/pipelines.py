# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import log
from ifttt.items import ChannelItem


class IftttPipeline(object):
    def process_item(self, item, spider):
        return item


class LogPipeline(object):
    """ Dummy logPipeline for learning purposes only """
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
        if isinstance(item, ChannelItem):
            filename = 'scraped_data/channels/' + item['title'] + '.rdf'
            with open(filename, 'w') as f:
                f.write(item['title'])
                f.write('\n')
            f.close()
        return item
    
    def open_spider(self, spider):
        log.msg("[FileExporterPipeline] Open spider:" + spider.name, level=log.DEBUG)
    
    def close_spider(self, spider):
        log.msg("[FileExporterPipeline] Close spider:" + spider.name, level=log.DEBUG)