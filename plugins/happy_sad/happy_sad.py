#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  SLACKOTRON

  An extensible Slack bot.
'''

import plugins.plugin_base
import happy_sad_settings
from pattern.en import sentiment


class HappySad(plugins.plugin_base.PluginBase):
  sentiment_subjectivity_threshold = \
      happy_sad_settings.SENTIMENT_SUBJECTIVITY_THRESHOLD
  positive_responses = \
      sorted(happy_sad_settings.POSITIVE_RESPONSES, key=lambda tup: tup[0])
  negative_responses = \
      sorted(happy_sad_settings.NEGATIVE_RESPONSES, key=lambda tup: tup[0])
  activation_strings = [
  ]

  def _callback(self, channel, user, message):
    message_text_sentiment = sentiment(message.text.lower())
    if message_text_sentiment[1] > self.sentiment_subjectivity_threshold:
      if message_text_sentiment[0] > 0.0:
        return self._response(
            message_text_sentiment[0],
            self.positive_responses
        )
      elif message_text_sentiment[0] < 0.0:
        return self._response(
            message_text_sentiment[0],
            self.negative_responses
        )
    return None

  def _response(self, sentiment, possible_responses):
    index = -1
    for i, possible_response in enumerate(possible_responses):
      if abs(sentiment) >= abs(possible_response[0]):
        index = i
      else:
        break
    if index != -1:
      return possible_responses[index][1]
    else:
      return None
