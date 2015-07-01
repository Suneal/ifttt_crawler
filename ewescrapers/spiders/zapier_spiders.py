'''
Created on Jun 21, 2015

@author: miguel
'''
from ewescrapers import loaders
from ewescrapers.items import ChannelItem, EventItem, ActionItem, RecipeItem
from scrapy.spiders.crawl import CrawlSpider
import json
import re
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
        ''' Parse response from start urls (/zapbook) '''
        services_grid = response.css('.services-grid')
        for service in services_grid.css('.service'):
            klass = service.xpath('@class').extract_first() # extract category. A few may not have category
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
            item['category']= self._extract_category(klass)
            
            yield scrapy.Request(abs_url, meta={'channel':item}, callback=self.parse_channel)
    
    def _extract_category(self, text):
        ''' Extracts the category from the string where zapier encodes that information.
            
            The format of the input string consist on a list of css classes. 
            Among them, the category or categories are incuded.
        
            >>> _extract_category('service service-all service-developer-tools service-phone')
            ["developer tools", "service phone"]
        
        '''
        text = text.replace('service-all', '')
        patt = re.compile('(service-([a-zA-Z\-]+))+')
        cat_list = patt.findall(text)
        return [cat[1].replace('-',' ') for cat in cat_list]
        

    def parse_channel(self, response):
        ''' '''
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
            action = ActionItem()
            action['id'] = loaders.generate_uri(title, base_url=response.url, relative_path="actions/")
            action['title'] = title
            action['description'] = description
            channel['actions_provided'].append(action)
            
        return channel
        
        
class ZapierRuleSpider(CrawlSpider):
    ''' This consutls the zapier api (internal api) to get the rules form 
        the zapps 
    '''
    name = 'zapier_rules'
    allowed_domains = ['zapier.com']
    start_urls = ['https://zapier.com/api/v3/recipes?per_page=15&page=1']
    max_page = None
     
    def parse(self, response):
        ''' Parse the json data '''        
        data = json.loads(response.body)
        
        self.logger.debug("Scraping page {} of {}".format(data.get('page', 'X'), data.get('pages', 'Y')) )
        
        for zapp in data['objects']:
            item = RecipeItem()
            abs_url = loaders.contextualize(zapp['url'], base_url="https://zapier.com")
            item['id'] = abs_url
            item['title'] = zapp.get('title', '')
            item['description'] = zapp.get('description', '')
            item['url'] = abs_url
            item['event'] = zapp.get('read_data', {}).get('action', '')
            item['event_channel'] = zapp.get('read_data',{}).get('selected_api', '')
            item['action'] = zapp.get('write_data', {}).get('action', '')
            item['action_channel'] = zapp.get('write_data',{}).get('selected_api', '')
            item['rule'] = unicode(zapp.get('write_data',{}).get('params', ''))
            item['times_used'] = zapp.get('used_human', '')
            item['times_favorite'] = zapp.get('used_score', '')
            item['supported_by'] = 'https://zapier.com'
            yield item
        
        if self.max_page and int(data['page']) >= int(self.max_page):
            self.logger.info("Reached the maximun page given by the user. Mision accomplished!")
        elif data['next_url']:
            abs_url = loaders.contextualize(data['next_url'], base_url='http://zapier.com')
            yield scrapy.Request(abs_url, callback = self.parse)
        else:
            self.logger.info("Could not find next url. Last url parsed:{}".format(response.url))