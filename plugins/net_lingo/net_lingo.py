#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  SLACKOTRON

  An extensible slack bot.
'''

import requests
import BeautifulSoup
import net_lingo_settings
import plugins.plugin_base


class NetLingo(plugins.plugin_base.PluginBase):
  url = net_lingo_settings.NETLINGO_URL
  activation_strings = [
  ]

  def _callback(self, channel, user, message):
    try:
      self.redis_client.get('')
    except:
      self.warning('Is redis-server running?')
      return None
    if (self.redis_client.get('netlingo:scraped') is None or
       self.redis_client.get('netlingo:scraped') == 'false'):
      response = requests.get(self.url)
      soup = BeautifulSoup.BeautifulSoup(response.content)
      acronyms_raw = soup.find('div', {'class': 'list_box3'})
      for dom_element in acronyms_raw.findAll('li'):
        acronym = dom_element.find('span').find('a').text
        if len(dom_element.contents) >= 2:
          translation = dom_element.contents[1]
        else:
          continue
        self.redis_client.set(
            'netlingo:scraped:' + str(acronym),
            str(translation)
        )
      self.redis_client.set('netlingo:scraped', 'true')
    if self.redis_client.get('netlingo:scraped') == 'true':
      message_tokens = message.text.split()
      translations = {}
      for token in message_tokens:
        translations[token] = self.redis_client.get(
            'netlingo:scraped:' + str(token)
        )
      response = ', '.join([str(v) for k, v in translations.items() if v])
      if len(response) > 2:
        return response
    return None
