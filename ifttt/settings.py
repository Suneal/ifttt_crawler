# Scrapy settings for ifttt project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

# BOT_NAME = 'ifttt'
# 
SPIDER_MODULES = ['ifttt.spiders']
NEWSPIDER_MODULE = 'ifttt.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'ifttt (+http://www.yourdomain.com)'

ITEM_PIPELINES = {
     'ifttt.pipelines.RemoveEmptyItemsPipeline' : 900,
#     # 'ifttt.pipelines.LogPipeline',
#     # 'ifttt.pipelines.FileExporterPipeline',
#     'ifttt.pipelines.IdRegistryPipeline' : 100
      'ifttt.pipelines.PopulateParameterIds' : 700
    }

FEED_EXPORTERS = {
    # 'rdf' : 'ifttt.rdf.jinja_exporters.JinjaExporter',
    'rdf' : 'ifttt.rdf.jinja_exporters.JinjaExporterMultifile',
    # 'rdf2' : 'ifttt.rdf.exporter.RdfExporter',
    'json': 'scrapy.exporters.JsonItemExporter',
    'jsonlines': 'scrapy.exporters.JsonLinesItemExporter',
    'csv': 'scrapy.exporters.CsvItemExporter',
    'xml': 'scrapy.exporters.XmlItemExporter',
}
