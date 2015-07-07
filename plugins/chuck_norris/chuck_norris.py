#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import urllib
import requests
import chuck_norris_settings
import plugins.plugin_base


class ChuckNorris(plugins.plugin_base.PluginBase):
  self._safe_set_config_from_env(chuck_norris_settings)
  exclude = chuck_norris_settings.EXCLUDE
  activation_strings = [
      'tell me about chuck norris',
      'what do you know about chuck norris',
      'tell me a chuck norris joke',
      'any good chuck norris jokes'
  ]

  def _callback(self, channel, user, message):
    params = {
        'exclude': self.exclude
    }
    response = requests.get(
        'http://api.icndb.com/jokes/random',
        params=params
    ).json()
    if response['type'] == 'success':
      joke_text = response['value']['joke']
      joke_text = urllib.unquote_plus(joke_text)
    else:
      joke_text = "Who's Chuck Norris?"
    return joke_text
