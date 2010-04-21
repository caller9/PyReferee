#~ PyReferee
#~ Created by caller9.com 
#~ This will read config/servers.cfg and create connection objects for those servers.
#~ It will also serve as a watchdog and re-launch terminated connection threads if so configured.
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

from modules.IRC.IRC_Connection import IRC_Connection
import ConfigParser
import logging
import time
import threading
import signal

if __name__ == '__main__':
  VERSION_NUMBER = '0.20'

  config = ConfigParser.RawConfigParser()
  
  logging_level = logging.DEBUG
  #logging_level = logging.INFO
  
  #logging.basicConfig(filename='log/pyreferee.log', level=logging_level)
  logging.basicConfig(level=logging_level, format='%(asctime)s %(levelname)s %(message)s')
  
  SERVER_CONFIG_FILE = 'config/servers.cfg'
  
  logging.debug ('Reading configuration from ' + SERVER_CONFIG_FILE)
  config.read(SERVER_CONFIG_FILE)
  
  IRC_Connection_List = []
  
  #Config file can contain multiple servers. Each section will be treated as a server section
  for server in config.sections():
    
    #Skip disabled configurations
    if config.has_option(server,'disabled') and config.getboolean(server,'disabled'):
      logging.info ('Server config [' + server + '] is disabled in ' + SERVER_CONFIG_FILE)
      continue
    
    #Require this list of options in the server section
    vital_options = ['port','server_name','nick','realname','channel_csv','nickserv_command','log_size','log_max','reconnect_wait']
    valid_config = True
    for option in vital_options:
      if not config.has_option(server,option):
        logging.error ('Server config [' + server + '] option "' + option + '" missing from ' + SERVER_CONFIG_FILE)
        valid_config = False
    
    if not valid_config:
      logging.error ('Invalid configuration [' + server + '].')
      continue
    
    #Instantiate IRC connection thread and start it
    IRC = IRC_Connection(config.get(server,'server_name'),
      config.getint(server,'port'),
      config.get(server,'nick'),
      config.get(server,'realname'),
      config.get(server,'nickserv_command'),
      config.get(server,'channel_csv'),
      logging_level,
      config.getint(server,'log_size'),
      config.getint(server,'log_max'),
      config.getint(server,'reconnect_wait'),
      VERSION_NUMBER
      )
    IRC.start()
    
    #Add to list of IRC connection threads
    IRC_Connection_List.append(IRC)
  
  #Main Loop app_running is set false by SystemExit or KeyboardInterrupt exceptions or 
  #all threads being stopped with none waiting on a restart
  app_running = True
  
  logging.info ('PyReferee Bot v' + VERSION_NUMBER + ' running... CTRL+C to shutdown')
  
  while (app_running):
    try:        
      #Check that all connection threads are running, restart if needed
      already_slept = 0
      for IRC in IRC_Connection_List:
        if (not IRC.isAlive() and (IRC.get_reconnect_wait() > 0)):
          logging.warning ('Thread ' + IRC.get_server_name() 
            + ' died. Restarting in ' + `IRC.get_reconnect_wait()` + ' seconds.')
          
          #Rather than deal with threading.Timer here for multiple dead threads, just start the
          #threads sequentially and wait for the IRC.reconnect_wait interval less any time
          #that has already been waited in this pass through the IRC_Connection_List          
          sleep_diff = IRC.get_reconnect_wait() - already_slept
          if (sleep_diff > 0):
            time.sleep(sleep_diff)
            already_slept += sleep_diff
            
          IRC.reset_thread()
          IRC.start()
      
      #If there are no more connection threads running, exit
      if (len(threading.enumerate()) == 1):
        logging.info('All connection threads have died with no reconnect_wait set.')
        app_running = False
      
      #Keep this loop from eating many resources
      time.sleep(5)
      
    except (KeyboardInterrupt, SystemExit):
      #Exit the application, first tell all of the connection threads to shutdown
      for IRC in IRC_Connection_List:
        IRC.shutdown()
      app_running = False
  
  #Wait until threads exit. Otherwise "zombie" threads keep interpreter running 
  #with nothing to properly listen for KeyboardInterrupt or signals
  logging.info ('Waiting for threads to close... CTRL+C to abort')
  while (len(threading.enumerate()) > 1):
    logging.debug ('Waiting on ' + `threading.enumerate()`)
    time.sleep(5)
  
  logging.info ('Clean Shutdown Completed')
