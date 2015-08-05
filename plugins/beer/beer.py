#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import random
import requests
import beer_settings
import plugins.plugin_base

class Beer(plugins.plugin_base.PluginBase):
  self._safe_set_config_from_env(beer_settings)
  api_url = beer_settings.API_URL
  order = beer_settings.ORDER
  activation_strings = [
      'recommend a beer',
      'recommend me a beer',
      'give me a beer',
      'give me a beer recommendation',
      'what\'s a good beer'
  ]

  def _callback(self, channel, user, message):
    params = {
        'order': self.order
    }
    response = requests.get(
        self.api_url,
        params=params
    ).json()
    beers = response['beers']
    beer = random.choice(beers)
    response = 'how about a ' + \
        beer['name'] + \
        '?' + \
        ' ' + \
        beer['description'].replace('\n', ' ')
    return response
