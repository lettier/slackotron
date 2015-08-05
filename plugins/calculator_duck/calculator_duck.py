#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import requests
# import nltk
import stanford_nlp_service
import calculator_duck_settings
import plugins.plugin_base


class CalculatorDuck(plugins.plugin_base.PluginBase):
  self._safe_set_config_from_env(calculator_duck_settings)
  api_url = calculator_duck_settings.DUCKDUCKGO_API_URL
  activation_strings = [
      'what is',
      'give me the answer to',
      'calculate for me'
  ]
  activation_threshold = 0.5

  def _callback(self, channel, user, message):
    query = self.__mathematical_expression(message.text.lower())
    if query is None:
      return None
    answer = self.__api_answer(query)
    if answer is None or answer == '':
      return 'I do not know what ' + query + ' is.'
    else:
      return answer

  def __mathematical_expression(self, message_text):
    message_text = self._strip_bot_name_activation_string(message_text)
    sp = stanford_nlp_service.StanfordParser()
    noun_phrases = sp.noun_phrases(message_text)
    if noun_phrases is None:
      return None
    if len(noun_phrases) > 0:
      noun_phrase = max(noun_phrases, key=len)
      noun_phrase = sp.untokenize(noun_phrase, message_text)
      if noun_phrase is not None:
        return noun_phrase
    return None

  def __api_answer(self, query):
    answer = None
    try:
      answer = self.__response_from_api(query).json()['Answer']
    except:
      pass
    return answer

  def __response_from_api(self, query):
    response = None
    try:
      response = requests.get(
          self.api_url,
          params={
              'q': str(query),
              'format': 'json',
              'no_html': '1'
          }
      )
    except:
      pass
    return response
