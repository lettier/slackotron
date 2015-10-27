#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import random
import requests
import plugins.plugin_base
import gif_gopher_settings
from bs4 import BeautifulSoup


class GifGopher(plugins.plugin_base.PluginBase):
  activation_strings = [
      'fetch me a gif about',
      'get me a gif about',
      'find me a gif about',
      'fetch a gif about',
      'get a gif about',
      'find a gif about',
      'search for a gif about'
  ]
  api_endpoint = gif_gopher_settings.API_ENDPOINT

  def _callback(self, channel, user, message):
    try:
      gif_query = self._parse_gif_query(message.text.lower())
      self.info(gif_query)
      if gif_query is None:
        return None
      if len(gif_query) is None:
        return None
      gif_query_split = gif_query.split()
      response = requests.get(
          self.api_endpoint + '-'.join(gif_query_split)
      )
      if response.status_code != 200:
        self.info('status_code != 200')
        return 'Site is down. :('
      soup = BeautifulSoup(response.text)
      images = soup.find_all(
          'img',
          attrs={'data-animated': True},
          limit=20
      )
      links = []
      for image in images:
        try:
          great_grandparent = image.parent.parent.parent
          tags = great_grandparent.find_all(
              'a',
              attrs={'data-tag-encoded': True}
          )
          tags = reduce(
              lambda x, y: x + y,
              map(
                  lambda x: x.split('-'),
                  [x['data-tag-encoded'] for x in tags]
              )
          )
          matches = [
              1 if x.lower().strip() in gif_query_split else 0 for x in tags
          ]
          add_image = sum(matches)
          if add_image >= len(gif_query_split):
            link = image['data-animated']
            links.append(link)
        except Exception as e:
          self.error(e)
          continue
      self.info(links)
      if len(links) == 0:
        return 'There was nothing.'
      elif len(links) > 1:
        link = random.choice(links)
      else:
        link = links[0]
      return link
    except Exception as e:
      self.error(e)
      return 'No.'

  def _parse_gif_query(self, message_text):
    try:
      index = message_text.rfind(' about ')
      return message_text[index + len(' about '):].strip()
    except:
      return None
