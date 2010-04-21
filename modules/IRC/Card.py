#~ Created by caller9.com as part of the PyReferee application
#~ Configuration holder object for Cards
#~
#~ Created 2010-04-20
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

class Card:
  def __init__(self):
    self.message = ''
    self.action = ''
    self.revoke = ''
    self.duration = 0
    self.limit = 0
    self.max_age = 0
    