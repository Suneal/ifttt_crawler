# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class RecipeItem(Item):
    """ Class that represents a Recipe according to Ifttt definition. 
        All fields included can be populated using information scrapped
        from ifttt's website. """
        
    id = Field()
    title = Field()
    description = Field()
    url = Field()
    event = Field()
    event_channel = Field()
    action = Field()
    action_channel = Field()
    created_by = Field()
    times_used = Field()
    created_at = Field()

class ChannelItem(Item):
    """ Class that represents a Channel according to Ifttt definition.
        All fields included can be populated using information scrapped
        from ifttt's website. """
    
    id = Field() # Not a number a unique string
    title = Field()
    description = Field()
    events_generated = Field()
    actions_provided = Field()
    commercial_url = Field()

class EventItem(Item):
    
    pass

class ActionItem(Item):
    
    pass
    
class InputParameterItem(Item):
    id = Field()  # Not a number but a unique string
    title = Field()
    description = Field() # Notes + data example
    
class OutputParameterItem(Item):
    id = Field()  # Not a number but a unique string
    title = Field()
    description = Field() # Notes + data example
    
        
     