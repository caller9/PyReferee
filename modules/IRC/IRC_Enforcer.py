#~ Created by caller9.com as part of the PyReferee application
#~ This houses all of the enforcement operations and configuration
#~ IRC_Channel will proxy the enforcement functions [[yellow|red]_card|permaban] (channel, nick_obj, reason)
#~
#~ Created 2010-04-19
#~ Modified 2010-04-19

#~ This program is free software; you can redistribute it and/or modify
#~ it under the terms of the GNU General Public License as published by
#~ the Free Software Foundation; version 2 of the License.
#~ 
#~ This program is distributed in the hope that it will be useful,
#~ but WITHOUT ANY WARRANTY; without even the implied warranty of
#~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#~ GNU General Public License for more details.

import threading

class IRC_Enforcer:
  def __init__(self,parent,config):
    self.timer_dict = dict()
    self.parent = parent
    
    self.yellow_card_message = config.get('yellow_card','message')
    self.yellow_card_action = config.get('yellow_card','action')
    self.yellow_card_revoke = config.get('yellow_card','revoke')
    self.yellow_card_duration = config.getint('yellow_card','duration')
    self.yellow_card_limit = config.getint('yellow_card','limit')
    self.yellow_card_max_age = config.getint('yellow_card','max_age')
        
    self.red_card_message = config.get('red_card','message')
    self.red_card_action = config.get('red_card','action')
    self.red_card_revoke = config.get('red_card','revoke')
    self.red_card_duration = config.getint('red_card','duration')
    self.red_card_limit = config.getint('red_card','limit')
    self.red_card_max_age = config.getint('red_card','max_age')
        
    self.permaban_message = config.get('permaban','message')
    self.permaban_action = config.get('permaban','action')
  
  def shutdown (self):
    for timer in self.timer_dict.itervalues():
      timer.cancel()
  
  def parse_command(self, nick_obj, command):
    if (command == 'cards'):
      self.parent.channel_send(nick_obj.get_nick() + ': ' + nick_obj.format_counters(self.yellow_card_limit,self.red_card_limit))
  
  def fill_template(self, template, variables):
    #Replace strings in template with nested tuples from variables
    #e.g. template = "Hey $nick you are banned : $reason." 
    #variables = (("$nick","JohnDoe"),("$reason","you know why"))
    #would return "Hey JohnDoe you are banned : you know why."
    for item in variables:
      template = template.replace(item[0],item[1])
    return template
  
  def kill_timer(self, nick):
    if self.timer_dict.has_key(nick):
      self.timer_dict[nick].cancel()
      del self.timer_dict[nick]
  
  def yellow_card(self, channel, nick_obj, reason):
    #Nick has earned a yellow card
    
    #Exclude admins
    if (nick_obj.get_is_admin()):
      self.parent.logger.info('Skipping Yellow Card for ' + nick_obj.get_nick() + ' (admin)')
      return
    
    #Check that enforcement is not already in progress
    if (self.timer_dict.has_key(nick_obj.get_nick())):
      return
    
    nick_obj.clean_card_queues(self.yellow_card_max_age, self.red_card_max_age)
    nick_obj.add_yellow()
    
    if (nick_obj.get_yellow_count() > self.yellow_card_limit):        
      nick_obj.clear_yellow()
      self.red_card(channel, nick_obj, reason)
    else:
      #Yellow Card        
      self.parent.logger.info('Yellow Card for ' + nick_obj.get_nick() + ' for ' + reason)
      
      #Expand reason
      reason += 'Current count: ' + nick_obj.format_counters(self.yellow_card_limit,self.red_card_limit) + '. '      
      reason += 'Expires in ' + `self.yellow_card_duration` + ' seconds.'        
      
      #Start revocation timer
      self.kill_timer(nick_obj.get_nick())
      self.timer_dict[nick_obj.get_nick()] = threading.Timer(self.yellow_card_duration, self.revoke_yellow, args = [channel, nick_obj])
      self.timer_dict[nick_obj.get_nick()].start()
      
      #Send message command
      self.parent.channel_send(self.fill_template(self.yellow_card_message,
          (('$nick',nick_obj.get_nick()),
          ('$reason',reason))
          )
        )
      
      #Send action command
      self.parent.safe_send(self.fill_template(self.yellow_card_action,
          (('$channel',channel),
          ('$nick',nick_obj.get_nick()),
          ('$reason',reason))
          )
          + '\n'
        )
      
  
  def revoke_yellow(self, channel, nick_obj):
    self.parent.safe_send(self.fill_template(self.yellow_card_revoke,
        (('$channel',channel),
        ('$nick',nick_obj.get_nick()))
        )
        + '\n'
      )
    self.kill_timer(nick_obj.get_nick())

  def red_card(self, channel, nick_obj, reason):
    #Nick has earned a red card
    
    #Exclude admins
    if (nick_obj.get_is_admin()):
      self.parent.logger.info('Skipping Red Card for ' + nick_obj.get_nick() + ' (admin)')
      return
    
    #Check that enforcement is not already in progress
    if (self.timer_dict.has_key(nick_obj.get_nick())):
      return
        
    nick_obj.clean_card_queues(self.yellow_card_max_age, self.red_card_max_age)
    nick_obj.add_red()
      
    if (nick_obj.get_red_count() > self.red_card_limit):      
      self.permaban(channel, nick_obj, reason)
          
    else:
      #Red Card
      self.parent.logger.info('Red Card for ' + nick_obj.get_nick() + ' for ' + reason)
      
      #Expand Reason
      reason += 'More than ' + `self.yellow_card_limit` + ' yellow cards in ' + `self.yellow_card_max_age` + ' days. '
      reason += 'Current count: ' + nick_obj.format_counters(self.yellow_card_limit,self.red_card_limit) + '. '      
      reason += 'Expires in ' + `self.red_card_duration / 3600` + ' hours.'        
      
      #Start revocation timer
      self.kill_timer(nick_obj.get_nick())
      self.timer_dict[nick_obj.get_nick()] = threading.Timer(self.red_card_duration, self.revoke_red, args = [channel, nick_obj])
      self.timer_dict[nick_obj.get_nick()].start()  
      
      #Send message command
      self.parent.channel_send(self.fill_template(self.red_card_message,
            (('$nick',nick_obj.get_nick()),
            ('$reason',reason))
            )
          )
      
      #Send action command
      self.parent.safe_send(self.fill_template(self.red_card_action,
          (('$channel',channel),
          ('$nick',nick_obj.get_nick()),
          ('$reason',reason))
          )
          + '\n'
        )
      
  
  def revoke_red(self, channel, nick_obj):    
    self.parent.safe_send(self.fill_template(self.red_card_revoke,
        (('$channel',channel),
        ('$nick',nick_obj.get_nick()))
        )
        + '\n'
      )
    self.kill_timer(nick_obj.get_nick())
    
  def permaban(self, channel, nick_obj, reason):
    #Exclude admins
    if (nick_obj.get_is_admin()):
      self.parent.logger.info('Skipping Permaban for ' + nick_obj.get_nick() + ' (admin)')
      return
    
    #Permaban requires OP to manually reverse so no revocation timer
    self.parent.logger.info('Permaban for ' + nick_obj.get_nick() + ' for ' + reason)
    
    reason += 'More than ' + `self.red_card_limit` + ' red cards in ' + `self.red_card_max_age` + ' days. '
    
    #Send message command
    self.parent.channel_send(self.fill_template(self.permaban_message,
        (('$nick',nick_obj.get_nick()),
        ('$reason',reason))
        )
      )
    
    #Send action command
    self.parent.safe_send(self.fill_template(self.permaban_action,
        (('$channel',channel),
        ('$nick',nick_obj.get_nick()),
        ('$reason',reason))
        )
        + '\n'
      )
  
  
    