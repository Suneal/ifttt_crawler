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
    times_favorite = Field()
    featured = Field()
    created_at = Field()
    supported_by = Field()
    
    def __str__(self, *args, **kwargs):
        return str(self.get('title', 'NoTitle'))

class ChannelItem(Item):
    ''' Class that represents a Channel according to Ifttt definition.
        All fields included can be populated using information scrapped
        from ifttt's website. 
    '''
    template = 'channel'
    # Fields    
    id = Field()  # Not a number a unique string
    title = Field()
    description = Field()
    commercial_url = Field()
    logo = Field()
    category = Field()
    events_generated = Field()
    actions_provided = Field()

    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))

class EventItem(Item):
    '''
    '''
    # Fields
    template = 'event'
    id = Field()
    title = Field()
    description = Field()
    see_also = Field()
    input_parameters = Field()
    output_parameters = Field()
    
    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))

class ActionItem(Item):
    '''
    '''
    # Fields
    template = 'action'
    id = Field()
    title = Field()
    description = Field()
    see_also = Field()
    input_parameters = Field()
    
    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))
    
class InputParameterItem(Item):
    '''
    '''
    # Fields
    id = Field()
    title = Field()
    description = Field()
    type = Field()
    see_also = Field()
    
    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))
    
class OutputParameterItem(Item):
    '''
    '''
    # Fields
    id = Field()
    title = Field()
    description = Field()  # Name + Notes
    example = Field()
    see_also = Field()

    def __str__(self, *args, **kwargs):
        return str(self.get('title', ''))
