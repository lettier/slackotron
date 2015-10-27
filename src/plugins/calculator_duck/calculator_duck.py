#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import requests
# import nltk
import lib.stanford_nlp
import calculator_duck_settings
import plugins.plugin_base


class CalculatorDuck(plugins.plugin_base.PluginBase):
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
    message_text = self._clean_up_message_text(message_text)
    stanford_parser = lib.stanford_nlp.StanfordParser()
    noun_phrases = stanford_parser.noun_phrases(message_text)
    if noun_phrases is None:
      return None
    if len(noun_phrases) > 0:
      noun_phrase = max(noun_phrases, key=len)
      noun_phrase = stanford_parser.untokenize(
          noun_phrase,
          message_text
      )
      if noun_phrase is not None:
        return noun_phrase
    return None

  def __api_answer(self, query):
    answer = None
    try:
      answer = self.__response_from_api(query).json()['Answer']
    except Exception:
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
    except Exception:
      pass
    return response
