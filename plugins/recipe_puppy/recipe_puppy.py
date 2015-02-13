#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron--An extensible slack bot.
'''

import httplib2
import random
import requests
import json
import nltk
import recipe_puppy_settings
import plugins.plugin_base


class RecipePuppy(plugins.plugin_base.PluginBase):
  api_url = recipe_puppy_settings.RECIPEPUPPY_API_URL
  activation_strings = [
      'what can I make with'
  ]
  activation_threshold = 0.4

  def _callback(self, channel, user, message):
    requested_ingredients = self.__requested_ingredients(message.text.lower())
    if len(requested_ingredients) == 0:
      return 'I dunno.'
    valid_results = self.__valid_results_from_redis(
        requested_ingredients
    )
    if len(valid_results) == 0:
      api_results = self.__results_from_api(
          requested_ingredients,
          3
      )
      if len(api_results) > 0:
        valid_results = self.__valid_results(
            requested_ingredients,
            api_results
        )
        if len(valid_results) > 0:
          self.__store_valid_results_in_redis(
              requested_ingredients,
              valid_results
          )
    try:
      recipe = random.choice(valid_results)
      response = 'how about ' + recipe['title'].rstrip().lstrip() + ' ' + \
          recipe['thumbnail'] + ' ' + recipe['href']
      return response
    except:
      return None

  def __valid_results_from_redis(self, requested_ingredients):
    valid_results = []
    json_dump = None
    redis_key = self.__redis_key(requested_ingredients)
    try:
      json_dump = self.redis_client.get(redis_key)
    except:
      self.warning('\n[RecipePuppy] Is redis-server running?')
    if json_dump is not None:
      valid_results = json.loads(json_dump)
    return valid_results

  def __store_valid_results_in_redis(
      self,
      requested_ingredients,
      valid_results
  ):
    redis_key = self.__redis_key(requested_ingredients)
    try:
      self.redis_client.set(redis_key, json.dumps(valid_results))
    except:
      self.warning('\n[RecipePuppy] Is redis-server running?')

  def __redis_key(self, requested_ingredients):
    return 'recipepuppy___' + ''.join(sorted(requested_ingredients))

  def __requested_ingredients(self, message_text):
    message_text = self._strip_bot_name_activation_string(message_text)
    requested_ingredients = []
    tokens_raw = nltk.word_tokenize(message_text)
    tokens_raw = list(set(tokens_raw))
    tokens = []
    stop_tokens = [
        'with',
        'and',
        'the',
        'but',
        'a',
        ',',
        '.',
        '?',
        ';',
        '!',
        ':'
    ]
    for raw_token in tokens_raw:
      if raw_token not in stop_tokens:
        tokens.append(raw_token)
    for token in tokens:
      pos_tag = nltk.pos_tag([token])[0][1]
      if pos_tag in ['NN', 'NNS', 'NNP', 'NNPS']:
        requested_ingredients.append(token)
    return list(set(requested_ingredients))

  def __results_from_api(self, ingredients, pages):
    results = []
    for page in range(pages):
      try:
        response = self.__response_from_api(
            ingredients,
            page + 1
        )
        for result in response.json()['results']:
          results.append(result)
      except:
        continue
    return results

  def __response_from_api(self, ingredients, page):
    return requests.get(
        self.api_url,
        params={'i': ','.join(ingredients), 'p': str(page)}
    )

  def __valid_results(self, requested_ingredients, raw_results):
    valid_results = []
    httplib2_http = httplib2.Http()
    for raw_result in raw_results:
      try:
        raw_result_ingredient_list = raw_result['ingredients'].split(', ')
        ingredient_set_difference_size = len(
            set(requested_ingredients) & set(raw_result_ingredient_list)
        )
        if ingredient_set_difference_size != len(requested_ingredients):
          continue
        status = int(
            httplib2_http.request(raw_result['href'], 'HEAD')[0]['status']
        )
        if status == 200:
          valid_results.append(raw_result)
      except:
        continue
    return valid_results
