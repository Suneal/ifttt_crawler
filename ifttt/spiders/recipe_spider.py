'''
Created on Sep 10, 2013

@author: miguel
'''
from ifttt import loaders
from ifttt.items import RecipeItem, ChannelItem, EventItem, InputParameterItem, \
    OutputParameterItem, ActionItem
from ifttt.loaders import RecipeLoader, ChannelLoader, EventActionLoader, \
    BaseEweLoader
from scrapy.http.request import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.selector.lxmlsel import HtmlXPathSelector
from scrapy.spiders import CrawlSpider, Rule
import re
import scrapy
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
    
    rules = (Rule (LinkExtractor(# allow=("recipes/\d+$", )),
                                     allow=("recipes/117830",)),
                   callback="parse_recipe",
                   follow=False),
             # Rule (SgmlLinkExtractor(allow=("recipes",))),
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
        loader.add_value('id', get_id(response.url))
        loader.add_xpath('title', '//h1/span[@itemprop="name"]/text()')
        loader.add_xpath('description', '//span[@itemprop="description"]/text()')
        loader.add_xpath('event_channel', '//span[@class="recipe_trigger"]/@title')
        loader.add_xpath('event', '//span[@class="recipe_trigger"]/span/text()')
        loader.add_xpath('action_channel', '//span[@class="recipe_action"]/@title')
        loader.add_xpath('action', '//span[@class="recipe_action"]/span/text()')
        loader.add_xpath('created_by', '//span[@itemprop="author"]/a/text()')
        loader.add_xpath('created_at', '//span[@itemprop="datePublished"]/@datetime')
        loader.add_xpath('times_used', '//div[3]/div[2]/div[1]/div[3]/text()', re="(\d+)")  
        return loader.load_item()


class ChannelSpider(CrawlSpider):
    ''' This spider crawls ifttt and extracts all information of all channels 
        linked in the channel index page (/channels).
        
        This is a complex crawler that extracts information from different pages:
        
        * First, from channels-index-page (/channels) the links of the 
          channel pages as well as the category of each of them is extracted.
        * Second, from the channel page, the rest of the information about the 
          channel is extracted, and also, the links to the relted triggers and 
          actions.           
        * Finally the trigger and action pages are scraped and the information 
          from events and actions is appended to the channel. 
          
        Each request is completing the information from the channel, thus all 
        of them need to be performed in secuende to compile all the information.
        
        From the channel-index-page, the category is passed to the channel-page 
        requests. Then, all trigger/action requests are constructed. In this 
        case, they are organized as a sequence, and the requests are, one by 
        one, completing the information of the channel.
    '''
    name = 'channel'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/channels/",
                  ]
    
    rules = (Rule (LinkExtractor(allow=("https://ifttt.com/yammer"),  # allow=("https://ifttt.com/[\_\w]+$"), 
                                     deny=("terms$", "login$", "privacy$", "jobs$", "contact$", "join$", "channels$", "wtf$")),
                    callback="parse_channel"),
             )

    xpath_to_events = '//div[contains(concat(" ",normalize-space(@class)," ")," channel-page_triggers ")]/div/a/@href'
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
        channel = loader.load_item()
        yield channel
        
        hxs = HtmlXPathSelector(response)
        for url in hxs.select(self.xpath_to_events).extract():
            url = urlparse.urljoin(response.url, url)
            yield Request(url, meta={'channel': channel} , callback=self.parse_event)
            
        for url in hxs.select(self.xpath_to_actions).extract():
            url = urlparse.urljoin(response.url, url)
            yield Request(url, meta={'channel': channel}, callback=self.parse_action)
 
        
    def parse_event(self, response):
        ''' This function parses a event page. 
            Some contracts are mingled with this docstring.
        
            @url https://ifttt.com/channels/gmail/triggers/86
            @returns items 1
            @returns requests 0
            @scrapes id title description
        '''
        self.logger.debug("Parse event...")
        loader = EventActionLoader(item=EventItem(), response=response)
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//div[@class="show-trigger-action-show"]/div/div[@class="ta_title"]/text()')
        loader.add_xpath('description', '//div[@class="description"]/text()')
        
        hxs = HtmlXPathSelector(response)
        for selector in hxs.select('//div[@class="trigger-field"]'):
            loader.add_value('input_parameters', self._parse_event_iparam(selector))
        
        for selector in hxs.select('//table[@class="show-trigger-action_ingredients_table"]/descendant::tr'):
            loader.add_value('output_parameters', self._parse_event_oparam(selector))

        event = loader.load_item()
    
        if response.meta and response.meta.hasattr('channel'):
            channel = response.meta['channel']
            self.logger.debug("Meta" + str(channel))
            channel['events_generated'] = event
        else:
            self.logger.debug("No metadata found")
        return event
  
  
    def parse_action(self, response):
        ''' This function parses a action page. 
            Some contracts are mingled with this docstring.
        
            @url https://ifttt.com/channels/gmail/actions/34
            @returns items 1
            @returns requests 0
            @scrapes id title description input_parameters
        '''        
        self.logger.debug("Parse event...")
        loader = EventActionLoader(item=ActionItem(), response=response)
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//div[@class="show-trigger-action-show"]/div/div[@class="ta_title"]/text()')
        loader.add_xpath('description', '//div[@class="description"]/text()')

        hxs = HtmlXPathSelector(response)
        for selector in hxs.select('//div[contains(concat(" ",normalize-space(@class)," ")," action-field ")]'):
            loader.add_value('input_parameters', self._parse_action_iparam(selector))
            
        action = loader.load_item()
        
        if response.meta and 'channel' in response.meta:
        #if response.meta and response.meta.hasattr('channel'):
            channel = response.meta['channel']
            self.logger.debug("Meta" + str(channel))
            channel['actions_provided'] = action
        else:
            self.logger.debug("No meta")
        
        return action;
    
 
    def _parse_event_iparam(self, selector):
        ''' 
        '''
        loader = BaseEweLoader(item=InputParameterItem(), selector=selector)
        loader.add_xpath('title', 'label[@class="trigger-field_label"]/text()')
        loader.add_xpath('type', 'label[@class="trigger-field_label"]/@for')
        loader.add_xpath('description', 'descendant::div[@class="action_field_helper_text"]/text()')
        return loader.load_item()
 
    
    def _parse_event_oparam(self, selector):
        ''' It assumes the selector given is a table row, so the xpath used 
            to extract the data rely on that. 
        '''
        loader = BaseEweLoader(item=OutputParameterItem(), selector=selector)
        loader.add_xpath('title', 'td[2]/div/text()')
        loader.add_xpath('description', 'td[4]/text()')
        loader.add_xpath('example', 'td[3]/text()')
        return loader.load_item()


    def _parse_action_iparam(self, selector):
        ''' 
        '''
        loader = BaseEweLoader(item=InputParameterItem(), selector=selector)
        loader.add_xpath('title', 'label/text()')
        loader.add_xpath('description', 'descendant::div[@class="action_field_helper_text"]/text()')
        return loader.load_item()
