#~ Created by caller9.com as part of the PyReferee application
#~ This houses all of the enforcement operations and configuration
#~ IRC_Channel calls send_card_level to escalate through penalties for a nick
#~
#~ Created 2010-04-19
#~ Modified 2010-04-20

#~ This program is free software; you can redistribute it and/or modify
#~ it under the terms of the GNU General Public License as published by
#~ the Free Software Foundation; version 2 of the License.
#~ 
#~ This program is distributed in the hope that it will be useful,
#~ but WITHOUT ANY WARRANTY; without even the implied warranty of
#~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#~ GNU General Public License for more details.

import threading
import Card

class IRC_Enforcer:
  def __init__(self,parent,config):
    self.timer_dict = dict()
    self.parent = parent
    
    self.card_list = []
    self.card_dict = dict()
    
    self.load_config (config)
      
  def shutdown (self):
    #Kill any pending timers
    for timer in self.timer_dict.itervalues():
      timer.cancel()
  
  def parse_command(self, nick_obj, command):
    if (command == 'cards'):
      self.parent.channel_send(nick_obj.get_nick() + ': ' + nick_obj.format_counters(self.card_dict))
      
    if (nick_obj.get_is_admin()):
      command_split = command.split()
      
      if (len(command_split) > 1):
        tmp_nick_obj = self.parent.get_nick_obj(command_split[1])
        if not tmp_nick_obj:
          self.parent.channel_send(nick_obj.get_nick() + ': ' + command_split[1] + ' has not spoken since startup.')
          return
      
        if (command_split[0] == 'clear_penalty') and (len(command_split) == 3):
          tmp_nick_obj.clear_penalty(command_split[2])
          self.parent.channel_send(nick_obj.get_nick() + ': Cleared ' + command_split[2] + ' cards for ' + command_split[1])
        
        if (command_split[0] == 'cards') and (len(command_split) == 2):
          self.parent.channel_send(nick_obj.get_nick() + ': ' + command_split[1] + ' : ' + tmp_nick_obj.format_counters(self.card_dict))
        
  
  def fill_template(self, template, variables):
    #Replace strings in template with nested tuples from variables
    #e.g. template = "Hey $nick you are banned : $reason." 
    #variables = (("$nick","JohnDoe"),("$reason","you know why"))
    #would return "Hey JohnDoe you are banned : you know why."
    for item in variables:
      template = template.replace(item[0],item[1])
    return template
  
  def kill_timer(self, nick):
    #Kill a revoke timer and nuke the thread
    if self.timer_dict.has_key(nick):
      self.timer_dict[nick].cancel()
      del self.timer_dict[nick]
 
  def enforce_in_progress (self, nick_obj):
    #Check to see if a revoke timer is waiting.
    return self.timer_dict.has_key(nick_obj.get_nick())
  
  def send_card_level (self, channel, nick_obj, reason, level):
    #Determine if the user has gone over the limit for the card color at this level
    #Escalate to next level if possible or issue send_card enforcement command
    
    #Infinite loop stopper
    recursion_ok = True
    
    #Limit and recursion safety valve. Negative level means maximum level
    if (level > len(self.card_list)) or (level < 0):
      level = len(self.card_list) - 1
      recursion_ok = False
    
    #Check that enforcement is not already in progress
    if self.enforce_in_progress(nick_obj):
      return
    
    card = self.card_list[level]
    
    nick_obj.clean_penalty_queues(self.card_dict)
    nick_obj.add_penalty(card)
    
    if (recursion_ok) and (self.card_dict[card].limit > 0) and (nick_obj.get_penalty_count(card) > self.card_dict[card].limit):
      #If Over Limit recursively escalate
      reason += 'Exceeded ' + card + ' card limit. '
      nick_obj.clear_penalty(card)
      self.send_card_level (channel, nick_obj, reason, level + 1)
    else:
      #If Under Limit, enforce this penalty
      self.send_card (channel, nick_obj, reason, card)
  
  def send_card (self, channel, nick_obj, reason, card):
    #Perform actual enforcment actions and optionally schedule revoke
    
    #Exclude admins
    if (nick_obj.get_is_admin()):
      self.parent.logger.info('Skipping ' + card + ' card for ' + nick_obj.get_nick() + ' (admin)')
      return
    
    #Check that enforcement is not already in progress
    if self.enforce_in_progress(nick_obj):
      return
        
    self.parent.logger.info(card + ' card for ' + nick_obj.get_nick() + ' : ' + reason)
    
    card_obj = self.card_dict[card]
    
    reason += 'Card Count: ' + nick_obj.format_counters(self.card_dict) + ' '
    
    #Schedule Revocation
    if (card_obj.revoke != '') and (card_obj.duration != 0):
      #Start revocation timer
      reason += 'This will expire in ' + `card_obj.duration` + ' seconds. '
      self.kill_timer(nick_obj.get_nick())
      self.timer_dict[nick_obj.get_nick()] = threading.Timer(card_obj.duration, self.revoke_card, args = [channel, nick_obj, card])
      self.timer_dict[nick_obj.get_nick()].start()
    else:
      reason += 'This will never expire. '
    
    #Send message command
    self.parent.channel_send(self.fill_template(card_obj.message,
        (('$nick',nick_obj.get_nick()),
        ('$reason',reason))
        )
      )
    
    #Send action command
    self.parent.safe_send(self.fill_template(card_obj.action,
        (('$channel',channel),
        ('$nick',nick_obj.get_nick()),
        ('$reason',reason))
        )
        + '\n'
      )   
  
  def revoke_card (self, channel, nick_obj, card):
    self.parent.safe_send(self.fill_template(self.card_dict[card].revoke,
        (('$channel',channel),
        ('$nick',nick_obj.get_nick()))
        )
        + '\n'
      )
    self.kill_timer(nick_obj.get_nick())
  
  def load_config (self, config):
    self.card_list = config.get('cards','card_progression_csv').split(',')
    
    for card in self.card_list:
      self.card_dict[card] = Card.Card()
      self.card_dict[card].message = config.get(card,'message')
      self.card_dict[card].action = config.get(card,'action')
      self.card_dict[card].revoke = config.get(card,'revoke')
      self.card_dict[card].duration = config.getint(card,'duration')
      self.card_dict[card].limit = config.getint(card,'limit')
      self.card_dict[card].max_age = config.getint(card,'max_age')
    