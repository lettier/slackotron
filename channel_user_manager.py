from scribe import Scribe
from models import Channel
from models import User
from models import ChannelUserRelationship
from slackotron_thread import SlackotronThread
from channel_subscriber import ChannelSubscriber
from channel_publisher import ChannelPublisher


class ChannelUserManager(Scribe, object):

  def __init__(self, **kwargs):
    self.database_manager = kwargs['database_manager']
    self.slack = kwargs['slack']
    self.profanity_filter_on = kwargs['profanity_filter_on']
    self.bot_name = kwargs['bot_name']
    self.bot_slack_id = kwargs['bot_slack_id']
    self.bot_icon_emoji = kwargs['bot_icon_emoji']
    self.bot_icon_url = kwargs['bot_icon_url']
    self.channel_id_to_name_map = self.slack.channel_id_to_name_map
    self.channel_name_to_id_map = self.slack.channel_name_to_id_map
    self.thread = None

  def start(self):
    self._initialize_channels_and_users()
    self._get_or_create_slackotron_user()
    self._scrub_dead_channels_and_users()
    self.thread = ChannelUserManagerThread(
        **{
            'slack': self.slack,
            'profanity_filter_on': self.profanity_filter_on,
            'bot_name': self.bot_name,
            'bot_slack_id': self.bot_slack_id,
            'bot_icon_emoji': self.bot_icon_emoji,
            'bot_icon_url': self.bot_icon_url
        }
    )
    self.thread.daemon = False
    self.thread.start()

  def stop(self):
    self.thread.exit = True

  def _initialize_channels_and_users(self):
    self.info('Loading channels and users...')
    self.known_slack_channel_ids = []
    self.known_slack_user_ids = []
    with self.database_manager.transaction():
      for k, v in self.channel_id_to_name_map.items():
        is_direct = True if k.startswith('D0') else False
        try:
          channel = Channel.get(
              Channel.slack_id == k
          )
          channel.slack_name = v
          channel.is_direct = is_direct
          channel.save()
        except Channel.DoesNotExist:
          is_subscribed = True if v == 'USLACKBOT' else False
          channel = Channel.create(
              slack_name=v,
              slack_id=k,
              is_direct=is_direct,
              is_subscribed=is_subscribed
          )
        except Exception as e:
          self.error(e)
          continue
        self.known_slack_channel_ids.append(
            channel.slack_id
        )
        self.info(channel)
        channel_members = self.slack.channel_members(channel.slack_name)
        for channel_member in channel_members:
          try:
            user = User.get(
                User.slack_id == channel_member[0]
            )
            user.slack_name = channel_member[1]
            user.save()
          except User.DoesNotExist:
            user = User.create(
                slack_name=channel_member[1],
                slack_id=channel_member[0]
            )
          except Exception as e:
            self.error(e)
          try:
            ChannelUserRelationship.create(
                channel=channel,
                user=user
            )
          except:
            pass
          self.known_slack_user_ids.append(
              user.slack_id
          )
          self.info(user)

  def _scrub_dead_channels_and_users(self):
    Channel.delete().where(
        ~(Channel.slack_id << self.known_slack_channel_ids)
    )
    User.delete().where(
        ~(User.slack_id << self.known_slack_user_ids)
    )

  def _get_or_create_slackotron_user(self):
    try:
      self.slackotron_user = User.get(
          User.slack_name == self.bot_name,
          User.slack_id == self.bot_slack_id
      )
    except User.DoesNotExist:
      self.slackotron_user = User.create(
          slack_name=self.bot_name,
          slack_id=self.bot_slack_id
      )
    except Exception as e:
      self.error(e)
      return None
    self.info(self.slackotron_user)


class ChannelUserManagerThread(SlackotronThread):

  def __init__(self, *args, **kwargs):
    super(ChannelUserManagerThread, self).__init__(*args, **kwargs)
    self.profanity_filter_on = kwargs['profanity_filter_on']
    self.bot_name = kwargs['bot_name']
    self.bot_slack_id = kwargs['bot_slack_id']
    self.bot_icon_emoji = kwargs['bot_icon_emoji']
    self.bot_icon_url = kwargs['bot_icon_url']
    self.subscribers = {}
    self.publishers = {}

  def _load_unload(self):
    self._load_subscribers()
    self._load_publishers()
    self._unload_subscribers()
    self._unload_publishers()

  def _load_subscribers(self):
    self._load(self.subscribers, ChannelSubscriber)

  def _load_publishers(self):
    self._load(self.publishers, ChannelPublisher)

  def _load(self, dictt, Classs):
    is_subscribed = True
    for channel in list(Channel.select().where(
        (Channel.is_subscribed == is_subscribed)
    )):
      if channel.slack_id not in dictt:
        dictt[channel.slack_id] = Classs(
            **{
                'channel_id': channel.id,
                'slack': self.slack,
                'profanity_filter_on': self.profanity_filter_on,
                'bot_name': self.bot_name,
                'bot_slack_id': self.bot_slack_id,
                'bot_icon_emoji': self.bot_icon_emoji,
                'bot_icon_url': self.bot_icon_url
            }
        )

  def _unload_subscribers(self):
    self._unload(self.subscribers)

  def _unload_publishers(self):
    self._unload(self.publishers)

  def _unload(self, dictt):
    is_subscribed = False
    for channel in list(Channel.select().where(
        (Channel.is_subscribed == is_subscribed)
    )):
      if channel.slack_id in self.subscribers:
        del dictt[channel.slack_id]

  def _run_once(self):
    self._load_unload()
    for k, v in self.subscribers.items():
      v.step()
    for k, v in self.publishers.items():
      v.step()
