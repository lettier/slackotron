#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron--An extensible slack bot.
'''

import sys
import time
import traceback
import logging
import json
import slackotron_settings
import slack_service
import thread_manager
import plugins.plugin_manager
import database.database_manager
import dashboard.dashboard_manager
import decorators
from scribe import Scribe
from models import Base
from models import Channel
from models import User
from models import Message
from models import Response
from models import ChannelUserRelationship

logging.basicConfig(level=logging.WARNING)


class Slackotron(Scribe, object):
  bot_name = slackotron_settings.BOT_NAME
  bot_icon_url = slackotron_settings.BOT_ICON_URL
  bot_icon_emoji = slackotron_settings.BOT_ICON_EMOJI
  bot_slack_id = slackotron_settings.BOT_SLACK_ID
  profanity_filter_on = slackotron_settings.PROFANITY_FILTER_ON
  safety_on = slackotron_settings.SAFETY_ON
  slack = slack_service.Slack()
  dashboard_manager = dashboard.dashboard_manager.DashboardManager()
  plugin_manager = plugins.plugin_manager.PluginManager()
  thread_manager = thread_manager.ThreadManager()
  database_manager = database.database_manager.DatabaseManager()

  def __init__(self):
    self.info('Slacko Bot:')
    self.info(self.bot_name)
    if not self.slack.api_valid() or not self.slack.auth_valid():
      self.critical('API and/or auth not valid! Exiting.')
      sys.exit()

  def _initialize_channels_and_users(self):
    self.info('Loading channels and users...')
    channel_id_to_name_map, channel_name_to_id_map = \
        self.slack.channel_id_name_maps()
    with self.database_manager.db.transaction():
      for k, v in channel_id_to_name_map.items():
        is_direct = True if k.startswith('D0') else False
        try:
          channel = Channel.get(
              Channel.slack_id == k
          )
          channel.slack_name = v
          channel.is_direct = is_direct
          channel.save()
        except Channel.DoesNotExist:
          channel = Channel.create(
              slack_name=v,
              slack_id=k,
              is_direct=is_direct
          )
        except Exception as e:
          self.error(e)
        channel_members = self.slack.channel_members(channel.slack_name)
        for channel_member in channel_members:
          is_slackbot = True if channel_member[1] == 'USLACKBOT' else False
          try:
            user = User.get(
                User.slack_name == channel_member[1],
                User.slack_id == channel_member[0],
                User.is_slackbot == is_slackbot
            )
          except User.DoesNotExist:
            user = User.create(
                slack_name=channel_member[1],
                slack_id=channel_member[0],
                is_slackbot=is_slackbot
            )
          except Exception as e:
            self.error(e)
          try:
            ChannelUserRelationship.create(
                channel=channel,
                user=user
            )
          except:
            pass

  def _create_slackotron_user(self):
    try:
      is_slackbot = False
      self.slackotron_user = User.get(
          User.slack_name == self.bot_name,
          User.slack_id == self.bot_slack_id,
          User.is_slackbot == is_slackbot
      )
    except User.DoesNotExist:
      self.slackotron_user = User.create(
          slack_name=self.bot_name,
          slack_id=self.bot_slack_id,
          is_slackbot=False
      )
    except Exception as e:
      self.error(e)

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
                response.save()

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

  def run(self):
    while True:
      try:
        self._on_rmq_message()
      except Exception as e:
        self.info('Exception:')
        self.error(e)
        traceback.print_exc()
        continue

  def start(self):
    self.database_manager.connect()
    self.database_manager.create_tables(Base)
    self._initialize_channels_and_users()
    self._create_slackotron_user()
    self.info('Users:')
    for user in User.select():
      self.info(user)
    self.info('Channels:')
    for channel in Channel.select():
      self.info(channel)
    self.plugin_manager.start_plugins()
    self.thread_manager.start_threads()
    self.dashboard_manager.start_dashboard()
    self.run()

  def stop(self):
    self.dashboard_manager.stop_dashboard()
    self.thread_manager.stop_threads()
    self.plugin_manager.stop_plugins()
    self.database_manager.disconnect()
    time.sleep(5)
    self.info(self.__class__.__name__ + ' is closing.')

if __name__ == '__main__' and __package__ is None:
  slackotron = Slackotron()
  try:
    slackotron.start()
  except KeyboardInterrupt:
    slackotron.stop()
    print('\nBye.')
