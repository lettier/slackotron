#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import os
import sys
import nltk
import nltk.parse.stanford
import nltk.tag.stanford
import slackotron_settings

os.environ['JAVA_HOME'] = slackotron_settings.JAVA_HOME


class TypeChecker(object):
  '''
    TypeChecker(object)
  '''

  def __init__(self):
    pass

  def is_blank(self, _object):
    '''
      is_blank(_object)
    '''
    if self.__is_type(_object, 'NoneType'):
      return True
    else:
      return len(_object) == 0

  def is_tree(self, _object):
    '''
      is_tree(_object)
    '''
    return self.__is_type(_object, 'Tree')

  def is_list(self, _object):
    '''
      is_tree(_object)
    '''
    return self.__is_type(_object, 'list')

  def is_string(self, _object):
    '''
      is_tree(_object)
    '''
    return self.__is_type(_object, 'str') or self.__is_type(_object, 'unicode')

  def __is_type(self, _object, _type):  # pylint:disable=no-self-use
    '''
      __is_type(_object, _type)
    '''
    return _object.__class__.__name__ == _type


class StanfordNER(TypeChecker, object):
  '''
    StanfordNER(TypeChecker, object)
  '''
  stanford_ner_location = slackotron_settings.STANFORD_NER_LOCATION
  stanford_ner_classifier_location = \
      slackotron_settings.STANFORD_NER_CLASSIFIER_LOCATION

  def __init__(self):
    self.sner = nltk.tag.stanford.NERTagger(
        self.stanford_ner_classifier_location,
        self.stanford_ner_location
    )

  def organizations(self, sentence, group=False):
    return self.__named_entities(sentence, u'ORGANIZATION', group)

  def locations(self, sentence, group=False):
    return self.__named_entities(sentence, u'LOCATION', group)

  def people(self, sentence, group=False):
    return self.__named_entities(sentence, u'PERSON', group)

  def __named_entities(self, sentence, _type, group=False):
    if not self.is_string(_type):
      return []
    tags = self.__tags(sentence)
    if self.is_blank(tags):
      return []
    if group is False:
      try:
        return [x[0] for x in tags if x[1] == _type]
      except Exception:
        return []
    elif group is True:
      try:
        named_entities = []
        last_type = tags[0][1]
        group = []
        for tag in tags:
          if last_type != tag[1]:
            if len(group) > 0:
              named_entities.append(' '.join(group))
              group = []
          if _type == tag[1]:
            group.append(tag[0])
          last_type = tag[1]
        if len(group) > 0:
          named_entities.append(' '.join(group))
        return named_entities
      except:
        return []

  def __tokenize(self, _string):
    return nltk.wordpunct_tokenize(_string)

  def __tags(self, sentence):
    if self.is_blank(sentence):
      return []
    tokens = self.__tokenize(sentence)
    if not self.is_list(tokens):
      return []
    tags = self.sner.tag(tokens)
    return tags


class StanfordParser(TypeChecker, object):
  stanford_parser_location = slackotron_settings.STANFORD_PARSER_LOCATION
  stanford_parser_models_location = \
      slackotron_settings.STANFORD_PARSER_MODELS_LOCATION

  def __init__(self):
    self.sp = nltk.parse.stanford.StanfordParser(
        self.stanford_parser_location,
        self.stanford_parser_models_location
    )

  def tree(self, sentence):
    try:
      tree = self.sp.raw_parse(sentence)
      return tree[0]
    except Exception:
      return None

  def trees(self, sentences):
    if self.is_blank(sentences):
      return None
    trees = self.sp.raw_parse_sents(sentences)
    return trees

  def tokens(self, sentence_s):
    try:
      if self.is_blank(sentence_s):
        return None
      if self.is_list(sentence_s):
        trees = self.trees(sentence_s)
        tokens = [x.leaves() for x in trees]
        return tokens
      elif self.is_string(sentence_s):
        tree = self.tree(sentence_s)
        tokens = tree.leaves()
        return tokens
    except Exception:
      return None

  def untokenize(self, tokens, original_sentence):
    if self.is_blank(tokens):
      return None
    if not self.is_list(tokens):
      return None
    if self.is_blank(original_sentence):
      return None
    if not self.is_string(original_sentence):
      return None
    if len(tokens) == 1:
      return tokens[0]
    left_token_map = {
        '`': "'",
        '``': '"',
        '-LRB-': '(',
        '-LCB-': '{',
        '-LSB-': '[',
    }
    right_token_map = {
        "'": "'",
        "''": '"',
        '-RRB-': ')',
        '-RCB-': '}',
        '-RSB-': ']'
    }
    mapped_tokens = []
    for token in tokens:
      if token in left_token_map.keys():
        token = left_token_map[token]
      elif token in right_token_map.keys():
        token = right_token_map[token]
      mapped_tokens.append(token)

    def token_indexes(tokens, sentence, left=True):
      indexes = []
      i = 0
      j = i
      while True:
        if left:
          j = original_sentence[i:].find(mapped_tokens[0])
        else:
          j = original_sentence[
              0:len(original_sentence) - i
          ].rfind(mapped_tokens[-1])
        if j == -1:
          break
        i = i + j + 1
        indexes.append(i - 1)
      return indexes
    left_token_indexes = token_indexes(mapped_tokens, original_sentence)
    right_token_indexes = token_indexes(
        mapped_tokens,
        original_sentence,
        False
    )
    if len(left_token_indexes) == 0 or len(right_token_indexes) == 0:
      return ' '.join(mapped_tokens)
    if len(left_token_indexes) == 1 and len(right_token_indexes) == 1:
      return original_sentence[
          left_token_indexes[0]:
          right_token_indexes[0] + len(mapped_tokens[-1])
      ]
    else:
      lowest_difference = sys.maxint
      best_indexes = [left_token_indexes[0], right_token_indexes[-1]]
      done_searching = False
      for left_token_index in left_token_indexes:
        if done_searching is True:
          break
        for right_token_index in right_token_indexes[::-1]:
          if right_token_index <= left_token_index:
            done_searching = True
            break
          test = self.tokens(
              original_sentence[
                  left_token_index:
                  right_token_index + len(mapped_tokens[-1])
              ]
          )
          delta = abs(len(test) - len(mapped_tokens))
          if delta < lowest_difference:
            if delta == 0:
              done_searching = True
            lowest_difference = delta
            best_indexes[0] = left_token_index
            best_indexes[1] = right_token_index
      return original_sentence[
          best_indexes[0]:best_indexes[1] + len(mapped_tokens[-1])
      ]

  def parts_of_speech(self, sentence_s):
    '''
      parts_of_speech(sentence_s)
    '''
    if self.is_blank(sentence_s):
      return None
    pos = None
    if self.is_list(sentence_s):
      trees = self.trees(sentence_s)
      pos = [[y[1] for y in x] for x in [x.pos() for x in trees]]
    elif self.is_string(sentence_s):
      tree = self.tree(sentence_s)
      pos = [x[1] for x in tree.pos()]
    return pos

  def prepositional_phrases(self, sentence_s, flatten=False):
    return self._phrases(sentence_s, 'PP', flatten)

  def noun_phrases(self, sentence_s, flatten=False):
    return self._phrases(sentence_s, 'NP', flatten)

  def verb_phrases(self, sentence_s, flatten=False):
    return self._phrases(sentence_s, 'VP', flatten)

  def _phrases(self, sentence_s, _type, flatten=False):
    '''
      _phrases(sentence_s, _type, flatten=False)
    '''
    try:
      if self.is_blank(sentence_s):
        return None
      phrases = None
      if self.is_list(sentence_s):
        trees = self.trees(sentence_s)
        phrases = [self._extract_phrases(x, _type) for x in trees]
        if flatten is True:
          temp = []
          for i, phrase in enumerate(phrases):
            for char in phrase:
              temp.append(self.untokenize(char, sentence_s[i]))
          phrases = temp
      elif self.is_string(sentence_s):
        tree = self.tree(sentence_s)
        phrases = self._extract_phrases(tree, _type)
        if flatten is True:
          temp = []
          for phrase in phrases:
            temp.append(self.untokenize(phrase, sentence_s))
          phrases = temp
      return phrases
    except OSError:
      return None

  def _extract_phrases(self, tree, _type):
    if not self.is_tree(tree):
      return None
    phrases = []
    for subtree in tree.subtrees():
      if subtree.label() == _type:
        phrases.append(subtree.leaves())
    return phrases
