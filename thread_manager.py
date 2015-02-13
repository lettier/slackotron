#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import time
import traceback
import threading
import logging
import slackotron_settings
import slack_service
import decorators
import utilities
from scribe import Scribe
from models import Channel
from models import Response
from models import User
from models import Message

logging.basicConfig(level=logging.WARNING)


class SlackotronThreadManager(object):
  threads = {}
  thread_types = [
      'subscriber',
      'publisher'
  ]

  def _start_slackotron_thread(self, _type, **kwargs):
    if _type not in self.threads:
      self.threads[_type] = []
    slackotron_thread = SlackotronThreadFactory.new(
        _type,
        **kwargs
    )
    if slackotron_thread is None:
      return None
    slackotron_thread.daemon = False
    self.threads[_type].append(
        slackotron_thread
    )
    slackotron_thread.start()

  def _start_slackotron_threads(self):
    for channel in Channel.select():
      for _type in self.thread_types:
        params = {
            'channel_id': channel.get_id()
        }
        self._start_slackotron_thread(
            _type,
            **params
        )

  def _stop_slackotron_threads(self):
    for _type, threads in self.threads.items():
      for thread in threads:
        if hasattr(thread, 'stop_thread'):
          thread.stop_thread = True
    self.threads = {}

  def start_threads(self):
    self._start_slackotron_threads()

  def stop_threads(self):
    self._stop_slackotron_threads()


class SlackotronThreadFactory(object):

  @staticmethod
  def new(_type, **kwargs):
    if 'channel_id' not in kwargs:
      return None
    if _type == 'subscriber':
      return SlackChannelSubscriber(**kwargs)
    elif _type == 'publisher':
      return SlackChannelPublisher(**kwargs)


class SlackotronThread(Scribe, threading.Thread, object):
  lock = threading.Lock()

  def __init__(self, **kwargs):
    threading.Thread.__init__(self)
    self.stop_thread = False
    self.slack = slack_service.Slack()
    self.channel_id = kwargs['channel_id']
    self.channel = Channel.get(
        Channel.id == self.channel_id
    )

  def run(self):
    self.info(
        self.__class__.__name__ +
        ' starting with channel: ' +
        str(self.channel)
    )
    while True:
      try:
        self._run()
        if self.stop_thread:
          self.info(
              self.__class__.__name__ +
              ' stopping with channel: ' +
              str(self.channel)
          )
          break
      except Exception as e:
        self.error('Exception:')
        self.error(e)
        traceback.print_exc()
        continue

    def _run(self):
      pass


class SlackChannelSubscriber(SlackotronThread):

  def __init__(self, **kwargs):
    super(SlackChannelSubscriber, self).__init__(**kwargs)
    self.check_slack_interval = 5.0
    self.checked_slack_at = time.time() + self.check_slack_interval

  def _process_slack_raw_message(self, slack_raw_message):
    user, message, new = None, None, False
    SlackChannelSubscriber.lock.acquire()
    try:
      user = User.get(
          User.slack_id == slack_raw_message['user']
      )
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
    except Exception as e:
      self.error(e)
    finally:
      SlackChannelSubscriber.lock.release()
      return user, message, new

  @decorators.rabbitmq_publish(
      host=slackotron_settings.RABBITMQ_HOST_URL,
      exchange=slackotron_settings.PLUGIN_RABBITMQ_EXCHANGE_NAME,
      exchange_type='fanout',
      routing_key=slackotron_settings.PLUGIN_RABBITMQ_ROUTING_KEY
  )
  def _run(self, *args, **kwargs):
    current_time = time.time()
    rmq_messages = []
    if current_time - self.checked_slack_at > self.check_slack_interval:
      self.checked_slack_at = current_time
      slack_raw_messages = self.slack.channel_messages_since(
          self.channel.slack_id,
          30
      )
      for slack_raw_message in slack_raw_messages:
        user, message, new = self._process_slack_raw_message(
            slack_raw_message
        )
        if not new:
          continue
        self.info('Incoming message:')
        self.info(message)
        rmq_messages.append(
            {
                'channel_id': self.channel.get_id(),
                'user_id': user.get_id(),
                'message_id': message.get_id()
            }
        )
    return rmq_messages


class SlackChannelPublisher(SlackotronThread):

  def __init__(self, **kwargs):
    super(SlackChannelPublisher, self).__init__(**kwargs)
    self.bot_name = slackotron_settings.BOT_NAME
    if hasattr(slackotron_settings, 'BOT_ICON_URL'):
      self.bot_icon_url = slackotron_settings.BOT_ICON_URL
    if hasattr(slackotron_settings, 'BOT_ICON_EMOJI'):
      self.bot_icon_emoji = slackotron_settings.BOT_ICON_EMOJI
    self.bot_icon_url = slackotron_settings.BOT_ICON_URL
    self.bot_slack_id = slackotron_settings.BOT_SLACK_ID
    self.profanity_filter_on = slackotron_settings.PROFANITY_FILTER_ON

  def __format_response_text(self, user, response_text):
    if response_text.__class__.__name__ == 'str':
      response_text = response_text.decode('utf-8', 'ignore')
    return u'@' + \
        user.slack_name + \
        u', ' + \
        response_text

  def _run(self):
    SlackChannelPublisher.lock.acquire()
    try:
      is_approved = True
      is_sent = False
      is_deleted = False
      with Channel.database().transaction():
        self.channel = Channel.get(
            Channel.id == self.channel.get_id()
        )
        for response in list(Response.select().where(
            (Response.is_approved == is_approved) &
            (Response.is_sent == is_sent) &
            (Response.is_deleted == is_deleted) &
            (Response.to_channel == self.channel)
        )):
          response_text = response.text
          response_text = self.__format_response_text(
              response.to_user,
              response_text
          )
          if self.channel.is_secure is True:
            response_text = utilities.scrub_profanity(response_text)
          query_params = {
              'channel': self.channel.slack_id,
              'text': response_text,
              'parse': 'full',
              'linknames': 1,
              'unfurl_links': 'true',
              'unfult_media': 'true',
              'username': self.bot_name
          }
          if hasattr(slackotron_settings, 'BOT_ICON_URL'):
            query_params['icon_url'] = self.bot_icon_url
          if hasattr(slackotron_settings, 'BOT_ICON_EMOJI'):
            query_params['icon_emoji'] = self.bot_icon_emoji
          response_json = self.slack.send_message(query_params)
          if response_json is not None:
            response.text = response_text
            response.is_sent = True
            response.slack_timestamp = response_json['timestamp']
            response.save()
            self.info('Outgoing response:')
            self.info(response)
    except Exception as e:
      self.error(e.__class__.__name__)
      self.error(e)
      traceback.print_exc()
    finally:
      SlackChannelPublisher.lock.release()
