import traceback
import slackotron_settings
import utilities
from scribe import Scribe
from locker import Locker
from models import Channel
from models import Response


class ChannelPublisher(Scribe, object):

  def __init__(self, **kwargs):
    self.channel_id = kwargs['channel_id']
    self.slack = kwargs['slack']
    self.profanity_filter_on = kwargs['profanity_filter_on']
    self.bot_name = kwargs['bot_name']
    self.bot_slack_id = kwargs['bot_slack_id']
    self.bot_icon_emoji = kwargs['bot_icon_emoji']
    self.bot_icon_url = kwargs['bot_icon_url']

    self.locker = Locker()

  def step(self, *args, **kwargs):
    try:
      is_approved = True
      is_sent = False
      is_deleted = False
      self.channel = Channel.get(
          Channel.id == self.channel_id
      )
      if self.channel.is_subscribed is False:
        return None
      for response in list(Response.select().where(
          (Response.is_approved == is_approved) &
          (Response.is_sent == is_sent) &
          (Response.is_deleted == is_deleted) &
          (Response.to_channel == self.channel)
      )):
        response_text = response.text
        response_text = self.__format_response_text(
            response.to_user,
            response_text
        )
        if self.profanity_filter_on is True:
          response_text = utilities.scrub_profanity(response_text)
        query_params = {
            'channel': self.channel.slack_id,
            'text': response_text,
            'parse': 'full',
            'linknames': 1,
            'unfurl_links': 'true',
            'unfult_media': 'true',
            'username': self.bot_name
        }
        if hasattr(slackotron_settings, 'BOT_ICON_URL'):
          query_params['icon_url'] = self.bot_icon_url
        if hasattr(slackotron_settings, 'BOT_ICON_EMOJI'):
          query_params['icon_emoji'] = self.bot_icon_emoji
        g = self.locker.make_lock_generator('response')
        try:
          g.next()
          response_json = self.slack.send_message(query_params)
          if response_json is not None:
            response.text = response_text
            response.is_sent = True
            response.slack_timestamp = response_json['timestamp']
            response.save()
            self.info(response)
        except Exception as e:
          self.error(e)
        finally:
          g.next()
    except Exception as e:
      self.error(e.__class__.__name__)
      self.error(e)
      traceback.print_exc()

  def __format_response_text(self, user, response_text):
    if response_text.__class__.__name__ == 'str':
      response_text = response_text.decode('utf-8', 'ignore')
    return u''.join([
        u'@',
        user.slack_name,
        u', ',
        response_text
    ])
