#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import requests
import plugins.plugin_base
import net_lingo_settings
from bs4 import BeautifulSoup


class NetLingo(plugins.plugin_base.PluginBase):
  '''
    NetLingo(plugins.plugin_base.PluginBase)
  '''
  url = net_lingo_settings.NETLINGO_URL
  activation_strings = [
  ]

  def _callback(self, channel, user, message):
    '''
      _callback(channel, user, message)
    '''
    try:
      self.redis_client.get('')
    except Exception:
      self.warning('Is redis-server running?')
      return None
    scraped = self.redis_client.get('netlingo:scraped')
    if scraped is None or scraped is False:
      self.__scrap_net_lingo()
      self.redis_client.set('netlingo:scraped', 'true')
    if self.redis_client.get('netlingo:scraped') == 'true':
      message_tokens = message.text.split()
      translations = {}
      for token in message_tokens:
        translations[token] = self.redis_client.get(
            u'netlingo:scraped:' + token
        )
      response = u', '.join([str(v) for _, v in translations.items() if v])
      if len(response) > 2:
        return response
    return None

  def __scrap_net_lingo(self):
    '''
      __scrap_net_lingo()
    '''
    response = requests.get(self.url)
    soup = BeautifulSoup(response.content)
    acronyms_raw = soup.find('div', {'class': 'list_box3'})
    for dom_element in acronyms_raw.find_all('li'):
      acronym = dom_element.find('span').find('a').text
      if len(dom_element.contents) >= 2:
        translation = dom_element.contents[1]
      else:
        continue
      if isinstance(acronym, str) and isinstance(translation, str):
        try:
          acronym = acronym.decode('utf-8', 'ignore')
          translation = translation.decode('utf-8', 'ignore')
        except Exception as error:
          self.error(error)
          acronym = bytes(acronym, 'utf-8').decode('utf-8', 'ignore')
          translation = bytes(translation, 'utf-8').decode('utf-8', 'ignore')
      self.redis_client.set(
          u'netlingo:scraped:' + acronym,
          translation
      )
