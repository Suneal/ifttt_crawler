[Ewe-Scrappers](http://gsi.dit.upm.es) 
==================================

Introduction
---------------------

This project scrapes information from the major Task Automation Services (for now ifttt and Zapier are supported) in a semantic format. The extracted data is modelled using the Evented WEb ontology ([EWE]) developed by the Intelligent Systems Group ([GSI]). For this purpose the [scrapy] framework is used.  

The EWE ontology models Channels (called apps in Zapier) and Rules (Ifttt's recipes and Zapier's zapps). The data described using EWE may be loaded in a semantic endpoint to be consulted using SPARQL. Although particular exporters are provided to support EWE's format, the data may also be exported using the built-in exporters of scrapy (csv, json, etc.)

Documentation
----------------------

Detailed documentation may be found at the Wiki page of this proyect ([Wiki] (./wiki) ).


Usage
----------------------

Several spiders are provided with this project. These are developed using [scrapy], so its usage it that specified  by scrapy's documentation. For instance, for running the spider that extracts ifttt channels the following command should be executed.

    scrapy crawl ifttt_channels
  
The installation and configuration of the scrapper is detailed below.

### Installation

First of all, clone this repository in your system

    git clone https://github.com/miguelcb84/ewe-scrapers.git
    cd ewe-scrapers

Then, install the requirements. It is preferable to work with virtualenvs.

    mkvirtualenv ewescrapers
    pip install -r requirements.txt

And the scrapers are ready!

### Running the spiders

There are several spiders for scraping data from different sources. Spiders are invoked by name, as follows:

    scrapy crawl <spider_name>

Give the source and the data to scrape, the name of the spider to used is given by the following table.
    
| data \ source | ifttt.com      | zapier.com      |
|---------------|----------------|-----------------|
| channels      | ifttt_channels | zapier_channels |
| rules         | ifttt_rules    | zapier_rules    |

For instance, in order to scrape the channels from zapier `zapier_channels` should be used.

### Spider arguments

#### Authentication with ifttt_rules channel

Ifttt does not provide all the information about rules unless you are logged in. Thus, the `ifttt_rules` spider performs login. A user at ifttt.com is required. The username and the password are given as arguments as follows:

    scrapy crawl ifttt_rules -a username=<username> -a password=<password>

#### Selecting maximun number of rules to scrape

The number of channels it not big enough to implement a process to limit depth of the crawling. However, both Ifttt and Zapier gather plenty of rules. Thus spiders that scrape rules have provide arguments to limit the number of rules extracted.

    scrapy crawl ifttt_rules -a username=<username> -a password=<password> -a from_rule=1 -a to_rule=5000

`from_rule` and `to_rule` control the number of rules that will be scraped. This spider scrapes rules with consecutive ids. The `from_rule` sets lowest limit of ids and `to_rule` the highest id of the range (not included).

    scrapy crawl zapier_rules -a max_page=50

`max_page` controls the maximun number of pages or rules scraped. If ommited, it will crawl through all available pages
    

### Output data formats

This project also comes with a few additional exporters to those already provided by scrapy. To tell scrapy that it has to output the outcome into a file two arguments should be used: `t` that specifies the format and `o` that gives the output filename. For instance, the following command scrapes zapier's channels and saves the data in json format in apps.json file.

    scrapy crawl ifttt_rules -t json -o apps.json

#### Exporting to csv

Scrapy already provides a default csv exporter, however, it does not escape `;` characters. Because of that, some rows may have missplaced data. To solve it a new exporter that substitutes the scrapy built-in exporter is provided. To use that provider the `csv` format should be used. That exporter replaces `;` character with `%3B` (its representation in urls).

Since it may be nasty in some cases (and also because there is an issute with non textual fields), the built-in format is also provided selecting format `csvold`.

#### Exporting to semantic format

Rdf and n3 format are also supported. In those case, the exporting process is a bit different. The format that must be selected is `jinja`. Then, the channels are exported in individual files for easy reading. The output file is used to select the folder in which the files are creted, and the format used. As said, rdf and n3 are supported. 

These are some examples:

    scrapy crawl ifttt_channels -t jinja -o ifttt.n3
    scrapy crawl zapier_channels -t jinja -o output/zapier.rdf


### Contact

For more information, contact us through: http://gsi.dit.upm.es

![GSI Logo](http://gsi.dit.upm.es/templates/jgsi/images/logo.png)

[EWE]: http://www.gsi.dit.upm.es/ontologies/ewe/
[GSI]: http://gsi.dit.upm.es
[scrapy]: http://scrapy.org/
