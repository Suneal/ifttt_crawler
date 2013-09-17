'''
Created on Sep 17, 2013

@author: miguel
'''

from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy.settings import Settings
from scrapy import log, signals
from ifttt.spiders.recipe_spider import RecipeSpider 

spider = RecipeSpider(domain="ifttt.com")
crawler = Crawler(Settings())
crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
crawler.configure()
crawler.crawl(spider)
crawler.start()
log.start()
reactor.run() # the script will block here until the spider_closed signal was sent