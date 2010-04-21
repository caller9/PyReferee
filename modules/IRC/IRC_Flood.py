#~ Created by caller9.com as part of the PyReferee application
#~ This houses flood detection
#~ IRC_Channel will call parse_message (nick_obj, message) message is discarded here
#~ If triggered will call back IRC_Channel.yellow_card(nick,reason)
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

import datetime

class IRC_Flood:
  def __init__(self,parent,config):
    self.parent = parent
    
    self.flood_limit = config.getint('flood','flood_limit')
    self.flood_time = config.getint('flood','flood_time')

  def parse_message (self, nick_obj, message):
    nick_messages = nick_obj.get_messages()
    
    if ((len(nick_messages) > self.flood_limit) and
        ((datetime.datetime.utcnow() - nick_messages[-1 * self.flood_limit][0]).seconds < self.flood_time)):
        #Triggered limit
        reason = 'Sent more than ' + `self.flood_limit` + ' messages in ' + `self.flood_time` + ' seconds. ' 
        self.parent.send_card_level(nick_obj,reason,0)