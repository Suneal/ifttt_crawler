'''
Created on Sep 10, 2013

@author: miguel
'''
from ifttt.items import RecipeItem, ChannelItem, EventItem, InputParameterItem
from ifttt.loaders import RecipeLoader, ChannelLoader, EventLoader
from scrapy import log
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http.request import Request
from scrapy.selector.lxmlsel import HtmlXPathSelector
from scrapy.spider import BaseSpider
import re
import urlparse

def get_id (url):
    """ helper that extracts the id from the url """ 
    
    pattern = re.compile('\d+$')
    return pattern.findall(url)
    
    
    
class RecipeSpider(CrawlSpider):
    """ Spider that crawls by the urls that define recipes and parse them """
    
    name = 'recipe_page'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/recipes/", ]
    
    rules = (Rule (SgmlLinkExtractor(allow=("recipes/\d+$", )),
                   callback="parse_recipe", 
                   follow=False),
             #Rule (SgmlLinkExtractor(allow=("recipes",))),
    )
    
    def parse_recipe(self, response):
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
    """ """
    
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
        loader = ChannelLoader(item=ChannelItem(), response=response)
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//h1[@class="l-page-title"]/text()')
        loader.add_xpath('description', '//article/div/div[2]/div[2]/div[1]')
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
        log.msg("Parse event...", level=log.DEBUG)
        loader = EventLoader(item=EventItem(), response=response)
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//div[@class="show-trigger-action-show"]/div/div[@class="ta_title"]/text()')
        loader.add_xpath('description', '//div[@class="description"]/text()')
        loader.add_xpath('input_parameters', '//label[@class="trigger-field_label"]/text()')
        loader.add_xpath('output_parameters', '//table[@class="show-trigger-action_ingredients_table"]/descendant::tr/td[1]')
        
        log.msg("Antes del load")
        loader.add_value('extra', InputParameterItem(id="1", title="title prueba", description="description prueba"))
        log.msg("Despues del load")

        yield loader.load_item()
    
    def parse_action(self, response):
        log.msg("Parse action not implemented yet...", level=log.ERROR)
        return None

class EventSpider(CrawlSpider):

    name = 'events'
    allowed_domains = ["ifttt.com"]
    start_urls = [ "https://ifttt.com/linkedin",
                  ]
    
    rules = (Rule (SgmlLinkExtractor(allow=("https://ifttt.com/[\_\w]+/triggers/\d+$")), 
                    callback="parse_event" ),
             )

    def parse_event(self, response):
        pass
    

# class SimpleRecipeSpider(CrawlSpider):
#     base_url =  "https://ifttt.com"
#     recipes_url = "https://ifttt.com/recipes" 
# 
#     name = 'recipe'
#     allowed_domains = ["ifttt.com"]
#     start_urls = [ recipes_url, ]
#     
#     def parse(self, response):
#         log.msg("Start parsing...", level=log.INFO)
#         
#         hxs = HtmlXPathSelector(response)
#         recipes = hxs.select('//article/div[2]/div')
#         items = []
#         for recipe in recipes:
#             item = RecipeItem()
#             #item['id']
#             item['title'] = recipe.select('div/div/a/text()').extract()[0]
#             item['url'] = self.base_url + recipe.select('div/div/a/@href').extract()[0]
#             #item['event']
#             #item['action']
#             item['created_by'] = recipe.select('div/div/div/a/text()').extract()[0]
#             item['created_at'] = recipe.select('div[2]/div/div[1]/text()[3]').re('(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+,\s\d{4}')
#             item['times_used'] = recipe.select('div[2]/div/div[2]/text()').re("(\d+)")[0]
#             items.append(item)
#         return items
# 
#     
# class RecipePaginateSpider(CrawlSpider):
#     base_url =  "https://ifttt.com"
#     recipes_url = "https://ifttt.com/recipes" 
# 
#     name = 'recipe_pages'
#     allowed_domains = ["ifttt.com"]
#     start_urls = [ recipes_url, ]
#     
#     rules = (Rule (SgmlLinkExtractor(allow=("recipes\?page=\d+", ),
#                                      restrict_xpaths=('//a[@class="next_page"]',)),
#                    callback="parse_page", 
#                    follow= True),
#     )
#     
#     def parse_page(self, response):
#         hxs = HtmlXPathSelector(response)
#         recipes = hxs.select('//article/div[2]/div')
#         items = []
#         for recipe in recipes:
#             item = RecipeItem()
#             #item['id']
#             item['title'] = recipe.select('div/div/a/text()').extract()[0]
#             item['url'] = self.base_url + recipe.select('div/div/a/@href').extract()[0]
#             #item['event']
#             #item['action']
#             item['created_by'] = recipe.select('div/div/div/a/text()').extract()[0]
#             item['created_at'] = recipe.select('div[2]/div/div[1]/text()[3]').re('(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+,\s\d{4}')
#             item['times_used'] = recipe.select('div[2]/div/div[2]/text()').re("(\d+)")[0]
#             items.append(item)
#         return items