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
  ]

  def _callback(self, channel, user, message):
    if self.activation_strings[0].lower() in message.text.lower():
      messages = models.Message.select().where(
          models.Message.user == user,
          models.Message.channel == channel
      )
      self.__delete_messages(messages)
    elif self.activation_strings[1].lower() in message.text.lower():
      is_sent = True
      responses = models.Response.select().where(
          (models.Response.is_sent == is_sent) &
          (models.Response.to_channel == channel)
      )
      self.__delete_responses(responses)
    return None

  def __delete_messages(self, messages):
    message_ids = []
    for message in messages:
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
      self.slack.delete_message(
          response.to_channel.slack_id,
          response.slack_timestamp
      )
      response_ids.append(response.get_id())
    delete_reponses = models.Response.update(is_deleted=True).where(
        models.Response.id << response_ids
    )
    delete_reponses.execute()
