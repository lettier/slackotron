#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import re
import requests
import plugins.plugin_base  # pylint:disable=import-error
from bs4 import BeautifulSoup


class BigLebowski(plugins.plugin_base.PluginBase):  # noqa pylint:disable=no-init,too-few-public-methods
  '''
    BigLebowski(plugins.plugin_base.PluginBase)
  '''
  activation_strings = [
      'give me a lebowski quote',
      'how about a lebowski quote',
      'lebowski quote'
  ]

  def _callback(self, *_):  # pylint:disable=no-self-use
    '''
      _callback(channel, user, message)
    '''
    response = requests.get('http://www.dudequote.com/')
    soup = BeautifulSoup(response.content)
    for break_tag in soup.find_all('br'):
      break_tag.replaceWith(' ')
    quote = str(soup.find(id='quote'))
    tags = re.compile(r'<.*?>')
    quote = tags.sub(' ', quote)
    entities = re.compile(r'&.*?;')
    quote = entities.sub('', quote)
    quote = quote.replace('\n', '')
    return quote
