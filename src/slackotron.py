#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2016.

  http://www.lettier.com/

  Slackotron
'''

import sys
import time
import traceback
import logging
import json
import slackotron_settings
import decorators
from lib.scribe import Scribe
from lib.locker import Locker
from models import Base
from lib.slack import Slack
from database.database_manager import DatabaseManager
from plugins.plugin_manager import PluginManager
from channel_user_manager import ChannelUserManager
from dashboard.dashboard_manager import DashboardManager

logging.basicConfig(level=logging.WARNING)


class Slackotron(Scribe, object):
  '''
    Slackotron(Scribe, object)
  '''
  bot_slack_id = slackotron_settings.BOT_SLACK_ID
  bot_slack_name = slackotron_settings.BOT_SLACK_NAME
  bot_icon_url = slackotron_settings.BOT_ICON_URL
  bot_icon_emoji = slackotron_settings.BOT_ICON_EMOJI
  try:
    profanity_filter_on = slackotron_settings.PROFANITY_FILTER_ON
    if profanity_filter_on is not False or profanity_filter_on is not True:
      profanity_filter_on = True
  except Exception:
    profanity_filter_on = True
  slack = Slack()
  database_manager = DatabaseManager()
  locker = Locker()
  channel_user_manager = ChannelUserManager(
      **{
          'slack': slack,
          'database_manager': database_manager,
          'profanity_filter_on': profanity_filter_on,
          'bot_slack_id': bot_slack_id,
          'bot_slack_name': bot_slack_name,
          'bot_icon_emoji': bot_icon_emoji,
          'bot_icon_url': bot_icon_url
      }
  )
  plugin_manager = PluginManager(
      **{
          'slack': slack
      }
  )
  dashboard_manager = DashboardManager()

  def __init__(self):
    self.exit = False
    self.info('Slackotron bot Slack name: %s' % self.bot_slack_name)

  def start(self):
    '''
      start()
    '''
    if not self.slack.api_valid() or not self.slack.auth_valid():
      self.critical('Slack API and/or auth not valid! Exiting.')
      sys.exit()
    self.locker.unlock_all()
    self.database_manager.connect()
    self.database_manager.create_tables(Base)
    self.channel_user_manager.start()
    self.plugin_manager.start()
    self.dashboard_manager.start()
    self._run()

  def stop(self):
    '''
      stop()
    '''
    self.dashboard_manager.stop()
    self.plugin_manager.stop()
    self.channel_user_manager.stop()
    self.database_manager.disconnect()
    self.locker.unlock_all()
    time.sleep(5)
    self.info(self.__class__.__name__ + ' stopped.')

  @decorators.rabbitmq_subscribe(
      host=slackotron_settings.RABBITMQ_HOST_URL
  )
  def _on_rmq_message(self, *_, **kwargs):
    '''
      _on_rmq_message(*args, **kwargs)
    '''
    try:
      rmq_message = kwargs.get('rmq_message', '{}') or '{}'
      rmq_message = json.loads(rmq_message)
      self.exit = rmq_message.get('exit', False) or False
    except Exception as error:
      self.error(error)
    return None

  def _run(self):
    '''
      _run()
    '''
    while not self.exit:
      try:
        self._on_rmq_message()
      except Exception as error:
        self.error(error)
        traceback.print_exc()
        continue

if __name__ == '__main__' and __package__ is None:
  SLACKOTRON = Slackotron()
  try:
    SLACKOTRON.start()
  except KeyboardInterrupt:
    pass
  SLACKOTRON.stop()
  print('\nBye.')
