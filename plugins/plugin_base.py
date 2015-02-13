#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  SLACKOTRON

  An extensible slack bot.
'''

import traceback
import slackotron_settings
import decorators
import redis
import json
import models
import slack_service
from scribe import Scribe


class PluginBase(Scribe, object):
  bot_name = slackotron_settings.BOT_NAME
  bot_icon_url = slackotron_settings.BOT_ICON_URL
  bot_icon_emoji = slackotron_settings.BOT_ICON_EMOJI
  bot_slack_id = slackotron_settings.BOT_SLACK_ID
  rabbitmq_host_url = slackotron_settings.RABBITMQ_HOST_URL
  plugin_rabbitmq_exchange_name = \
      slackotron_settings.PLUGIN_RABBITMQ_EXCHANGE_NAME
  plugin_rabbitmq_queue_prefix = \
      slackotron_settings.PLUGIN_RABBITMQ_QUEUE_PREFIX
  redis_host = slackotron_settings.REDIS_HOST
  redis_port = slackotron_settings.REDIS_PORT
  slack = slack_service.Slack()
  activation_strings = []

  def _callback(self, rmq_body):
    pass

  def __initialize_redis(self):
    try:
      self.redis_client = redis.StrictRedis(
          host=self.redis_host,
          port=self.redis_port,
          db=0
      )
      self.redis_client.get('')
    except:
      self.warning('Is redis-server running?')

  def __create_slackotron_user(self):
    try:
      is_slackbot = False
      self.slackotron_user = models.User.get(
          models.User.slack_name == self.bot_name,
          models.User.slack_id == self.bot_slack_id,
          models.User.is_slackbot == is_slackbot
      )
    except models.User.DoesNotExist:
      self.slackotron_user = models.User.create(
          slack_name=self.bot_name,
          slack_id=self.bot_slack_id,
          is_slackbot=False
      )
    except Exception as e:
      self.error(e)

  @decorators.rabbitmq_subscribe(
      host=slackotron_settings.RABBITMQ_HOST_URL,
      exchange=slackotron_settings.PLUGIN_RABBITMQ_EXCHANGE_NAME,
      exchange_type='fanout',
      routing_key=slackotron_settings.PLUGIN_RABBITMQ_ROUTING_KEY
  )
  def __on_rmq_message(self, *args, **kwargs):
    if 'rmq_message' in kwargs:
      rmq_message = kwargs['rmq_message']
    else:
      return
    rmq_message = json.loads(rmq_message)
    channel, user, message = None, None, None
    if 'channel_id' in rmq_message:
      if 'user_id' in rmq_message:
        if 'message_id' in rmq_message:
          try:
            channel = models.Channel.get(
                models.Channel.id == rmq_message['channel_id']
            )
            user = models.User.get(
                models.User.id == rmq_message['user_id']
            )
            message = models.Message.get(
                models.Message.id == rmq_message['message_id']
            )
          except Exception as e:
            self.error(e)
            return
          self.__on_message(channel=channel, user=user, message=message)

  @decorators.rabbitmq_publish(
      host=slackotron_settings.RABBITMQ_HOST_URL,
      exchange=slackotron_settings.MAIN_RABBITMQ_EXCHANGE_NAME,
      exchange_type='direct',
      queue=slackotron_settings.MAIN_RABBITMQ_QUEUE_NAME,
      routing_key=slackotron_settings.MAIN_RABBITMQ_ROUTING_KEY
  )
  def __on_message(self, *args, **kwargs):
    response = None
    channel = None
    user = None
    message = None
    if 'channel' in kwargs:
      channel = kwargs['channel']
      if 'user' in kwargs:
        user = kwargs['user']
        if 'message' in kwargs:
          message = kwargs['message']
          if message is not None:
            if self.__is_activated(message.text.lower()):
              plugin_response = self._callback(channel, user, message)
              if plugin_response is not None and plugin_response != '':
                if plugin_response.__class__.__name__ == 'str':
                  plugin_response = plugin_response.decode('utf-8', 'ignore')
                elif plugin_response.__class__.__name__ == 'unicode':
                  plugin_response = plugin_response.encode('utf-8', 'ignore')
                response = {
                    'channel_id': channel.get_id(),
                    'user_id': user.get_id(),
                    'message_id': message.get_id(),
                    'plugin_name': self.__class__.__name__,
                    'plugin_response': plugin_response
                }
    return response

  def __is_activated(self, message_text):
    if len(self.activation_strings) > 0:
      for activation_string in self.activation_strings:
        if activation_string.lower() in message_text:
          return True
    elif len(self.activation_strings) == 0:
      return True
    return False

  def _strip_bot_name_activation_string(self, message_text):
    bot_name = self.bot_name.lower().split()
    for word in bot_name:
      if word in message_text:
        message_text = message_text.replace(word, '')
    for activation_string in self.activation_strings:
      activation_string = activation_string.split()
      for word in activation_string:
        if word in message_text:
          message_text = message_text.replace(word, '')
    return message_text

  def run(self):
    self.__initialize_redis()
    self.__create_slackotron_user()
    while True:
      try:
        self.__on_rmq_message()
      except Exception as e:
        self.error(e.__class__.__name__)
        self.error(e)
        traceback.print_exc()
        break
      except KeyboardInterrupt:
        break
    self.info('Plugin ' + self.__class__.__name__ + ' is closing.')
