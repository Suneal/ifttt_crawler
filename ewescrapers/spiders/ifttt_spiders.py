'''
Created on Jun 21, 2015

@author: miguel
'''
from ewescrapers import loaders
from ewescrapers.items import ChannelItem, EventItem, ActionItem, InputParameterItem, \
    OutputParameterItem
from scrapy.spiders.crawl import CrawlSpider
import scrapy


class IftttChannelSpider(CrawlSpider):
    ''' '''
    name = 'iftttch'
    allowed_domains = ['ifttt.com']
    start_urls = ['https://ifttt.com/channels']

    # def parse(self, response):
    #     channel = ChannelItem()
    #     channel['category'] = u'prueba'
    #     channel['title'] = u"SMS"
    #     request = scrapy.Request('https://ifttt.com/sms', callback=self.parse_channel)
    #     request.meta['item'] = channel
    # return request
        
    
    def parse(self, response):
        """ Parse response from start urls (/channels) """
        self.logger.debug("Parse url {}".format(response.url))        

        cat_container = response.xpath('/html/body/div[1]/div/article/div')
        
        # Channels are grouped by category in containers with class '.channel-category'
        for cat in cat_container.css('.channel-category'):
            # extract the title of the categoty
            cat_title = cat.xpath('h2/text()').extract_first()
            self.logger.debug("cat title {}".format(cat_title))
            # extract the link to the channl pages with their description
            for channel in cat.css('ul.channel-grid li'):
                link = channel.xpath('a//@href').extract_first()
                self.logger.debug(u"Link: {}".format(link))
                channel_title = channel.xpath('a/span//text()').extract_first()
                self.logger.debug(u"ChannelTitle: {}".format(channel_title))
                # Include the category in the request
                channel = ChannelItem()
                channel['category'] = loaders.strip(cat_title)
                channel['title'] = loaders.strip(channel_title)
                
                self.logger.debug("Post Item")
                                
                full_link = loaders.contextualize(link, base_url=response.url)
                self.logger.debug(u"Found link to channel {}".format(full_link))
                                
                request = scrapy.Request(full_link, callback=self.parse_channel)
                request.meta['item'] = channel
                
                yield request
                
        # Alternative selectors for backup        
        # cat_container = response.css('.channel-categories') # equivalent
        #for cat in cat_container.xpath('div'):
            #cat_title = cat.css('.channel-category__title').xpath('text()').extract_first()
            #cat_title = cat.xpath('h2/text()').extract_first()
            #for channel in cat.xpath('ul/li'):
                #channel_title = channel.css('a .channel-grid-item__title').xpath('text()').extract_first()
                #link = channel.xpath('a//@href//text()').extract_first()
        
    def parse_channel(self, response):
        """ From urls like (/<name_of_the_channel>) """
        self.logger.debug('Parse Channel from url {}'.format(response.url))
        
        # Retrieve the item
        channel = response.meta['item']
        channel['description'] = u"".join(response.xpath('/html/body/div[1]/div/article/div/div[2]/div[2]/div[1]//text()').extract()).strip()
        channel['logo'] = response.xpath('/html/body/div[1]/div/article/div/div[2]/div[1]/img/@src').extract_first()
        channel['commercial_url'] = response.url
        channel['id'] = response.url
        
        #events_sel = response.xpath('/html/body/div[1]/div/article/div/div[6]/div[1]')
        #actions_sel = response.xpath('/html/body/div[1]/div/article/div/div[6]/div[2]')
        # Alternative using css
        events_sel = response.css('.channel-page_triggers')
        actions_sel = response.css('.channel-page_actions')
        
        channel['events_generated'] = []
        channel['actions_provided'] = []
        
        self.logger.debug('Event1')
        self.logger.debug(events_sel.xpath('div/a'))
        
        # Iterate over the events
        for event_sel in events_sel.xpath('div/a'):
            self.logger.debug('Event')
            event_link = event_sel.xpath('@href').extract_first()
            absolute_link = loaders.contextualize(event_link)

            event = EventItem()
            event['id'] = absolute_link
            event['title'] = event_sel.xpath('div/h3[@class="trigger-list_item_name"]/text()').extract_first()
            event['description'] = event_sel.xpath('div/p[@class="trigger-list_item_desc"]/text()').extract_first()            
            
            event['input_parameters'] = []
            
            for field in event_sel.css('.fields_list').xpath('div'):
                input_param = InputParameterItem()
                ititle = field.xpath('text()').extract_first()
                input_param['id'] = loaders.generate_uri(ititle, relative_path='properties/', is_prop=True)
                input_param['title'] = ititle
                input_param['see_also'] = absolute_link
                event['input_parameters'].append(input_param)
            
                # All fields are tagged with this class, by now...
                assert field.xpath('@class').extract_first() == 'single_field_item'
            
            request = scrapy.Request(absolute_link, callback=self.parse_event)
            request.meta['event'] = event
            request.meta['channel'] = channel
            
            self.logger.debug('Yield with request {}'.format(request))            
            yield request
            
#             channel['events_generated'].append(event)

        self.logger.debug('Finished with events for channel {}. Lets proceed with actions'.format(channel))
        self.logger.debug('Title{}'.format(channel['title']))
        self.logger.debug('events{}'.format(channel['events_generated']))
        
        # iterate over the actions
        for action_sel in actions_sel.xpath('div/a'):
            self.logger.debug('Action')
            action_link = action_sel.xpath('@href').extract_first()
            absolute_link = loaders.contextualize(action_link)
            
            self.logger.debug("ACTION_LINK{}".format(absolute_link))
            
            action = ActionItem()
            action['id'] = absolute_link
            action['title'] = action_sel.xpath('div/h3[@class="action-list_item_name"]/text()').extract_first()
            action['description'] = action_sel.xpath('div/p[@class="action-list_item_desc"]/text()').extract_first()            
            
            action['input_parameters'] = []
            
            for field in action_sel.css('.fields_list').xpath('div'):
                input_param = InputParameterItem()
                ititle = field.xpath('text()').extract_first()
                input_param['id'] = loaders.generate_uri(ititle, relative_path='properties/', is_prop=True)
                input_param['title'] = ititle
                input_param['see_also'] = absolute_link
                action['input_parameters'].append(input_param)
                # All fields are tagged with this class, by now...
                assert field.xpath('@class').extract_first() == 'single_field_item'
            
            channel['actions_provided'].append(action)

        self.logger.debug('Finised with channel {}. Return'.format(channel))
        self.logger.debug('Title{}'.format(channel['title']))
        self.logger.debug('events{}'.format(channel['events_generated']))                
        yield channel
            

    def parse_event(self, response):
        """ From urls like: 
            /channels/<channel_name>/triggers/<triggeridid>-<trigger-slug>
          
            For instance: /channels/gmail/triggers/86-new-email-in-inbox-from
            
            This only scrapers the output paramters of the event. 
        """
        event = response.meta['event']
        channel = response.meta['channel']
        self.logger.debug('Entering parse event with event {} and channel {}'.format(event, channel))
        
        event['output_parameters'] = []
        rows_sel =response.xpath('/html/body/div[1]/div/article/div/div/table/tr')
        for row in rows_sel:
            ingredient = OutputParameterItem()
            ingredient['title'] = row.xpath('td/div[@class="ingredient_name"]/text()').extract_first()
            ingredient['example'] = row.xpath('td[2]/text()').extract_first()
            ingredient['description'] = row.xpath('td[3]/text()').extract_first()
            event['output_parameters'].append(ingredient)
            
        self.logger.debug('Return after parse event'.format(event, channel))
        channel['events_generated'].append(event)
        self.logger.debug('Title{}'.format(channel['title']))
        self.logger.debug('events{}'.format(channel['events_generated']))
        return
            