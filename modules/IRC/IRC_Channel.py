#~ Created by caller9.com as part of the PyReferee application
#~ This houses all of the channel specific operations and configuration
#~ IRC_Connection will call parse_message of this function for all channel 
#~ specific messages.
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


import logging, logging.handlers
import ConfigParser
import os.path
import IRC_Nick, IRC_Flood, IRC_Enforcer, IRC_Admin

class IRC_Channel:
  def __init__(self, parent, server_name, channel_name, logging_level, log_size, log_max):
    self.parent = parent
    
    self.server_name = server_name
    self.channel_name = channel_name
    self.nick_dict = dict()
    
    #Configure logging
    self.logger = logging.getLogger(server_name + channel_name)
    self.logger.setLevel(logging_level)
    handler = logging.handlers.RotatingFileHandler(
      'log/' + self.server_name + channel_name + '.log',
      maxBytes = log_size, 
      backupCount = log_max
      )
    self.logger.addHandler(handler)
    
    #Load configuration file or use default_channel.cfg
    self.channel_config_file = 'config/' + self.server_name + self.channel_name + '.cfg'
    self.config = ConfigParser.RawConfigParser()
    self.loadConfig()
    
    #Create Child Objects
    self.command_parser_list = []    
    self.enforcer = IRC_Enforcer.IRC_Enforcer(self,self.config)
    self.command_parser_list.append(self.enforcer)
    
    self.parser_list = []
    self.parser_list.append(IRC_Flood.IRC_Flood(self,self.config))
    
    self.admin = IRC_Admin.IRC_Admin(self.config)
    
  def shutdown(self):
    self.enforcer.shutdown()
  
  def parse_message(self, line):    
    self.logger.debug(line)
    line_split = line.split()
    
    #Extract source nick from ':nick!~nick@host' format
    full_nick = line_split[0][1:]
    nick = full_nick.split('!')[0]
    
    #Check for administrative user
    nick_is_admin = self.admin.check_admin(full_nick)
    
    #Extract message
    message = ' '.join(line_split[3:]).lstrip(':')
    
    #Add nick to dictionary of nick objects if needed
    if not self.nick_dict.has_key(nick):      
      self.nick_dict[nick] = IRC_Nick.IRC_Nick(self, nick, full_nick, nick_is_admin)
    
    #Handle parsing operations
    current_nick = self.nick_dict[nick]
    current_nick.parse_message(message)
    
    for parser in self.parser_list:
      parser.parse_message(current_nick,message)
    
    message_split = message.split()
    
    if ((message_split[0].rstrip(':,') == self.parent.get_nick()) and (len(message_split) > 1)):
      #This is addressed to the bot parse as command.
      command = ' '.join(message_split[1:])
      
      for parser in self.command_parser_list:
        parser.parse_command(current_nick, command)
  
  def channel_send(self, message):
    self.safe_send ('PRIVMSG ' + self.channel_name + ' :' + message + '\n')
  
  def safe_send(self, line):
    self.parent.safe_send(line)
  
  def yellow_card(self, nick_obj, reason):
    self.enforcer.yellow_card(self.channel_name, nick_obj, reason)
  
  def red_card(self, nick_obj, reason):
    self.enforcer.yellow_card(self.channel_name, nick_obj, reason)
  
  def permaban(self, nick_obj, reason):
    self.enforcer.yellow_card(self.channel_name, nick_obj, reason)
  
  def loadConfig(self):
    if (os.path.isfile(self.channel_config_file)):
      self.logger.info("Reading configuration " + self.channel_config_file)
      self.config.read(self.channel_config_file)
    else:
      self.config.read('config/default_channel.cfg')
      self.logger.info('Creating configuration ' + self.channel_config_file)
      try:
        configfile = open(self.channel_config_file, 'wb')
        self.config.write(configfile)
      except:
	self.logger.error('Cannot create ' + self.channel_config_file)    
    
