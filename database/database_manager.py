#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import os
import playhouse.berkeleydb

BASE_DIR = os.path.dirname(__file__)


class DatabaseManager(object):
  database = playhouse.berkeleydb.BerkeleyDatabase(
      BASE_DIR + '/' + 'slackotron.db',
      threadlocals=True,
      timeout=600.0
  )

  def connect(self):
    self.database.connect()
    self.database.execute_sql('PRAGMA journal_mode=WAL;')

  def disconnect(self):
    self.database.close()

  def transaction(self):
    return self.database.transaction()

  def create_tables(self, base):
    self.database.create_tables(base.__subclasses__(), True)
