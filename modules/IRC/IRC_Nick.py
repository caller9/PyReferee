#~ Created by caller9.com as part of the PyReferee application
#~ This houses all of the nick information
#~ IRC_Channel will call parse_message(message) to enqueue into self.messages
#~
#~ Created 2010-04-18
#~ Modified 2010-04-19

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
    
    self.yellow_cards = deque()      
    self.red_cards = deque()    
    self.messages = deque()

  def clean_message_queue(self):
    #Restrict message buffer to 50
    while (len(self.messages) > 50):
      self.messages.popleft()
  
  def clean_card_queues(self, yellow_card_max_age, red_card_max_age):
    #Remove any cards that are outside of the sliding window max_age
    
    start_time = datetime.datetime.utcnow()
    while ((len(self.yellow_cards) > 0) and
      ((start_time - self.yellow_cards[0]).days > yellow_card_max_age)):
      self.yellow_cards.popleft()
    
    while ((len(self.red_cards) > 0) and
      ((start_time - self.red_cards[0]).days > red_card_max_age)):
      self.red_cards.popleft()
  
  def format_counters(self, yellow_card_limit, red_card_limit):
    format_string = 'yellow (' + `len(self.yellow_cards)` + ' / ' 
    format_string += `yellow_card_limit` + ') red ('
    format_string += `len(self.red_cards)` + ' / ' + `red_card_limit` + ')'
    return format_string
  
  def parse_message (self, message):
    self.parent.logger.debug (self.nick + ' : ' + message)
    self.messages.append((datetime.datetime.utcnow(),message))    
    self.clean_message_queue()
    
  def get_nick (self):
    return self.nick
  
  def get_is_admin (self):
    return self.is_admin
  
  def get_messages (self):
    return self.messages
  
  def add_yellow (self):
    self.yellow_cards.append(datetime.datetime.utcnow())
  
  def get_yellow_count (self):
    return len(self.yellow_cards)
  
  def clear_yellow (self):
    self.yellow_cards.clear()
    
  def add_red (self):
    self.red_cards.append(datetime.datetime.utcnow())
  
  def get_red_count (self):
    return len(self.red_cards)
  
  def clear_red (self):
    self.red_cards.clear()