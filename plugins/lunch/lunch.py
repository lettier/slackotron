#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
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
      'what\'s for lunch',
      'whats for lunch',
      'give me a lunch suggestion',
      'what should we have for lunch'
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
      return 'an apple?'
    choices = []
    for choice in response_json:
      if 'dba' in choice:
        if 'building' in choice:
          if 'street' in choice:
            if 'grade' in choice:
              choices.append(choice)
    if len(choices) == 0:
      return 'I dunno. What did you bring?'
    random_choice = random.choice(choices)
    name = random_choice['dba'].title().replace("'S", "'s")
    building = random_choice['building'].strip().title()
    street = ' '.join(random_choice['street'].strip().title().split())
    grade = random_choice['grade']
    return 'um...how about ' + \
        random_cuisine_description.rstrip() + \
        '? Looks like ' + \
        name + \
        ' is open. They\'re at ' + \
        building + \
        ' ' + \
        street + \
        '. They got a ' + \
        grade + \
        '.'
