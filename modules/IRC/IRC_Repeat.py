#~ Created by caller9.com as part of the PyReferee application
#~ Catch repeated messages/taunts/bullying
#~
#~ Created 2010-04-
#~ Modified 2010-04-19

#~ This program is free software; you can redistribute it and/or modify
#~ it under the terms of the GNU General Public License as published by
#~ the Free Software Foundation; version 2 of the License.
#~ 
#~ This program is distributed in the hope that it will be useful,
#~ but WITHOUT ANY WARRANTY; without even the implied warranty of
#~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#~ GNU General Public License for more details.

# TODO: Implement checks that the last N messages when split into words have no words that are repeated
#       more than M times. Maybe just keep a dict with a counter for each word(key) and exclude very common
#       words and smileys