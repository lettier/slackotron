#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import re
import requests
import plugins.plugin_base
from BeautifulSoup import BeautifulSoup


class BigLebowski(plugins.plugin_base.PluginBase):
  activation_strings = [
      'give me a lebowski quote',
      'how about a lebowski quote',
      'lebowski quote'
  ]

  def _callback(self, channel, user, message):
    response = requests.get('http://www.dudequote.com/')
    soup = BeautifulSoup(response.content)
    for br in soup.findAll('br'):
      br.replaceWith(' ')
    quote = str(soup.find(id='quote'))
    tags = re.compile(r'<.*?>')
    quote = tags.sub(' ', quote)
    entities = re.compile(r'&.*?;')
    quote = entities.sub('', quote)
    quote = quote.replace('\n', '')
    return quote
