#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

# pylint:disable=attribute-defined-outside-init,no-member,bad-continuation

import sys
import traceback
import redis
import json
import slackotron_settings
import lib.slack
import models
import decorators
from lib.scribe import Scribe

RABBITMQ_PLUGIN_EXCHANGE = 'plugins'
RABBITMQ_PLUGIN_EXCHANGE_TYPE = 'fanout'
RABBITMQ_PLUGIN_ROUTING_KEY = 'plugins'
RABBITMQ_PLUGIN_RESPONSE_EXCHANGE = 'plugin_responses'
RABBITMQ_PLUGIN_RESPONSE_QUEUE = 'plugin_responses'
RABBITMQ_PLUGIN_RESPONSE_ROUTING_KEY = 'plugin_responses'


class PluginBase(Scribe, object):
  '''
    PluginBase(Scribe, object)
  '''
  bot_slack_id = slackotron_settings.BOT_SLACK_ID
  bot_slack_name = slackotron_settings.BOT_SLACK_NAME
  bot_icon_url = slackotron_settings.BOT_ICON_URL
  bot_icon_emoji = slackotron_settings.BOT_ICON_EMOJI
  rabbitmq_host_url = slackotron_settings.RABBITMQ_HOST_URL
  redis_host = slackotron_settings.REDIS_HOST
  redis_port = slackotron_settings.REDIS_PORT
  slack = lib.slack.Slack()
  activation_strings = []

  def __init__(self):
    self.redis_client = None
    self.slackotron_user = None
    self.channel = None
    self.user = None
    self.message = None

  def run(self):
    '''
      run()
    '''
    self.__initialize_redis()
    self.__get_or_create_slackotron_user()
    while True:
      try:
        self.__on_rmq_message()
      except KeyboardInterrupt:
        break
      except Exception as error:
        self.error(error.__class__.__name__)
        self.error(error)
        traceback.print_exc()
        break
    self.info('Plugin ' + self.__class__.__name__ + ' is closing.')
    sys.stdout.flush()

  def _callback(self, channel, user, message):
    '''
      _callback(self, channel, user, message)
    '''
    pass

  def __initialize_redis(self):
    '''
      __initialize_redis()
    '''
    try:
      self.redis_client = redis.StrictRedis(
          host=self.redis_host,
          port=self.redis_port,
          db=0
      )
      self.redis_client.get('')
    except Exception:
      self.warning('Is redis-server running?')

  def __get_or_create_slackotron_user(self):
    '''
      __get_or_create_slackotron_user()
    '''
    try:
      self.slackotron_user = models.User.get(
          models.User.slack_id == self.bot_slack_id,
          models.User.slack_name == self.bot_slack_name
      )
    except models.User.DoesNotExist:
      self.slackotron_user = models.User.create(
          slack_id=self.bot_slack_id,
          slack_name=self.bot_slack_name
      )
    except Exception as error:
      self.error(error)

  @decorators.rabbitmq_subscribe(
      host=slackotron_settings.RABBITMQ_HOST_URL,
      exchange=RABBITMQ_PLUGIN_EXCHANGE,
      exchange_type=RABBITMQ_PLUGIN_EXCHANGE_TYPE,
      routing_key=RABBITMQ_PLUGIN_ROUTING_KEY
  )
  def __on_rmq_message(self, *_, **kwargs):
    '''
      __on_rmq_message(*_, **kwargs)
    '''
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
          except Exception as error:
            self.error(error)
            return None
          self.__on_message(channel=channel, user=user, message=message)

  @decorators.rabbitmq_publish(
      host=slackotron_settings.RABBITMQ_HOST_URL,
      exchange=RABBITMQ_PLUGIN_RESPONSE_EXCHANGE,
      queue=RABBITMQ_PLUGIN_RESPONSE_QUEUE,
      routing_key=RABBITMQ_PLUGIN_RESPONSE_ROUTING_KEY
  )
  def __on_message(self, *_, **kwargs):
    '''
      __on_message(*_, **kwargs)
    '''
    try:
      self.channel = kwargs['channel']
      self.user = kwargs['user']
      self.message = kwargs['message']
    except Exception as error:
      self.error(error)
      return None
    if not hasattr(self.message, 'text'):
      return None
    if self.message.text is None:
      self.message.text = ''
    if len(self.message.text) == 0:
      return None
    if not self.__is_activated(self.message.text):
      return None
    plugin_response = self._callback(
        self.channel,
        self.user,
        self.message
    )
    if plugin_response is None:
      plugin_response = ''
    if len(plugin_response) == 0:
      return None
    if plugin_response.__class__.__name__ == 'str':
      plugin_response = plugin_response.decode(
          'utf-8',
          'ignore'
      )
    elif plugin_response.__class__.__name__ == 'unicode':
      plugin_response = plugin_response.encode(
          'utf-8',
          'ignore'
      )
    response = {
        'channel_id': self.channel.get_id(),
        'user_id': self.user.get_id(),
        'message_id': self.message.get_id(),
        'plugin_name': self.__class__.__name__,
        'plugin_response': plugin_response
    }
    return response

  def __is_activated(self, message_text):
    '''
      __is_activated(message_text)
    '''
    if len(self.activation_strings) > 0:
      for activation_string in self.activation_strings:
        if activation_string.lower() in message_text.lower():
          return True
    elif len(self.activation_strings) == 0:
      return True
    return False

  def _clean_up_message_text(self, message_text):
    '''
      _clean_up_message_text(message_text)
    '''
    bot_slack_name = self.bot_slack_name.strip().split()
    for token in bot_slack_name:
      message_text = message_text.replace(token, '')
      message_text = message_text.replace(token.lower(), '')
    for activation_string in self.activation_strings:
      message_text = message_text.replace(activation_string, '')
      message_text = message_text.replace(activation_string.lower(), '')
    self.info(message_text)
    return message_text
