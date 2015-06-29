'''
Created on Jun 21, 2015

@author: miguel
'''
from ewescrapers import loaders
from ewescrapers.items import ChannelItem, EventItem
from scrapy.spiders.crawl import CrawlSpider
import scrapy


class ZapierChannelSpider(CrawlSpider):
    ''' This spider scrapes all channels (apps) from Zapier starting from their  
        App Directory (https://zapier.com/zapbook/).
        
        The information is scraped from the main page (where the id, title, 
        description, category are scraped from) and the page of each channel 
        (logo, triggers and actions).
    '''
    name = 'zapier_channels'
    allowed_domains = ['zapier.com']
    start_urls = ['https://zapier.com/zapbook/']

    
    def parse(self, response):
        """ Parse response from start urls (/zapbook) """
        services_grid = response.css('.services-grid')
        for service in services_grid.css('.service'):
            klass = service.xpath('@class').extract_first() # extract category. A few may not have category
            category = klass.replace('service-all', '').replace('service','').replace('-','').strip()
            description = service.xpath('@data-description').extract() # remove the ending <div>category</div>
            #logo is a background-image css property
            url = service.xpath('a[@class="title"]/@href').extract_first() 
            abs_url = loaders.contextualize(url, "https://zapier.com")
            title =  service.xpath('a[@class="title"]/text()').extract_first().strip()
            
            item = ChannelItem()
            item['id'] = abs_url
            item['title'] = title
            item['description'] = description
            item['commercial_url'] = abs_url
            item['category'] = category
            
            yield scrapy.Request(abs_url, meta={'channel':item}, callback=self.parse_channel)
            

    def parse_channel(self, response):
        """ """
        channel = response.meta['channel']
        channel['logo'] = response.xpath('//*[@id="app"]/div[1]/div[2]/div/div[2]/div[1]/div/img/@src').extract_first()

        channel['events_generated'] = []
        channel['actions_provided'] = []
        
        # Get triggers
        triggers_sel = response.css('.column.one-third.left-when-wide .service-actions')
        trigger_divs = triggers_sel.xpath('div/text()').extract()
        # take the divs in pairs
        for title, description in zip(*[trigger_divs[x::2] for x in (0, 1)]):
            event = EventItem()
            event['id'] = loaders.generate_uri(title, base_url=response.url, relative_path="triggers/")
            event['title'] = title
            event['description'] = description
            channel['events_generated'].append(event)
            
        # Get actions
        actions_sel = response.css('.column.one-third.middle-when-wide .service-actions')
        action_divs = actions_sel.xpath('div/text()').extract()
        # take the divs in pairs
        for title, description in zip(*[action_divs[x::2] for x in (0, 1)]):
            action = EventItem()
            action['id'] = loaders.generate_uri(title, base_url=response.url, relative_path="actions/")
            action['title'] = title
            action['description'] = description
            channel['actions_provided'].append(action)
            
        return channel
        