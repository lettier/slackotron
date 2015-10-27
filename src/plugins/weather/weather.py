#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import requests
import weather_settings
import plugins.plugin_base


class Weather(plugins.plugin_base.PluginBase):
  api_endpoint = weather_settings.API_ENDPOINT
  zipcode = weather_settings.ZIP
  use_fahrenheit = weather_settings.USE_FAHRENHEIT
  activation_strings = [
      'what\'s the weather like',
      'what\'s the weather',
      'how\'s the weather',
      'whats the weather like',
      'whats the weather',
      'hows the weather'
  ]

  def _callback(self, channel, user, message):
    try:
      response = requests.get(
          self.api_endpoint,
          params={
              'inputstring': str(self.zipcode)
          },
          allow_redirects=False
      )
      self.location = response.headers['location']
      response = requests.get(
          self.location + '&FcstType=json'
      )
    except Exception as e:
      self.error(e)
      return 'I dunno.'
    if response.status_code != 200:
      self.warning('status_code != 200')
      return 'I dunno.'
    json = response.json()
    temp = int(json['currentobservation']['Temp'])
    description = json['currentobservation']['Weather']
    temp_symbol = 'F'
    if self.use_fahrenheit is False:
      temp = self.__fahrenheit_to_celsius(temp)
      temp_symbol = 'C'
    return ''.join([
        'I am seeing ',
        description,
        '. '
        'The temp is ',
        str(int(temp)),
        temp_symbol,
        '. ',
        self.location
    ])

  def __kelvin_to_celsius(self, kelvin_reading):
    return float(kelvin_reading) - 273.15

  def __celsius_to_fahrenheit(self, celsius_reading):
    return ((float(celsius_reading) * 9) / 5) + 32.0

  def __fahrenheit_to_celsius(self, fahrenheit_reading):
    return (fahrenheit_reading - 32.0) * (5 / 9.0)
