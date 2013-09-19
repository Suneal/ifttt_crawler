'''
Created on Sep 17, 2013

@author: miguel
'''
from ifttt.items import RecipeItem, ChannelItem, EventItem, InputParameterItem, \
    OutputParameterItem, ActionItem
from ifttt.loaders import RecipeLoader, ChannelLoader, EventActionLoader, BaseEweLoader
    
from scrapy import log
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http.request import Request
from scrapy.selector.lxmlsel import HtmlXPathSelector
import urlparse

class IftttRuleSpider(CrawlSpider):
    ''' '''
    name = 'ifttt_rules'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/recipes"]

    rules = (Rule( SgmlLinkExtractor(allow=("recipes/\d+$", "recipes?page=")),
                                #allow=("recipes/118306", "recipes/113399", "recipes/118276", "recipes/115934")),
                    callback="parse_recipe", 
                    follow=False),
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
        loader.add_value('supported_by', 'https://ifttt.com/')
        loader.add_value('url', response.url)
        loader.add_value('id', response.url)
        loader.add_xpath('title','//h1/span[@itemprop="name"]/text()')
        loader.add_xpath('description','//span[@itemprop="description"]/text()')
        loader.add_xpath('event_channel', '//span[@class="recipe_trigger"]/@title')
        loader.add_xpath('event', '//span[@class="recipe_trigger"]/span/text()')
        loader.add_xpath('action_channel', '//span[@class="recipe_action"]/@title')
        loader.add_xpath('action', '//span[@class="recipe_action"]/span/text()')
        loader.add_xpath('created_by', '//span[@itemprop="author"]/a/@href')
        loader.add_xpath('created_at', '//span[@itemprop="datePublished"]/@datetime')
        loader.add_xpath('times_used','//div[3]/div[2]/div[1]/div[3]/text()', re="(\d+)")  
        return loader.load_item()



class IftttChannelSpider(CrawlSpider):
    ''' '''
    name = 'ifttt_channels'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/channels/",
                   ]

    rules = (Rule (SgmlLinkExtractor(allow=("https://ifttt.com/[\_\w]+$"), 
                                     #allow=("https://ifttt.com/sms"), 
                                     deny=("terms$", "login$", "privacy$", "jobs$", "contact$", "join$", "channels$", "wtf$")),
                    callback="parse_channel" ),
    )
    

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
        
        hxs = HtmlXPathSelector(response)
        sequence = [] # subsequent requests
        for url in hxs.select('//div[contains(concat(" ",normalize-space(@class)," ")," channel-page_triggers ")]/div/a/@href').extract():
            url = urlparse.urljoin(response.url, url)
            sequence.append(Request(url, callback=self.parse_event))
             
        for url in hxs.select('//div[contains(concat(" ",normalize-space(@class)," ")," channel-page_actions ")]/div/a/@href').extract():
            url = urlparse.urljoin(response.url, url)
            sequence.append(Request(url, callback=self.parse_action))
        
        # prepare next request
        rq = sequence.pop()
        rq.meta['loader'] = loader
        rq.meta['sequence'] = sequence
        return rq
 
    
    def parse_event(self, response):
        ''' This function parses a event page. 
            Some contracts are mingled with this docstring.
        
            @url https://ifttt.com/channels/gmail/triggers/86
            @returns items 1
            @returns requests 0
            @scrapes id title description
        '''
        log.msg("Parse event at " + str(response.url), level=log.DEBUG)
        
        loader = EventActionLoader(item=EventItem(), response=response)
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//div[@class="show-trigger-action-show"]/div/div[@class="ta_title"]/text()')
        loader.add_xpath('description', '//div[@class="description"]/text()')
        
        hxs = HtmlXPathSelector(response)
        for selector in hxs.select('//div[@class="trigger-field"]'):
            loader.add_value('input_parameters', self._parse_event_iparam(selector))
        
        for selector in hxs.select('//table[@class="show-trigger-action_ingredients_table"]/descendant::tr'):
            loader.add_value('output_parameters', self._parse_event_oparam(selector))

        if response.meta:
            ch_ldr = response.meta['loader']
            ch_ldr.add_value('events_generated', loader.load_item())
            return self._dispatch_request(response)
        else:
            log.msg("No meta data found", level = log.WARNING)
            return loader.load_item()
  
    
    def parse_action(self, response):
        ''' This function parses a action page. 
            Some contracts are mingled with this docstring.
        
            @url https://ifttt.com/channels/gmail/actions/34
            @returns items 1
            @returns requests 0
            @scrapes id title description input_parameters
        '''        
        log.msg("Parse action at " + str(response.url), level=log.DEBUG)
        loader = EventActionLoader(item=ActionItem(), response=response)
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//div[@class="show-trigger-action-show"]/div/div[@class="ta_title"]/text()')
        loader.add_xpath('description', '//div[@class="description"]/text()')

        hxs = HtmlXPathSelector(response)
        for selector in hxs.select('//div[contains(concat(" ",normalize-space(@class)," ")," action-field ")]'):
            loader.add_value('input_parameters', self._parse_action_iparam(selector))
            
        if response.meta:
            ch_ldr = response.meta['loader']
            ch_ldr.add_value('actions_provided', loader.load_item())
            return self._dispatch_request(response)
        else:
            log.msg("No meta data found", level = log.WARNING)
            return loader.load_item()
        
    
    def _parse_event_iparam(self, selector):
        ''' It parses an input parameter from the triggers view '''
        loader = BaseEweLoader(item=InputParameterItem(), selector=selector)
        loader.add_xpath('title', 'label[@class="trigger-field_label"]/text()')
        loader.add_xpath('type', 'label[@class="trigger-field_label"]/@for')
        loader.add_xpath('description', 'descendant::div[@class="action_field_helper_text"]/text()')
        return loader.load_item()
 
    
    def _parse_event_oparam(self, selector):
        ''' It parses an output parameter. It assumes the selector given is a 
            table row, so the xpath used to extract the data rely on that. 
        '''
        loader = BaseEweLoader(item=OutputParameterItem(), selector=selector)
        loader.add_xpath('title', 'td[2]/div/text()')
        loader.add_xpath('description', 'td[4]/text()')
        loader.add_xpath('example', 'td[3]/text()')
        return loader.load_item()


    def _parse_action_iparam(self, selector):
        ''' It parses an input parameter from the actions view '''
        loader = BaseEweLoader(item=InputParameterItem(), selector=selector)
        loader.add_xpath('title', 'label/text()')
        loader.add_xpath('description', 'descendant::div[@class="action_field_helper_text"]/text()')
        return loader.load_item()


    def _dispatch_request(self, response):
        ''' Helper method that fetches the list of pending requests,
            pops one, sets the metadata properly and returns it. 
            In case there is no pending requests it returns the item
        '''
        sequence = response.meta['sequence']
        if sequence:
            rq = sequence.pop()
            rq.meta['loader'] = response.meta['loader']
            rq.meta['sequence'] = sequence
            return rq
        else:
            return response.meta['loader'].load_item()
    
    