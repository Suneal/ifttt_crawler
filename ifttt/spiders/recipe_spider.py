'''
Created on Sep 10, 2013

@author: miguel
'''
from ifttt.items import RecipeItem, ChannelItem, EventItem, InputParameterItem, \
    OutputParameterItem, ActionItem
from ifttt.loaders import RecipeLoader, ChannelLoader, EventLoader, \
    InputParameterLoader, OutputParameterLoader
    
from scrapy import log
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http.request import Request
from scrapy.selector.lxmlsel import HtmlXPathSelector

import re
import urlparse

def get_id (url):
    ''' helper that extracts the id from the url ''' 
    pattern = re.compile('\d+$')
    return pattern.findall(url)
    
    
    
class RecipeSpider(CrawlSpider):
    ''' Spider that crawls by the urls that define recipes and parse them '''
    
    name = 'recipe_page'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/recipes/", ]
    
    rules = (Rule (SgmlLinkExtractor(#allow=("recipes/\d+$", )),
                                     allow=("recipes/117830", )),
                   callback="parse_recipe", 
                   follow=False),
             #Rule (SgmlLinkExtractor(allow=("recipes",))),
    )
    
    def parse_recipe(self, response):
        ''' This function parses a recipe page. 
            Some contracts are mingled with this docstring.
        
            @url https://ifttt.com/recipes/117260
            @returns items 1
            @returns requests 0
            @scrapes url id title description event_channel event action_channel action created_by created_at times_used
        '''
        loader = RecipeLoader(item=RecipeItem(), response=response)
        loader.add_value('url', response.url)
        loader.add_value('id', get_id(response.url))
        loader.add_xpath('title','//h1/span[@itemprop="name"]/text()')
        loader.add_xpath('description','//span[@itemprop="description"]/text()')
        loader.add_xpath('event_channel', '//span[@class="recipe_trigger"]/@title')
        loader.add_xpath('event', '//span[@class="recipe_trigger"]/span/text()')
        loader.add_xpath('action_channel', '//span[@class="recipe_action"]/@title')
        loader.add_xpath('action', '//span[@class="recipe_action"]/span/text()')
        loader.add_xpath('created_by', '//span[@itemprop="author"]/a/text()')
        loader.add_xpath('created_at', '//span[@itemprop="datePublished"]/@datetime')
        loader.add_xpath('times_used','//div[3]/div[2]/div[1]/div[3]/text()', re="(\d+)")  
        return loader.load_item()


class ChannelSpider(CrawlSpider):
    ''' '''
    
    name = 'channel'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/channels/",
                  ]
    
    rules = (Rule (SgmlLinkExtractor(allow=("https://ifttt.com/bitly$"), #allow=("https://ifttt.com/[\_\w]+$"), 
                                     deny=("terms$", "login$", "privacy$", "jobs$", "contact$", "join$", "channels$", "wtf$")),
                    callback="parse_channel" ),
             )

    xpath_to_events  = '//div[contains(concat(" ",normalize-space(@class)," ")," channel-page_triggers ")]/div/a/@href'
    xpath_to_actions = '//div[contains(concat(" ",normalize-space(@class)," ")," channel-page_actions ")]/div/a/@href'



    def parse_channel(self, response):
        ''' This function parses a channel page. 
            Some contracts are mingled with this docstring.
        
            @url https://ifttt.com/bitly
            @returns items 1
            @returns requests 0
            @scrapes id title description commercial_url events_generated actions_provided logo
        '''
        loader = ChannelLoader(item=ChannelItem(), response=response)
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//h1[@class="l-page-title"]/text()')
        loader.add_xpath('description', '//article/div/div[2]/div[2]/div[1]')
        loader.add_xpath('logo', '//img[contains(concat(" ",normalize-space(@class)," ")," channel-icon ")]/@src')
        loader.add_xpath('commercial_url', '//article/div/div[2]/div[2]/div[1]/a/@href')
        loader.add_xpath('events_generated', self.xpath_to_events)
        loader.add_xpath('actions_provided', self.xpath_to_actions)
        yield loader.load_item()
        
        hxs = HtmlXPathSelector(response)
        for url in hxs.select(self.xpath_to_events).extract():
            url = urlparse.urljoin(response.url, url)
            yield Request(url, callback=self.parse_event)
            
        for url in hxs.select(self.xpath_to_actions).extract():
            url = urlparse.urljoin(response.url, url)
            yield Request(url, callback=self.parse_action)
        
 
    
    def parse_event(self, response):
        ''' This function parses a event page. 
            Some contracts are mingled with this docstring.
        
            @url https://ifttt.com/channels/gmail/triggers/86
            @returns items 1
            @returns requests 0
            @scrapes id title description
        '''
        log.msg("Parse event...", level=log.DEBUG)
        loader = EventLoader(item=EventItem(), response=response)
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//div[@class="show-trigger-action-show"]/div/div[@class="ta_title"]/text()')
        loader.add_xpath('description', '//div[@class="description"]/text()')
        
        hxs = HtmlXPathSelector(response)
        for selector in hxs.select('//div[@class="trigger-field"]'):
            loader.add_value('input_parameters', self._parse_event_iparam(selector))
        
        for selector in hxs.select('//table[@class="show-trigger-action_ingredients_table"]/descendant::tr'):
            loader.add_value('output_parameters', self._parse_event_oparam(selector))

        return loader.load_item()
    
  
    
    def parse_action(self, response):
        ''' This function parses a action page. 
            Some contracts are mingled with this docstring.
        
            @url https://ifttt.com/channels/gmail/actions/34
            @returns items 1
            @returns requests 0
            @scrapes id title description input_parameters
        '''        
        log.msg("Parse event...", level=log.DEBUG)
        loader = EventLoader(item=ActionItem(), response=response)
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//div[@class="show-trigger-action-show"]/div/div[@class="ta_title"]/text()')
        loader.add_xpath('description', '//div[@class="description"]/text()')

        hxs = HtmlXPathSelector(response)
        for selector in hxs.select('//div[contains(concat(" ",normalize-space(@class)," ")," action-field ")]'):
            loader.add_value('input_parameters', self._parse_action_iparam(selector))
            
        return loader.load_item()
    
 
    
    def _parse_event_iparam(self, selector):
        '''  
        '''
        loader = InputParameterLoader(item=InputParameterItem(), selector=selector)
        loader.add_xpath('title', 'label[@class="trigger-field_label"]/text()')
        loader.add_xpath('type', 'label[@class="trigger-field_label"]/@for')
        loader.add_xpath('description', 'descendant::div[@class="action_field_helper_text"]/text()')
        return loader.load_item()
    
 
    
    def _parse_event_oparam(self, selector):
        ''' It assumes the selector given is a table row, so the xpath used 
            to extract the data rely on that. 
        '''
        loader = OutputParameterLoader(item=OutputParameterItem(), selector=selector)
        loader.add_xpath('title', 'td[2]/div/text()')
        loader.add_xpath('description', 'td[4]/text()')
        loader.add_xpath('example', 'td[3]/text()')
        return loader.load_item()



    def _parse_action_iparam(self, selector):
        '''  
        '''
        loader = InputParameterLoader(item=InputParameterItem(), selector=selector)
        loader.add_xpath('title', 'label/text()')
        loader.add_xpath('description', 'descendant::div[@class="action_field_helper_text"]/text()')
        return loader.load_item()
