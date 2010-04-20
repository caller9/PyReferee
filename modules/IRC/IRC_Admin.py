#~ Created by caller9.com as part of the PyReferee application
#~ Determines if user is an admin based on their full nick@host
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

class IRC_Admin:
  def __init__(self,config):
    self.admin_list = []
    
    if not config.has_section('admins'):
      return
    
    admin_options = config.options('admins')
    for option in admin_options:
      self.admin_list.append(config.get('admins',option))
      
  
  def check_admin(self, full_nick):
    if '!~' not in full_nick:
      return False
    
    if full_nick.split('!~')[1] in self.admin_list:
      return True
    
    return False
    