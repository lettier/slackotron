#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  SLACKOTRON

  An extensible Slack bot.
'''

import models
import plugins.plugin_base


class SlackScraper(plugins.plugin_base.PluginBase):
  activation_strings = [
      'scrape slack please'
  ]

  def _callback(self, channel, user, message):
    for channel in models.Channel.select():
      messages = self.slack.all_channel_messages(channel.slack_id)
      for raw_message in messages:
        text = raw_message['text']
        user = models.User.get(
            models.User.slack_id == raw_message['user']
        )
        try:
          models.Message.get(
              models.Message.timestamp == raw_message['timestamp'],
              models.Message.user == user,
              models.Message.channel == channel
          )
        except models.Message.DoesNotExist:
          models.Message.create(
              text=text,
              timestamp=raw_message['timestamp'],
              channel=channel,
              user=user
          )
    return 'Done.'
