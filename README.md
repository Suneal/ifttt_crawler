[Ewe-Scrappers](http://gsi.dit.upm.es) 
==================================

Introduction
---------------------

This project scrapes information from the major Task Automation Services (for now ifttt and Zapier are supported) in a semantic format. The extracted data is modelled using the Evented WEb ontology ([EWE]) developed by the Intelligent Systems Group ([GSI]). For this purpose the [scrapy] framework is used.  

The EWE ontology models Channels (called apps in Zapier) and Rules (Ifttt's recipes and Zapier's zapps). The data described using EWE may be loaded in a semantic endpoint to be consulted using SPARQL. Although particular exporters are provided to support EWE's format, the data may also be exported using the built-in exporters of scrapy (csv, json, etc.)

Documentation
----------------------

Detailed documentation may be found at the Wiki page of this proyect ([Wiki] (./wiki) ).

### Contact

For more information, contact us through: http://gsi.dit.upm.es

![GSI Logo](http://gsi.dit.upm.es/templates/jgsi/images/logo.png)

[EWE]: http://www.gsi.dit.upm.es/ontologies/ewe/
[GSI]: http://gsi.dit.upm.es
[scrapy]: http://scrapy.org/
