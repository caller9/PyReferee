#~ Created by caller9.com as part of the PyReferee application
#~ This houses all of the connection management
#~ Creates IRC_Channel objects and joins them. Parses raw messages from server and routes
#~ Also serves as transmission gateway. 
#~ This thread will die with unhandled exceptions or connection errors. Parent object must reconnect.
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

import threading, logging, logging.handlers, sys
import socket
import IRC_Channel

class IRC_Connection(threading.Thread):  
  def __init__(self, server_name, port, nick, realname, nickserv_command, channel_csv, logging_level,
    log_size, log_max, reconnect_wait, version):
    
    #Configure thread initialization and set as non daemon (default)
    threading.Thread.__init__(self)    
    self.daemon = False
    
    #Configure Local IRC variables
    self.IRC_socket = socket.socket()
    self.server_name = server_name
    self.port = port
    self.nick = nick
    self.realname = realname
    self.nickserv_command = nickserv_command
    self.reconnect_wait = reconnect_wait
    self.version = version
    
    #Create channel handlers for multiple channels
    channel_list = channel_csv.strip().split(',')        
    self.channel_dict = dict()
    for channel in channel_list:      
      self.channel_dict[channel] = IRC_Channel.IRC_Channel(self, self.server_name, channel,
        logging_level, log_size, log_max)
    
    #Configure logging
    self.logger = logging.getLogger(server_name)
    self.logger.setLevel(logging_level)
    handler = logging.handlers.RotatingFileHandler('log/' + self.server_name + '.log',
      maxBytes = log_size, backupCount = log_max)
    self.logger.addHandler(handler)
     
    
  def shutdown(self):
    self.logger.info ('Disconnecting and Stopping Threads for ' + self.server_name)
    for channel_obj in self.channel_dict.itervalues():
      channel_obj.shutdown()
    self.safe_send('QUIT :Requested Shutdown\n')    
    self.running = False
  
  def connect_to_server(self):
    self.logger.info ('Connecting to ' + self.server_name + ':' + `self.port`)
    self.IRC_socket = socket.socket()
    self.IRC_socket.connect((self.server_name, self.port))
    self.safe_send('NICK ' + self.nick + '\n')
    self.safe_send('USER ' + self.nick + ' ' + self.nick + ' ' + self.server_name + ' :' + self.realname + '\n')
  
  def join_channels(self):
    for channel in self.channel_dict.keys():
      self.logger.info('Joining ' + channel.strip())
      self.safe_send('JOIN ' + channel.strip() + '\n')
  
  def send_nickserv_command(self):
    if (len(self.nickserv_command) > 1):
      self.logger.info("Sending nickserv_command")
      self.safe_send(self.nickserv_command)
    else:
      self.logger.info("Skipping empty nickserv_command")
  
  def safe_send(self,strToSend):
    try:
      self.logger.debug("SENDING: " + strToSend.rstrip())
      self.IRC_socket.sendall(strToSend)
    except socket.error, (value,message):
      self.logger.error("socket.sendall - Error: " + message)
    except:
      self.logger.error("socket.sendall - Unexpected Error: " + `sys.exc_info()[0]` + `sys.exc_info()[2]`)

  def parse_message(self,line):
    line=line.rstrip()
    split_line = line.split()
   
    if (split_line[1] == 'PRIVMSG'):
      #Message from user or channel
      
      #Match channel in list of joined channels and parse              
      if self.channel_dict.has_key(split_line[2]):
        self.channel_dict[split_line[2]].parse_message(line)
      elif split_line[3] == ':\001VERSION\001':
	#CTCP Version request
        ctcp_version_source_nick = split_line[0][1:].split('!~')[0] 
        version_reply = 'NOTICE '
        version_reply += ctcp_version_source_nick
        version_reply += ' :\001VERSION PyReferee ' + self.version + ' \001\n'
        self.logger.info('Replied to CTCP Version request from ' + ctcp_version_source_nick)
        self.safe_send(version_reply)
      else:
        #Private message, no/invalid channel context
        self.logger.debug("Ignored PM: "+line)
    else:        
      self.logger.debug(line)
      
      #Welcome message, ready to join channels
      if (split_line[1] == '001'):
        self.send_nickserv_command()
        self.join_channels()        
      
      #Client timeout ping response
      if (split_line[0] == 'PING'):
        self.safe_send('PONG '+split_line[1]+'\n') 
      
  def get_nick(self):
    return self.nick
  
  def get_reconnect_wait(self):
    return self.reconnect_wait
    
  def get_server_name(self):
    return self.server_name

  def reset_thread(self):
    threading.Thread.__init__(self)

  def run(self):    
    self.connect_to_server()    
    self.running = True
    while self.running:      
      line=self.IRC_socket.recv(4096) #recieve server messages up to 4KB
      if not line:
        self.running = False
      else:
        self.parse_message(line)        
      
    #Something has broken or exit requested, close socket and end thread
    self.IRC_socket.close()

if __name__ == '__main__':
  IRC = IRC_Connection('localhost',6667,'justatest','Fake Name','foo','#faketest',logging.DEBUG,20480,5)
  IRC.parse_message('PING :calvino.freenode.net')
