#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import re
import suds
import random
import models
import plugins.plugin_base
import yoda_speak_settings


class YodaSpeak(plugins.plugin_base.PluginBase):
  self._safe_set_config_from_env(yoda_speak_settings)
  api_url = yoda_speak_settings.API_URL
  activation_probability = yoda_speak_settings.ACTIVATION_PROBABILITY
  activation_strings = [
  ]

  def _callback(self, channel, user, message):
    if random.randrange(100) >= self.activation_probability:
      return None
    try:
      message_text = message.text
      message_text = self.__fix_urls(message_text)
      message_text = self.__fix_slack_user_ids(message_text)
      client = suds.client.Client(self.api_url)
      response = client.service.yodaTalk(message_text)
      if response is not None and len(response) > 0:
        response = self.__replace_i(
            str(response)
        )
        if message.text.lower() in response.lower():
          return None
        elif len(self.__scrub_urls(message.text).split()) == 0:
          return None
        else:
          return response
      else:
        return None
    except Exception as e:
      self.error(e)
      return None

  def __replace_i(self, text):
    text_tokens = text.split()
    result = []
    for index, text_token in enumerate(text_tokens):
      if text_token.lower() in ['i', 'i,', 'i.', 'i?', 'i!']:
        postfix = ''
        if text_token[-1] in [',', '.', '?', '!']:
          postfix = text_token[-1]
        if index == 0:
          text_token = 'You'
        else:
          text_token = 'you'
        text_token += postfix
      result.append(text_token)
    return ' '.join(result)

  def __find_slack_user_ids(self, text):
    re_compiled = re.compile('(?P<SLACK_USER_ID><@u.*?>)', flags=re.U | re.I)
    slack_user_ids = re_compiled.findall(text)
    return slack_user_ids

  def __fix_slack_user_ids(self, text):
    slack_user_ids = self.__find_slack_user_ids(text)
    for slack_user_id in slack_user_ids:
      slack_user_id_fixed = slack_user_id.replace('<@', '').replace('>', '')
      try:
        user = models.User.get(models.User.slack_id == slack_user_id_fixed)
      except models.User.DoesNotExist:
        continue
      text = text.replace(slack_user_id, u'@' + user.slack_name)
    return text

  def __find_urls(self, text):
    re_compiled = re.compile('(?P<URL><https?://.*?>)', flags=re.U | re.I)
    urls = re_compiled.findall(text)
    return urls

  def __fix_urls(self, text):
    urls = self.__find_urls(text)
    for url in urls:
      url_fixed = url.replace('<', '').replace('>', '').replace('/ /', '//')
      text = text.replace(url, url_fixed)
    return text

  def __scrub_urls(self, text):
    urls = self.__find_urls(text)
    for url in urls:
      text = text.replace(url, '')
    return text
