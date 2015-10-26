#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import re
import random
import requests
import chatty_kathy_settings
import plugins.plugin_base
import stanford_nlp_service
from bs4 import BeautifulSoup


class ChattyKathy(plugins.plugin_base.PluginBase):
  activation_strings = [
  ]
  activation_probability = chatty_kathy_settings.ACTIVATION_PROBABILITY
  twitter_search_url = chatty_kathy_settings.TWITTER_SEARCH_URL

  def _callback(self, channel, user, message):
    if random.randrange(100) >= self.activation_probability:
      return None
    try:
      self.redis_client.get('')
    except:
      self.warning('Is redis-server running?')
      return None
    sp = stanford_nlp_service.StanfordParser()
    noun_phrases = sp.noun_phrases(message.text)
    if noun_phrases is None:
      return None
    if len(noun_phrases) > 0:
      self.info('Noun phrases %s.' % noun_phrases)
      noun_phrase = max(noun_phrases, key=len)
      try:
        noun_phrase = sp.untokenize(noun_phrase, message.text)
      except OSError:
        return None
      if noun_phrase is not None:
        self.info('Noun phrase %s.' % noun_phrase)
        redis_key = self._redis_key(noun_phrase)
        redis_set_member = self.redis_client.srandmember(redis_key)
        if redis_set_member is not None:
          return redis_set_member
        search_results = self._twitter_search_results(noun_phrase)
        if search_results != '':
          conversation_links = self._twitter_conversation_links(
              search_results
          )
          if len(conversation_links) > 0:
            conversation_replies = self._twitter_conversation_replies(
                conversation_links
            )
            if len(conversation_replies) > 0:
              redis_key = self._redis_key(noun_phrase)
              self.redis_client.sadd(redis_key, *conversation_replies)
              return random.choice(conversation_replies)
    return None

  def _twitter_conversation_replies(self, conversation_links):
    replies = []
    for conversation_link in conversation_links:
      result = requests.get('https://twitter.com' + conversation_link)
      soup = BeautifulSoup(
          result.text
      )
      raw_replies = soup.find_all('div', {'data-component-context': 'replies'})
      for raw_reply in raw_replies:
        p_tags = raw_reply.find_all(
            'p',
            class_='tweet-text'
        )
        for p_tag in p_tags:
          if p_tag.contents[-1].__class__.__name__ != 'Tag':
            reply = p_tag.contents[-1].encode('utf-8', 'ignore')
            reply = self._strip_at_names(reply)
            replies.append(reply)
    return list(set(replies))

  def _twitter_conversation_links(self, raw_page):
    soup = BeautifulSoup(raw_page)
    a_tags = soup.select(
        'a.details.with-icn.js-details'
    )
    conversation_links = []
    for a_tag in a_tags:
      span_tags = a_tag.select(
          'span.expand-stream-item.js-view-details'
      )
      for span_tag in span_tags:
        if span_tag.text == 'View conversation':
          conversation_links.append(a_tag['href'])
    if len(conversation_links) == 0:
      self.warning('Conversation links were empty.')
    return conversation_links

  def _twitter_search_results(self, query):
    try:
      result = requests.get(
          self.twitter_search_url,
          params={
              'f': 'realtime',
              'q': '"' + query + '" filter:replies'
          }
      )
      return result.text
    except Exception as e:
      self.error(e)
      return ''

  def _strip_at_names(self, _string):
    _string = re.sub(r'@\S*', '', _string, flags=re.U).strip()
    _string = re.sub(r'\s\s', ' ', _string, flags=re.U).strip()
    return _string

  def _redis_key(self, string):
    return 'slackotron:chatty.kathy:' + '.'.join(string.lower().strip())
