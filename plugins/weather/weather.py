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
  url = weather_settings.OPENWEATHER_URL
  api_url = weather_settings.OPENWEATHER_API_URL
  city = weather_settings.CITY
  zipcode = weather_settings.ZIP
  country = weather_settings.COUNTRY
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
          self.api_url + '?q=' + self.city.lower() + ',' + self.country.lower()
      )
    except:
      return None
    if response.status_code != 200:
      self._respond(channel, user, 'I dunno.')
      return None
    json = response.json()
    descriptions = ', '.join(
        [x['description'].lower() for x in json['weather']]
    )
    last_comma_location = descriptions.rfind(',')
    if last_comma_location != -1:
      conjunction = ', and'
      if len(descriptions.split(', ')) <= 2:
        conjunction = ' and'
      descriptions = descriptions[:last_comma_location] + \
          conjunction + descriptions[last_comma_location + 1:]
    city_id = json['id']
    temp = json['main']['temp']
    temp = self.__kelvin_to_celsius(temp)
    temp_symbol = 'C'
    if self.use_fahrenheit:
      temp = self.__celsius_to_fahrenheit(temp)
      temp_symbol = 'F'
    return 'I\'m seeing ' + \
        descriptions + \
        '. ' + \
        'The temp is ' + str(int(temp)) + temp_symbol + \
        '.  ' + \
        self.url + str(city_id)

  def __kelvin_to_celsius(self, kelvin_reading):
    return float(kelvin_reading) - 273.15

  def __celsius_to_fahrenheit(self, celsius_reading):
    return ((float(celsius_reading) * 9) / 5) + 32.0
