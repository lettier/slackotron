import time
import traceback
import slackotron_settings
import decorators
from scribe import Scribe
from models import Channel
from models import User
from models import Message


class ChannelSubscriber(Scribe, object):

  def __init__(self, **kwargs):
    self.channel_id = kwargs['channel_id']
    self.slack = kwargs['slack']
    self.check_slack_interval = 1.0
    self.checked_slack_at = time.time() + self.check_slack_interval

  @decorators.rabbitmq_publish(
      host=slackotron_settings.RABBITMQ_HOST_URL,
      exchange=slackotron_settings.PLUGIN_RABBITMQ_EXCHANGE_NAME,
      exchange_type='fanout',
      routing_key=slackotron_settings.PLUGIN_RABBITMQ_ROUTING_KEY
  )
  def step(self, *args, **kwargs):
    try:
      self.channel = Channel.get(
          Channel.id == self.channel_id
      )
      if self.channel.is_subscribed is False:
        return []
      current_time = time.time()
      rmq_messages = []
      if (current_time - self.checked_slack_at) > self.check_slack_interval:
        self.checked_slack_at = current_time
        slack_raw_messages = self.slack.channel_messages_since(
            self.channel.slack_id,
            30
        )
        for slack_raw_message in slack_raw_messages:
          user, message, new = self._process_slack_raw_message(
              slack_raw_message
          )
          if not new:
            continue
          self.info(message)
          rmq_messages.append(
              {
                  'channel_id': self.channel.get_id(),
                  'user_id': user.get_id(),
                  'message_id': message.get_id()
              }
          )
      return rmq_messages
    except Exception as e:
      self.error(e)
      traceback.print_exc()
      return []

  def _process_slack_raw_message(self, slack_raw_message):
    user, message, new = None, None, False
    try:
      user = User.get(
          User.slack_id == slack_raw_message['user']
      )
      try:
        message = Message.get(
            Message.slack_timestamp == slack_raw_message['timestamp'],
            Message.user == user,
            Message.channel == self.channel
        )
        new = False
      except Message.DoesNotExist:
        message = Message.create(
            text=slack_raw_message['text'],
            slack_timestamp=slack_raw_message['timestamp'],
            channel=self.channel,
            user=user
        )
        new = True
    except Exception as e:
      self.error(e)
    finally:
      return user, message, new
