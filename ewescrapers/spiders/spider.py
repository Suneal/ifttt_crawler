'''
Created on Sep 17, 2013

@author: miguel
'''
from ewescrapers import loaders
from ewescrapers.items import RecipeItem, ChannelItem, EventItem, \
    InputParameterItem, OutputParameterItem, ActionItem
from ewescrapers.loaders import RecipeLoader, ChannelLoader, EventActionLoader, \
    BaseEweLoader
from scrapy.http.request import Request
from scrapy.spiders import CrawlSpider
import re
import scrapy
import urlparse

class IftttRulesSpider(CrawlSpider):
    ''' This spider scrapes ifttt recipe pages to extract the rules.
        
        The strategy followed consist on getting the recpies by id. 
        The url of the recipe consist on an id and a slug, however giving the 
        id, the server redirects to the correct recipe url is that exists.
        Thus, the spider hit all recipe ids and scrapes those that exist.
        
        This spider requires authentication since a the information provided 
        by the recipes is different wheter the user is logged in or not. 
        
        The crawling sequence is as follows:
        
        1. Hit the login page (/login) and perform a login using a `FormRequest`. 
           That includes the "authenticity_token".
        2. If login process fails, the process is over. We know it failed if it 
           redirects to the login page again.
        3. If the login process suceeded the recipe urls are scraped one by one, 
           using its simple pattern /recipes/<count>. In those cases the recipe 
           exist, the response will redirect to the url of the recipe.
        4. Once the url of each recipe is reached, the rule is scraped
        
    '''
    name = 'ifttt_rules'
    start_urls = ['https://ifttt.com/login']
    
    def __init__(self, username=None, password=None, num_rules=80, *args, **kwargs):
        """ Read arguments """
        super(IftttRulesSpider, self).__init__(*args, **kwargs)
        self.ifttt_username = username
        self.ifttt_password = password 
        self.num_rules = num_rules

    def parse(self, response):
        """ Get authenticity token and perform login """
        if self.ifttt_username is None or self.ifttt_password is None:
            self.logger.info("No credentials provided. Carry on without loggin in...")
            #return Request(self.recipes_url, callback=self.parse_rule)
        else:
            self.logger.info("Loging in into Ifttt...")

        # Authenticity token        
        at = response.css('[name="authenticity_token"]').xpath('@value').extract_first()
        self.logger.debug(u'Authenticity token {}'.format(at))
        # LoginForm Request
        return scrapy.FormRequest.from_response(
            response,
            formdata={'login': self.ifttt_username, 'password': self.ifttt_password, 'remember_me':'1', 'commit':'Sign in', 'authenticity_token':at},
            callback=self._after_login
        )
    
    def _after_login(self, response):
        ''' Hit the recipe urls by id '''
        for n in range(self.num_rules):
            yield Request("https://ifttt.com/recipes/{}".format(n), callback=self.parse_rule)
        
        
    def parse_rule(self, response):
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
        event = response.css('#live_trigger_fields_complete h4').xpath('text()').extract_first()
        loader.add_value('event', event)
        loader.add_xpath('action_channel', '//span[@class="recipe_action"]/@title')
        action = response.css('#live_action_fields_complete h4').xpath('text()').extract_first()
        loader.add_value('action', action)
        loader.add_xpath('created_by', '//span[@itemprop="author"]/a/@href')
        loader.add_xpath('created_at', '//span[@itemprop="datePublished"]/@datetime')
        loader.add_xpath('times_used', '//span[@class="stats_item__use-count__number"]/text()')
        loader.add_xpath('times_favorite', '//span[@class="stats_item__favorites-count__number"]/text()')
        return loader.load_item()
    
    
class IftttPagesSpider(CrawlSpider):
    ''' '''
    name = 'ifttt_rule_pages'
    start_urls = ['https://ifttt.com/login']
    recipes_url = 'https://ifttt.com/recipes'    
    

    def __init__(self, username=None, password=None, max_page=3, *args, **kwargs):
        """ Read arguments """
        super(IftttPagesSpider, self).__init__(*args, **kwargs)
        self.ifttt_username = username
        self.ifttt_password = password                
        self.max_page = max_page

    def parse(self, response):
        """ Get authenticity token and perform login """
        if self.ifttt_username is None or self.ifttt_password is None:
            self.logger.info("No credentials provided. Carry on without loggin in...")
            return self._iterate_over_pages()
        else:
            self.logger.info("Loging in into Ifttt...")
        
        at = response.css('[name="authenticity_token"]').xpath('@value').extract_first()
        self.logger.debug(u'Authenticity token {}'.format(at))
                
        return scrapy.FormRequest.from_response(
            response,
            formdata={'login': self.ifttt_username, 'password': self.ifttt_password, 'remember_me':'1', 'commit':'Sign in', 'authenticity_token':at},
            callback=self._after_login
        )
        
    def _after_login(self, response):
        ''' Check if login whent right and trigger'''
        if 'Sign in' in response.body:
            self.logger.warning("Login process failed")            
        else:
            self.logger.info("Login process succeeded!")
            
            csrf_token = response.xpath('//meta[@name="csrf-token"]/@content').extract_first()
            self.logger.debug("csrf_token = {}".format(csrf_token))
            
            return Request('https://ifttt.com/recipes', callback=self._find_links, meta={'page':1})
        
    
    def _iterate_over_pages(self, response):
        ''' '''
        csrf_token = response.xpath('//meta[@name="csrf-token"]/@content').extract_first()
        
        for n in range(self.max_page):
            self.logger.info("Receipt page number {}".format(n))
            yield Request('https://ifttt.com/recipes?page={}'.format(n), callback=self._find_links, meta={'page':n}, headers={'X-CSRF-Token':csrf_token})
    
    def _find_links(self, response):
        ''' '''
        slug_re = re.compile("recipes/[0-9][-a-zA-Z0-9_]+$")
        n = response.meta['page'] # pagenumber
        
        # Iterate over recipe links
        for link in response.xpath('//a/@href').extract():
            if slug_re.search(link):
                url = urlparse.urljoin("https://ifttt.com", link)   
                print 'match {} {}'.format(url, n)                
                yield Request(url, callback=self.parse_rule)
        
        # Get next page
        csrf_token = response.xpath('//meta[@name="csrf-token"]/@content').extract_first()
        self.logger.debug("csrf_token = {}".format(csrf_token))
        
        n = n + 1
        if n <= self.max_page:
            yield Request('https://ifttt.com/recipes?page={}'.format(n), callback=self._find_links, meta={'page':n}, headers={'X-CSRF-Token':csrf_token, "Referer": "https://ifttt.com/recipes", "X-Requested-With": "XMLHttpRequest"})            

        
    def parse_rule(self, response):
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
        event = response.css('#live_trigger_fields_complete h4').xpath('text()').extract_first()
        loader.add_value('event', event)
        loader.add_xpath('action_channel', '//span[@class="recipe_action"]/@title')
        action = response.css('#live_action_fields_complete h4').xpath('text()').extract_first()
        loader.add_value('action', action)
        loader.add_xpath('created_by', '//span[@itemprop="author"]/a/@href')
        loader.add_xpath('created_at', '//span[@itemprop="datePublished"]/@datetime')
        loader.add_xpath('times_used', '//span[@class="stats_item__use-count__number"]/text()')
        loader.add_xpath('times_favorite', '//span[@class="stats_item__favorites-count__number"]/text()')
        loader.add_xpath('featured', '//div[@title="featured"]/@title')
        return loader.load_item()
        
        
#         trigger = response.css('.recipe_trigger .recipe_component-icon').xpath('@href').extract_first()
#         self.logger.debug(u"Trigger {}".format(trigger))
#         action = response.css('.recipe_action .recipe_component-icon').xpath('@href').extract_first()
#         self.logger.debug(u"Action {}".format(action))
        
#         tgs = response.css('.trigger_fields h4').xpath('text()').extract_first()
#         self.logger.debug(u"Triggers+ {}".format(tgs))
#         tgs = response.css('#live_trigger_fields_complete h4').xpath('text()').extract_first()
#         self.logger.debug(u"O bien Triggers+ {}".format(tgs))
#         
#         acs = response.css('#live_action_fields_complete h4').xpath('text()').extract_first() 
#         self.logger.debug(u"Actions {}".format(acs))


class IftttChannelSpider(CrawlSpider):
    ''' This spider crawls ifttt and extracts all information of all channels 
        linked in the channel index page (/channels).
        
        This spider requires no authentication.
        
        This is a complex crawler that extracts information from different pages:
        
        * First, from channels-index-page (/channels) the links of the 
          channel pages as well as the category of each of them is extracted.
        * Second, from the channel page, the rest of the information about the 
          channel is extracted, and also, the links to the relted triggers and 
          actions.           
        * Finally the trigger and action pages are scraped and the information 
          from events and actions is appended to the channel. 
          
        Each request is completing the information from the channel, thus all 
        of them need to be performed in sequence to compile all the information.
        
        From the channel-index-page, the category is passed to the channel-page 
        requests. Then, all trigger/action requests are constructed. In this 
        case, they are organized as a sequence, and the requests are, one by 
        one, completing the information of the channel.
        
        The sequence of requests is handled as follows:
        
        1. First, it is constructed by the `parse_channel` method using the 
           links to triggers and actions from the action page. The requests 
           are appended to a list. The callback is conveniently assigned: 
           `parse_event` for trigger links, and `parse_action` to action 
           links.
        2. Secondly, the first request is popped from the list. The rest of the 
           list is passed as metadata to this request, as well as the channel 
           (particularly, the `loader` object used). That request is returned
           to be processed by scrapy.
        3. Then, the callback method is called once the data is scraped from 
           the requested url. This, constructs a Event/Action item that is 
           given to the channel loader (from the meta). The next request is 
           popped from the list, and steps 2 and 3 are repeated until the 
           sequence is empty. Helper method `_dispatch_request` is in charge of
           handling the sequences.
    '''
    name = 'ifttt_channels'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/channels/" ]
    
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
    
    
