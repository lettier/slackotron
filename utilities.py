#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import string
import requests


def clean_string(dirty_string):
  return dirty_string.translate(
      string.maketrans('', ''),
      string.punctuation
  ).lower()


def scrub_profanity(dirty_string):
  params = {
      'text': dirty_string,
      'add': 'chinaman,dick,damn'
  }
  response = requests.get(
      'http://www.purgomalum.com/service/json',
      params=params
  )
  if 'result' in response.json():
    return response.json()['result']
  else:
    return ''


def jaccard_similarity(string1, string2):
  string1 = clean_string(string1)
  string2 = clean_string(string2)
  set1 = set(string1.split(' '))
  set2 = set(string2.split(' '))
  return len(set1 & set2) / float(len(set1 | set2))
