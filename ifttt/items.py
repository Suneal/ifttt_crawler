# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class RecipeItem(Item):
    ''' Class that represents a Recipe according to Ifttt definition. 
        All fields included can be populated using information scrapped
        from ifttt's website. 
    '''
    ewe_class = 'Rule'
    template = 'rule'
    
    # Fields    
    id = Field()
    title = Field()
    description = Field()
    url = Field()  # this should be id
    event = Field()
    event_channel = Field()
    action = Field()
    action_channel = Field()
    created_by = Field()
    times_used = Field()
    created_at = Field()
    supported_by = Field()
    
    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))

class ChannelItem(Item):
    ''' Class that represents a Channel according to Ifttt definition.
        All fields included can be populated using information scrapped
        from ifttt's website. 
    '''
    ewe_class = 'ewe:Channel' 
    template = 'channel'
    
    # Fields    
    id = Field()  # Not a number a unique string
    
    title_label = 'dcterms:title'
    title = Field()
    
    description_label = 'dcterms:description'    
    description = Field()
    
    commercial_url_label = 'foaf:url'
    commercial_url = Field()
    
    logo_label = 'foaf:logo'
    logo = Field()
    
    events_generated_label = 'ewe:generatesEvent'
    events_generated_asAttr = True
    events_generated = Field()
    
    actions_provided_label = 'ewe:hasAction'
    actions_provided_asAttr = True
    actions_provided = Field()

    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))

class EventItem(Item):
    '''
    '''
    ewe_class = 'ewe:Event' 
    
    # Fields
    id = Field()
    
    title_label = 'dcterms:title'
    title = Field()
    
    description_label = 'dcterms:description'
    description = Field()
    
    input_parameters_label = 'ewe:hasInputParameter'
    input_parameters_asAttr = True
    input_parameters = Field()
    
    output_parameters_label = 'ewe:hasOutputParameter'
    output_parameters_asAttr = True
    output_parameters = Field()
    
    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))

class ActionItem(Item):
    '''
    '''
    ewe_class = 'ewe:Action'    
    
    # Fields
    id = Field()
    
    title_label = 'dcterms:title'
    title = Field()
    
    description_label = 'dcterms:description'
    description = Field()
    
    input_parameters_label = 'ewe:hasInputParameter'
    input_parameters_asAttr = True
    input_parameters = Field()
    
    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))
    
class InputParameterItem(Item):
    '''
    '''
    ewe_class = 'ewe:InputParameter' 
    
    # Fields
    title_label = 'dcterms:title'
    title = Field()
    
    description_label = 'dcterms:description'
    description = Field()
    
    type_label = 'xsd:type'
    type = Field()
    
    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))
    
class OutputParameterItem(Item):
    '''
    '''
    ewe_class = 'ewe:OutputParameter' 
    
    # Fields
    title_label = 'dcterms:title'
    title = Field()
    
    description_label = 'dcterms:description'
    description = Field()  # Name + Notes
    
    example_label = 'ewe:example'
    example = Field()

    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))
