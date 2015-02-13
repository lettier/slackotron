#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  SLACKOTRON

  An extensible Slack bot.
'''

import re
import suds
import random
import plugins.plugin_base
import yoda_speak_settings


class YodaSpeak(plugins.plugin_base.PluginBase):
  api_url = yoda_speak_settings.API_URL
  activation_probability = yoda_speak_settings.ACTIVATION_PROBABILITY
  activation_strings = [
  ]

  def _callback(self, channel, user, message):
    if random.randrange(100) >= self.activation_probability:
      return None
    try:
      client = suds.client.Client(self.api_url)
      response = client.service.yodaTalk(message.text)
      if response is not None and len(response) > 0:
        response = self.__replace_i(
            str(response)
        )
        if message.text.lower() in response.lower():
          return None
        elif len(self.__scrub_urls(message.text).split()) == 0:
          return None
        else:
          return self.__fix_urls(response)
      else:
        return None
    except Exception as e:
      self.warning(e)
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

  def __find_urls(self, text):
    re_compiled = re.compile('(?P<URL><https?:/ /.*?>)')
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
