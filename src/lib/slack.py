#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import re
import time
import requests
import slackotron_settings
from scribe import Scribe


class Slack(Scribe, object):
  api_token = slackotron_settings.SLACK_API_TOKEN
  api_url = slackotron_settings.SLACK_API_URL
  ignore_urls = slackotron_settings.IGNORE_URLS
  ignore_subtypes = slackotron_settings.IGNORE_MESSAGE_TYPES
  ignore_bots = slackotron_settings.IGNORE_BOTS
  slackotron_bot_slack_id = slackotron_settings.BOT_SLACK_ID
  slackotron_bot_slack_name = slackotron_settings.BOT_SLACK_NAME

  def __init__(self):
    self.channel_id_to_name_map = {}
    self.channel_name_to_id_map = {}
    self.member_id_to_name_map = {}
    self.member_name_to_id_map = {}
    self.channel_id_name_maps()
    self.member_id_name_maps()

  def request(self, end_point, query_params, headers={}, data=''):
    params = {'token': self.api_token}
    if isinstance(query_params, type({})) is True:
      params = dict(params.items() + query_params.items())
    try:
      if end_point != 'files.upload':
        response = requests.get(
            self.api_url + end_point, params=params
        )
      else:
        response = requests.post(
            self.api_url + end_point,
            params=params,
            headers=headers,
            data=data
        )
    except Exception as error:
      self.error(error)
      return None
    if response is None:
      self.warning('Response is none!')
      return None
    if response.status_code != requests.codes.ok:
      self.warning('Response is not okay! %s' % response.status_code)
      self.info(response.text)
      return None
    return response.json()

  def api_valid(self):
    response_json = self.request('api.test', {})
    if response_json is None:
      return False
    return response_json['ok']

  def auth_valid(self):
    response_json = self.request('auth.test', {})
    if response_json is None:
      return False
    return response_json['ok']

  def auth_user_id_name(self):
    response_json = self.request('auth.test', {})
    if response_json is None:
      return None
    return response_json['user_id'], response_json['user']

  def channel_id_name_maps(self):
    self.channel_id_to_name_map = {}
    self.channel_name_to_id_map = {}
    response_json1 = self.request(
        'channels.list',
        {'exclude_archived': 1}
    )
    response_json2 = self.request('im.list', {})
    if response_json1 is not None and response_json2 is not None:
      if response_json1['ok'] and response_json2['ok']:
        channels = response_json1['channels'] + response_json2['ims']
        for channel in channels:
          idd = str(channel['id'])
          try:
            name = str(channel['name'])
          except Exception:
            name = str(channel['user'])
          self.channel_id_to_name_map[idd] = name
          self.channel_name_to_id_map[self.channel_id_to_name_map[idd]] = idd
    return self.channel_id_to_name_map, self.channel_name_to_id_map

  def member_id_name_maps(self):
    self.member_id_to_name_map = {}
    self.member_name_to_id_map = {}
    response_json = self.request('users.list', {})
    if response_json is not None:
      if response_json['ok']:
        members = response_json['members']
        for member in members:
          if not member['deleted']:
            idd = str(member['id'])
            name = str(member['name'])
            self.member_id_to_name_map[idd] = name
            self.member_name_to_id_map[self.member_id_to_name_map[idd]] = idd
    return self.member_id_to_name_map, self.member_name_to_id_map

  def channel_info(self, channel_id):
    query_params = {
        'channel': channel_id
    }
    response_json = None
    if channel_id.startswith('C0') is True:
      response_json = self.request('channels.info', query_params)
    elif channel_id.startswith('D0') is True:
      response_json = {
          'channel': {
              'members': [
                  self.member_channel_name(channel_id),
                  self.auth_user_id_name()[0]
              ]
          }
      }
    return response_json

  def slackbot_channel_id(self):
    return self.channel_name_to_id_map['USLACKBOT']

  def member_channel_id(self, member_name):
    return self.channel_name_to_id_map[self.member_name_to_id_map[member_name]]

  def member_channel_name(self, member_channel_id):
    return self.channel_id_to_name_map[member_channel_id]

  def channel_id(self, channel_name):
    if channel_name in self.member_name_to_id_map:
      return self.member_channel_id(channel_name)
    else:
      return self.channel_name_to_id_map[channel_name]

  def channel_members(self, channel_name):
    response_json = self.channel_info(
        self.channel_name_to_id_map[channel_name]
    )
    channel_members = []
    if response_json is not None:
      if 'channel' in response_json:
        if 'members' in response_json['channel']:
          for member_id in response_json['channel']['members']:
            try:
              member_name = self.member_id_to_name_map[member_id]
            except KeyError:
              continue
            channel_members.append(
                (
                    member_id,
                    member_name
                )
            )
    return channel_members

  def channel_history(self, query_params):
    response_json = None
    if query_params['channel'].startswith('C0') is True:
      response_json = self.request('channels.history', query_params)
    elif query_params['channel'].startswith('D0') is True:
      response_json = self.request('im.history', query_params)
    return response_json

  def last_channel_message(self, channel_id):
    now = time.time()
    query_params = {
        'channel': channel_id,
        'latest': now,
        'count': 1
    }
    json_response = self.channel_history(query_params)
    message = self.parse_channel_messages(json_response)
    if len(message) == 0:
      return None
    if len(message) > 0:
      return message[0]
    return message

  def all_channel_messages(self, channel_id):

    def channel_messages(channel_id, timestamp):
      messages = []
      query_params = {
          'channel': channel_id,
          'latest': timestamp
      }
      json_response = self.channel_history(query_params)
      if 'messages' in json_response:
        ignore_subtypes = self.ignore_subtypes
        ignore_urls = self.ignore_urls
        self.ignore_subtypes = []
        self.ignore_urls = False
        messages = self.parse_channel_messages(json_response)
        self.ignore_subtypes = ignore_subtypes
        self.ignore_urls = ignore_urls
        if len(messages) == 0:
          return messages
      if 'has_more' in json_response:
        if json_response['has_more'] is True:
          timestamp = messages[-1]['timestamp']
          return messages + channel_messages(channel_id, timestamp)
        else:
          return messages

    return channel_messages(channel_id, time.time())

  def channel_messages_since(self, channel_id, seconds):
    now = time.time()
    query_params = {
        'channel': channel_id,
        'oldest': now - (seconds + 1),
        'latest': now + 1
    }
    response_json = self.channel_history(query_params)
    messages = self.parse_channel_messages(response_json)
    return messages

  def parse_channel_messages(self, response_json):
    messages_parsed = []

    if response_json is None:
      return messages_parsed
    if not hasattr(response_json, 'items'):
      return messages_parsed
    if 'messages' not in response_json:
      return messages_parsed

    messages = response_json['messages']
    for message in messages:
        if 'subtype' in message:
          if message['subtype'] in self.ignore_subtypes:
            continue
        if u'user' not in message and u'username' not in message:
          continue
        if u'text' not in message:
          continue
        if u'ts' not in message:
          continue

        message['text'] = message.get('text', u'') or u''
        message['text'] = self._strip_at_mentions(message['text'])
        if len(message['text']) == 0:
          continue

        message['user'] = message.get(
            'user',
            message.get('username', '')
        ) or ''
        if len(message['user']) == 0:
          continue
        if message['user'] == self.slackotron_bot_slack_name:
          message['user'] = str(self.slackotron_bot_slack_id)
        if self.ignore_bots is True:
          if message.get('subtype', '').lower() == 'bot_message':
            continue
          if not message['user'].lower().startswith('u0'):
            continue

        urls = []
        attachments = message.get('attachments', []) or []
        if hasattr(attachments, '__iter__'):
          for attachment in attachments:
            if not hasattr(attachment, 'items'):
              continue
            if 'from_url' in attachment:
              urls.append(attachment['from_url'])
        if self.ignore_urls is True:
          if len(urls) > 0:
            continue
          text_lower = message['text'].lower()
          match = re.match(r'.*?:?//\S*\.\D{2,3}?', text_lower, re.M | re.I)
          if match is not None:
            continue

        if isinstance(message['text'], str):
          try:
            message['text'] = message['text'].decode('utf-8', 'ignore')
          except Exception:
            message['text'] = bytes(message['text'], 'utf-8').decode(
                'utf-8',
                'ignore'
            )

        messages_parsed.append(
            {
                'user': str(message['user']),
                'text': message['text'],
                'timestamp': str(message['ts']),
                'urls': urls
            }
        )
    return messages_parsed

  def send_message(self, query_params):
    response_json = self.request('chat.postMessage', query_params)
    if response_json is None:
      return None
    response = {
        'timestamp': response_json['ts'],
        'channel_id': response_json['channel']
    }
    return response

  def delete_message(self, channel_id, timestamp):
    query_params = {
        'channel': channel_id,
        'ts': timestamp
    }
    response_json = self.request('chat.delete', query_params)
    if response_json is None:
      return None
    return response_json

  def file_upload(self, **kwargs):
    query_params = kwargs.get('query_params', {})
    headers = kwargs.get('headers', {})
    data = kwargs.get('data', '')
    response_json = self.request(
        'files.upload',
        query_params,
        headers,
        data
    )
    if response_json is None:
      return None
    return response_json

  def _strip_at_mentions(self, text):
    if text is None:
      return u''
    if len(text) == 0:
      return u''
    matches = re.findall(r'<@\w+?\|?\w*?>:?,?', text, re.M | re.I)
    for match in matches:
      text = text.replace(match, u'')
    return text
