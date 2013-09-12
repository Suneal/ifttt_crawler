'''
Created on Sep 10, 2013

@author: miguel
'''
from ifttt.items import RecipeItem, ChannelItem
from ifttt.loaders import RecipeLoader, ChannelLoader
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector.lxmlsel import HtmlXPathSelector
from scrapy.spider import BaseSpider
import re

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
                   #"https://ifttt.com/google_calendar", 
                  ]
    
    rules = (Rule (SgmlLinkExtractor(allow=("https://ifttt.com/[\_\w]+$"), 
                                     deny=("terms$", "login$", "privacy$", "jobs$", "contact$", "join$", "channels$", "wtf$")),
                    callback="parse_channel" ),
             )

    def parse_channel(self, response):
        loader = ChannelLoader(item=ChannelItem(), response=response)
#         hxs = HtmlXPathSelector(response)
#         description = hxs.select('//article/div/div[2]/div[2]/div[1]/a/text()')
#         description.append(hxs.select('//article/div/div[2]/div[2]/div[1]/text()'))
        loader.add_value('id', response.url)
        loader.add_xpath('title', '//h1[@class="l-page-title"]/text()')
        #loader.add_xpath('description', '//div[contains(concat(" ",normalize-space(@class)," ")," channel-page_description ")]/text()')
        #loader.add_xpath('description', '//article/div/div[2]/div[2]/div[1]/a/text()')
        #loader.add_xpath('description', '//article/div/div[2]/div[2]/div[1]/text()')
        loader.add_xpath('description', '//article/div/div[2]/div[2]/div[1]')
        loader.add_xpath('commercial_url', '//article/div/div[2]/div[2]/div[1]/a/@href')
        #events_generated
        #actions_provided
        return loader.load_item()

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