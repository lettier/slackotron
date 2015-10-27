#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2016.

  http://www.lettier.com/

  Slackotron
'''

# pylint:disable=attribute-defined-outside-init,no-member,bad-continuation,unused-argument

import time
import traceback
import slackotron_settings
import decorators
from lib.scribe import Scribe
from models import Channel
from models import User
from models import Message
from plugins.plugin_base import RABBITMQ_PLUGIN_EXCHANGE
from plugins.plugin_base import RABBITMQ_PLUGIN_EXCHANGE_TYPE
from plugins.plugin_base import RABBITMQ_PLUGIN_ROUTING_KEY


class ChannelSubscriber(Scribe, object):
  '''
    ChannelSubscriber()
  '''

  def __init__(self, **kwargs):
    self.channel_id = kwargs['channel_id']
    self.slack = kwargs['slack']
    self.check_slack_interval = 1.0
    self.checked_slack_at = time.time() + self.check_slack_interval

  @decorators.rabbitmq_publish(
    host=slackotron_settings.RABBITMQ_HOST_URL,
    exchange=RABBITMQ_PLUGIN_EXCHANGE,
    exchange_type=RABBITMQ_PLUGIN_EXCHANGE_TYPE,
    routing_key=RABBITMQ_PLUGIN_ROUTING_KEY
  )
  def step(self, *args, **kwargs):
    '''
      step(*args, **kwargs)
    '''

    try:
      self.channel = Channel.get(
          Channel.id == self.channel_id
      )
      if self.channel.is_subscribed is False:
        return []
      current_time = time.time()
      rmq_messages = []
      if (current_time - self.checked_slack_at) > self.check_slack_interval:
        self.checked_slack_at = current_time
        slack_raw_messages = self.slack.channel_messages_since(
          self.channel.slack_id,
          2
        )
        for slack_raw_message in slack_raw_messages:
          user, message, new = self._process_slack_raw_message(
              slack_raw_message
          )
          if not new:
            continue
          self.info(message)
          rmq_messages.append(
              {
                  'channel_id': self.channel.get_id(),
                  'user_id': user.get_id(),
                  'message_id': message.get_id()
              }
          )
      return rmq_messages
    except Exception as error:
      self.error(error)
      traceback.print_exc()
      return []

  def _process_slack_raw_message(self, slack_raw_message):
    '''
      _process_slack_raw_message(slack_raw_message)
    '''

    user, message, new = None, None, False
    try:
      try:
        user = User.get(
            User.slack_id == slack_raw_message['user']
        )
      except User.DoesNotExist:
        if len(slack_raw_message['user']) == 0:
          raise Exception("Raw slack message user field empty.")
        self.slack.member_id_name_maps()
        slack_name = self.slack.member_id_to_name_map.get(
            slack_raw_message['user'],
            ''
        ) or ''
        if len(slack_name) == 0:
          raise Exception('Could not find slack name.')
        user = User(
            slack_id=str(slack_raw_message['user']),
            slack_name=slack_name
        )
        user.save()
      try:
        message = Message.get(
            Message.slack_timestamp == slack_raw_message['timestamp'],
            Message.user == user,
            Message.channel == self.channel
        )
        new = False
      except Message.DoesNotExist:
        message = Message.create(
            text=slack_raw_message['text'],
            slack_timestamp=slack_raw_message['timestamp'],
            channel=self.channel,
            user=user
        )
        new = True
    except Exception as error:
      self.error(error)
    return user, message, new
