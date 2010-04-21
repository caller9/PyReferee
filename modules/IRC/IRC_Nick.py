#~ Created by caller9.com as part of the PyReferee application
#~ This houses all of the nick information
#~ IRC_Channel will call parse_message(message) to enqueue into self.messages
#~
#~ Created 2010-04-18
#~ Modified 2010-04-20

#~ This program is free software; you can redistribute it and/or modify
#~ it under the terms of the GNU General Public License as published by
#~ the Free Software Foundation; version 2 of the License.
#~ 
#~ This program is distributed in the hope that it will be useful,
#~ but WITHOUT ANY WARRANTY; without even the implied warranty of
#~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#~ GNU General Public License for more details.

import datetime
from collections import deque

class IRC_Nick:
  def __init__ (self, parent, nick, full_nick, nick_is_admin):
    self.parent = parent
    
    self.nick = nick
    self.full_nick = full_nick
    self.is_admin = nick_is_admin
    self.instantiated = datetime.datetime.utcnow()
    
    #Dictionary keyed by card (color string) containing a deque of timestamps 
    #Timestamps represent when the penalty was given and are used for aging cards
    self.penalty_dict = dict()
    
    self.messages = deque()

  def clean_message_queue(self):
    #Restrict message buffer to 50
    while (len(self.messages) > 50):
      self.messages.popleft()
  
  def clean_penalty_queues(self, card_dict):
    #Remove any penalty cards that are outside of the sliding window max_age
    
    start_time = datetime.datetime.utcnow()    
    
    for card in self.penalty_dict.keys():
      penalty_obj = self.penalty_dict[card]
      while ((len(penalty_obj) > 0) and
        ((start_time - penalty_obj[0]).days > card_dict[card].max_age)):
        penalty_obj.popleft()
      
  def format_counters(self, card_dict):
    #Return a formatted string with card totals for this nick
    format_string = ''
    
    for card in card_dict.keys():
      format_string += card + ' (' + `self.get_penalty_count(card)` + ' / ' 
      format_string += `card_dict[card].limit` + ') '
    
    return format_string
  
  def parse_message (self, message):
    #Store message with timestamp as tuple in queue
    self.parent.logger.debug (self.nick + ' : ' + message)
    self.messages.append((datetime.datetime.utcnow(),message))    
    self.clean_message_queue()
    
  def get_nick (self):
    return self.nick
  
  def get_is_admin (self):
    return self.is_admin
  
  def get_messages (self):
    return self.messages
  
  def add_penalty (self, card):
    #Create penalty queue if required for card color, add an entry timestamp
    if not self.penalty_dict.has_key(card):
      self.penalty_dict[card] = deque()
    self.penalty_dict[card].append(datetime.datetime.utcnow())
  
  def get_penalty_count (self, card):
    #If this color has accumulated cards, add to the counter
    if self.penalty_dict.has_key(card):
      return len(self.penalty_dict[card])
    return 0
  
  def clear_penalty (self, card):
    #Reset the penalties for this card color
    if self.penalty_dict.has_key(card):
      self.penalty_dict[card].clear()
  