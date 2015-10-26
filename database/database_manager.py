#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import os
import playhouse.berkeleydb

module_path = os.path.dirname(os.path.abspath(__file__))


class DatabaseManager(object):
  database = playhouse.berkeleydb.BerkeleyDatabase(
      os.path.normpath(
          module_path + '/' + 'slackotron.db',
      ),
      threadlocals=True,
      pragmas=(
          ('journal_mode', 'WAL'),
          ('busy_timeout', 10000)
      )
  )

  def connect(self):
    self.database.connect()

  def disconnect(self):
    self.database.close()

  def transaction(self):
    return self.database.transaction()

  def create_tables(self, base):
    self.database.create_tables(base.__subclasses__(), True)
