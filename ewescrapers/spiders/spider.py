'''
Created on Sep 17, 2013

@author: miguel
'''
from ewescrapers import loaders
from ewescrapers.items import RecipeItem, ChannelItem, EventItem, InputParameterItem, \
    OutputParameterItem, ActionItem
from ewescrapers.loaders import RecipeLoader, ChannelLoader, EventActionLoader, \
    BaseEweLoader
from scrapy.http.request import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import urlparse
    

class IftttRuleSpider(CrawlSpider):
    ''' '''
    name = 'ifttt_rules'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/recipes"]

    rules = (Rule(LinkExtractor(allow=("recipes/\d+$", "recipes?page=")),
                                # allow=("recipes/118306", "recipes/113399", "recipes/118276", "recipes/115934")),
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
        loader.add_xpath('title', '//h1/span[@itemprop="name"]/text()')
        loader.add_xpath('description', '//span[@itemprop="description"]/text()')
        loader.add_xpath('event_channel', '//span[@class="recipe_trigger"]/@title')
        loader.add_xpath('event', '//span[@class="recipe_trigger"]/span/text()')
        loader.add_xpath('action_channel', '//span[@class="recipe_action"]/@title')
        loader.add_xpath('action', '//span[@class="recipe_action"]/span/text()')
        loader.add_xpath('created_by', '//span[@itemprop="author"]/a/@href')
        loader.add_xpath('created_at', '//span[@itemprop="datePublished"]/@datetime')
        loader.add_xpath('times_used', '//div[3]/div[2]/div[1]/div[3]/text()', re="(\d+)")  
        return loader.load_item()


class IftttChannelSpider(CrawlSpider):
    ''' '''
    name = 'ifttt_channels'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/channels/",
                   ]
    # def parse(self, response):
    #     request = Request('https://ifttt.com/sms', callback=self.parse_channel)
    #     request.meta['category'] = 'categoria'
    #     return request

    def parse(self, response):
        ''' Parse response from start urls (/channels)
            
            Channels are groups by category. So, this spider extracts the 
            category of each channel, and constructs a request with the meta 
            information of the category (that information would not be 
            available from the channel page otherwise)
        '''
        self.logger.debug("Parse url {}".format(response.url))        

        cat_container = response.xpath('/html/body/div[1]/div/article/div')
        
        # Channels are grouped by category in containers with class '.channel-category'
        for cat in cat_container.css('.channel-category'):
            # extract the title of the category
            cat_title = cat.xpath('h2/text()').extract_first()            
            # extract the link to the channel pages
            for channel in cat.css('ul.channel-grid li'):
                link = channel.xpath('a//@href').extract_first()
                full_link = loaders.contextualize(link, base_url=response.url)
                # Construct request               
                request = Request(full_link, callback=self.parse_channel)
                request.meta['category'] = cat_title
                
                yield request
    

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
        loader.add_value('category', response.meta['category'])
        loader.add_xpath('title', '//h1[@class="l-page-title"]/text()')
        loader.add_xpath('description', '//article/div/div[2]/div[2]/div[1]')
        loader.add_xpath('logo', '//img[contains(concat(" ",normalize-space(@class)," ")," channel-icon ")]/@src')
        loader.add_xpath('commercial_url', '//article/div/div[2]/div[2]/div[1]/a/@href')
        
        
        sequence = []  # subsequent requests
        for url in response.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," channel-page_triggers ")]/div/a/@href').extract():
            url = urlparse.urljoin(response.url, url)
            sequence.append(Request(url, callback=self.parse_event))
             
        for url in response.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," channel-page_actions ")]/div/a/@href').extract():
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
        self.logger.debug("Parse event at " + str(response.url))
        
        loader = EventActionLoader(item=EventItem(), response=response)
        loader.add_value('id', response.url)
        # loader.add_xpath('title', '//div[@class="show-trigger-action-show"]/div/div[@class="ta_title"]/text()')
        loader.add_xpath('title', '//div[@class="l-page-header"]//h1[@class="l-page-title"]/text()')
        loader.add_xpath('description', '//div[@class="description"]/text()')
        
        #for selector in response.xpath('//div[@class="trigger-field"]'):
        for selector in response.css(".trigger_fields .trigger-field"):
            loader.add_value('input_parameters', self._parse_event_iparam(selector))
        
        #for selector in response.xpath('//table[@class="show-trigger-action_ingredients_table"]/descendant::tr'):
        for selector in response.xpath('/html/body/div[1]/div/article/div/div/table/tr'):
            loader.add_value('output_parameters', self._parse_event_oparam(selector))

        if response.meta:
            ch_ldr = response.meta['loader']
            ch_ldr.add_value('events_generated', loader.load_item())
            return self._dispatch_request(response)
        else:
            self.logger.warning("No meta data found")
            return loader.load_item()
  
    
    def parse_action(self, response):
        ''' This function parses a action page. 
            Some contracts are mingled with this docstring.
        
            @url https://ifttt.com/channels/gmail/actions/34
            @returns items 1
            @returns requests 0
            @scrapes id title description input_parameters
        '''        
        self.logger.debug("Parse action at " + str(response.url))
        loader = EventActionLoader(item=ActionItem(), response=response)
        loader.add_value('id', response.url)
        # loader.add_xpath('title', '//div[@class="show-trigger-action-show"]/div/div[@class="ta_title"]/text()')
        loader.add_xpath('title', '//div[@class="l-page-header"]//h1[@class="l-page-title"]/text()')
        loader.add_xpath('description', '//div[@class="description"]/text()')

        for selector in response.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," action-field ")]'):
            loader.add_value('input_parameters', self._parse_action_iparam(selector))
            
        if response.meta:
            ch_ldr = response.meta['loader']
            ch_ldr.add_value('actions_provided', loader.load_item())
            return self._dispatch_request(response)
        else:
            self.logger.warning("No meta data found")
            return loader.load_item()
        
    
    def _parse_event_iparam(self, selector):
        ''' It parses an input parameter from the triggers view '''
        loader = BaseEweLoader(item=InputParameterItem(), selector=selector)
        loader.add_xpath('title', 'label[@class="trigger-field_label"]/text()')
        #loader.add_xpath('title', 'label/text()')
        loader.add_xpath('type', 'label[@class="trigger-field_label"]/@for')
        loader.add_xpath('description', 'descendant::div[@class="trigger_field_helper_text"]/text()')
        return loader.load_item()
 
    
    def _parse_event_oparam(self, selector):
        ''' It parses an output parameter. It assumes the selector given is a 
            table row, so the xpath used to extract the data rely on that. 
        '''
        loader = BaseEweLoader(item=OutputParameterItem(), selector=selector)
        loader.add_xpath('title', 'td/div[@class="ingredient_name"]/text()')
        loader.add_xpath('example', 'td[2]/text()')
        loader.add_xpath('description', 'td[3]/text()')
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
    
    
