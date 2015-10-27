#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import models
import plugins.plugin_base


class CleanUp(plugins.plugin_base.PluginBase):
  activation_strings = [
      'clean up after me',
      'clean up after yourself',
      'clean up after yourself and me',
      'nuke me'
  ]

  def _callback(self, channel, user, message):
    is_deleted = False

    if self.activation_strings[3].lower() in message.text.lower():
      messages = models.Message.select().where(
          models.Message.user == user,
          models.Message.is_deleted == is_deleted
      )
      self.__delete_messages(messages)

    delete_messages = False
    delete_responses = False
    if self.activation_strings[2].lower() in message.text.lower():
      delete_messages = True
      delete_responses = True
    elif self.activation_strings[1].lower() in message.text.lower():
      delete_responses = True
    elif self.activation_strings[0].lower() in message.text.lower():
      delete_messages = True

    if delete_responses is True:
      is_sent = True
      responses = models.Response.select().where(
          (models.Response.is_sent == is_sent) &
          (models.Response.to_channel == channel) &
          (models.Response.is_deleted == is_deleted)
      )
      self.__delete_responses(responses)
    if delete_messages is True:
      messages = models.Message.select().where(
          models.Message.user == user,
          models.Message.channel == channel,
          models.Message.is_deleted == is_deleted
      )
      self.__delete_messages(messages)

    return None

  def __delete_messages(self, messages):
    message_ids = []
    for message in messages:
      self.__log_deletion(message)
      self.slack.delete_message(
          message.channel.slack_id,
          message.slack_timestamp
      )
      message_ids.append(message.get_id())
    delete_messages = models.Message.update(is_deleted=True).where(
        models.Message.id << message_ids
    )
    delete_messages.execute()

  def __delete_responses(self, responses):
    response_ids = []
    for response in responses:
      self.__log_deletion(response)
      self.slack.delete_message(
          response.to_channel.slack_id,
          response.slack_timestamp
      )
      response_ids.append(response.get_id())
    delete_reponses = models.Response.update(is_deleted=True).where(
        models.Response.id << response_ids
    )
    delete_reponses.execute()

  def __log_deletion(self, model):
    if not hasattr(model, 'text'):
      return

    text = model.text
    if not isinstance(text, str) and not isinstance(text, type(u'')):
      text = u''
    if len(text) == 0:
      return

    self.info(u'Deleting ' + model.__class__.__name__ + u': ' + text)
