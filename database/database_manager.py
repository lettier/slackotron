#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron--An extensible slack bot.
'''

import os
import playhouse.berkeleydb

BASE_DIR = os.path.dirname(__file__)


class DatabaseManager(object):
  db = playhouse.berkeleydb.BerkeleyDatabase(
      BASE_DIR + '/' + 'slackotron.db',
      threadlocals=True,
      timeout=600.0
  )

  def __init__(self):
    pass

  def connect(self):
    self.db.connect()
    self.db.execute_sql('PRAGMA journal_mode=WAL;')

  def disconnect(self):
    self.db.close()

  def create_tables(self, base):
    self.db.create_tables(base.__subclasses__(), True)
