#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import models
import plugins.plugin_base


class SlackScraper(plugins.plugin_base.PluginBase):
  activation_strings = [
      'scrape slack please'
  ]

  def _callback(self, channel, user, message):
    with models.Channel.database().transaction():
      for channel in models.Channel.select():
        raw_slack_messages = self.slack.all_channel_messages(channel.slack_id)
        for raw_slack_message in raw_slack_messages:
          text = raw_slack_message['text']
          user = models.User.get(
              models.User.slack_id == raw_slack_message['user']
          )
          try:
            models.Message.get(
                models.Message.slack_timestamp ==
                raw_slack_message['timestamp'],
                models.Message.user == user,
                models.Message.channel == channel
            )
          except models.Message.DoesNotExist:
            models.Message.create(
                text=text,
                slack_timestamp=raw_slack_message['timestamp'],
                channel=channel,
                user=user
            )
    return 'Done.'
