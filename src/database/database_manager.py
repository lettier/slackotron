#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2016.

  http://www.lettier.com/

  Slackotron
'''

import os
import playhouse.berkeleydb
from slackotron_settings import SLACK_API_TOKEN

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE_PATH_NAME = ''.join(
    [MODULE_PATH, '/databases/', SLACK_API_TOKEN, '.db']
)
DATABASE_FILE_PATH_NAME = os.path.normpath(DATABASE_FILE_PATH_NAME)


class DatabaseManager(object):
  '''
    Manages the database.

    DatabaseManager()
  '''

  database = playhouse.berkeleydb.BerkeleyDatabase(
      DATABASE_FILE_PATH_NAME,
      threadlocals=True,
      pragmas=(('journal_mode', 'WAL'), ('busy_timeout', 10000))
  )

  def connect(self):
    '''
      Connects to the database.

      connect()
    '''

    self.database.connect()

  def disconnect(self):
    '''
      Disconnects from the database.

      disconnect()
    '''

    self.database.close()

  def transaction(self):
    '''
      Returns a database transaction.

      transaction()
    '''

    return self.database.transaction()

  def create_tables(self, base):
    '''
      Creates the tables in the database.

      create_tables()
    '''

    self.database.create_tables(base.__subclasses__(), True)
