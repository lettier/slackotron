#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  SLACKOTRON

  An extensible slack bot.
'''

import requests
import random
import lunch_settings
import plugins.plugin_base


class Lunch(plugins.plugin_base.PluginBase):
  api_url = lunch_settings.NYC_OPEN_DATA_API_URL
  categories = lunch_settings.CATEGORIES
  zipcode = lunch_settings.ZIP
  activation_strings = [
      "what's for lunch?",
      "give me a lunch suggestion.",
      "what should we have for lunch?"
  ]

  def _callback(self, channel, user, message):
    random_cuisine_description = random.choice(
        self.categories
    )
    params = {
        'zipcode': self.zipcode,
        'cuisine_description': random_cuisine_description,
        '$where': 'grade is not null'
    }
    response_json = requests.get(
        self.api_url,
        params=params
    ).json()
    if len(response_json) == 0:
      return None
    random_choice = random.choice(response_json)
    return "um...how about " + \
        random_cuisine_description.rstrip() + \
        "? Looks like " + \
        random_choice['dba'].title().replace("'S", "'s") + \
        " is open. They're at " + \
        random_choice['building'].lstrip().rstrip().title() + \
        ' ' + \
        ' '.join(random_choice['street'].lstrip().rstrip().title().split()) + \
        '. They got a ' + \
        random_choice['grade'] + \
        '.'
