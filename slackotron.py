#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import sys
import time
import traceback
import logging
import json
import slackotron_settings
import slack_service
import decorators
from scribe import Scribe
from locker import Locker
from models import Base
from models import Channel
from models import User
from models import Message
from models import Response
from database.database_manager import DatabaseManager
from plugins.plugin_manager import PluginManager
from channel_user_manager import ChannelUserManager
from dashboard.dashboard_manager import DashboardManager

logging.basicConfig(level=logging.WARNING)


class Slackotron(Scribe, object):
  bot_name = slackotron_settings.BOT_NAME
  bot_icon_url = slackotron_settings.BOT_ICON_URL
  bot_icon_emoji = slackotron_settings.BOT_ICON_EMOJI
  bot_slack_id = slackotron_settings.BOT_SLACK_ID
  try:
    profanity_filter_on = slackotron_settings.PROFANITY_FILTER_ON
    if profanity_filter_on is not False or profanity_filter_on is not True:
      profanity_filter_on = True
  except:
    profanity_filter_on = True
  database_manager = DatabaseManager()
  locker = Locker()
  slack = slack_service.Slack()
  channel_user_manager = ChannelUserManager(
      **{
          'database_manager': database_manager,
          'slack': slack,
          'profanity_filter_on': profanity_filter_on,
          'bot_name': bot_name,
          'bot_slack_id': bot_slack_id,
          'bot_icon_emoji': bot_icon_emoji,
          'bot_icon_url': bot_icon_url
      }
  )
  plugin_manager = PluginManager()
  dashboard_manager = DashboardManager()

  def __init__(self):
    self.info('Slackotron Bot Name: %s' % self.bot_name)

  def start(self):
    if not self.slack.api_valid() or not self.slack.auth_valid():
      self.critical('API and/or auth not valid! Exiting.')
      sys.exit()
    self.database_manager.connect()
    self.database_manager.create_tables(Base)
    self.channel_user_manager.start()
    self.plugin_manager.start()
    self.dashboard_manager.start_dashboard()
    self._run()

  def stop(self):
    self.locker.unlock_all()
    self.plugin_manager.stop()
    self.channel_user_manager.stop()
    self.dashboard_manager.stop_dashboard()
    self.database_manager.disconnect()
    time.sleep(5)
    self.info(self.__class__.__name__ + ' is closing.')

  @decorators.rabbitmq_subscribe(
      host=slackotron_settings.RABBITMQ_HOST_URL,
      exchange=slackotron_settings.MAIN_RABBITMQ_EXCHANGE_NAME,
      exchange_type='direct',
      queue=slackotron_settings.MAIN_RABBITMQ_QUEUE_NAME,
      routing_key=slackotron_settings.MAIN_RABBITMQ_ROUTING_KEY
  )
  def _on_rmq_message(self, *args, **kwargs):
    if 'rmq_message' in kwargs:
      rmq_message = kwargs['rmq_message']
    else:
      return
    if rmq_message is not None:
      channel, user, message, plugin_name, plugin_response = \
          self._process_rmq_message(rmq_message)
      if channel is not None:
        if channel.is_subscribed is True:
          if user is not None:
            if message is not None:
              if plugin_name is not None:
                if plugin_response is not None:
                  is_approved = True if channel.is_secure is False \
                      else False
                  response = Response(
                      text=plugin_response,
                      from_plugin=plugin_name,
                      in_response_to=message,
                      to_channel=channel,
                      to_user=user,
                      is_approved=is_approved,
                      is_sent=False,
                  )
                  g = self.locker.make_lock_generator('response')
                  try:
                    g.next()
                    response.save()
                  except Exception as e:
                    self.error(e)
                  finally:
                    g.next()

  def _process_rmq_message(self, rmq_message):
    try:
      rmq_message = json.loads(rmq_message)
      channel = Channel.get(
          Channel.id == rmq_message['channel_id']
      )
      user = User.get(
          User.id == rmq_message['user_id']
      )
      message = Message.get(
          Message.id == rmq_message['message_id']
      )
      plugin_name = rmq_message['plugin_name']
      plugin_response = rmq_message['plugin_response']
      return channel, user, message, plugin_name, plugin_response
    except Exception as e:
      self.error(e)
      return None, None, None, None, None

  def _run(self):
    while True:
      try:
        self._on_rmq_message()
      except Exception as e:
        self.info('Exception:')
        self.error(e)
        traceback.print_exc()
        continue

if __name__ == '__main__' and __package__ is None:
  slackotron = Slackotron()
  try:
    slackotron.start()
  except KeyboardInterrupt:
    slackotron.stop()
    print('\nBye.')
