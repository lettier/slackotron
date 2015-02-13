#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron--An extensible slack bot.
'''

import time
import peewee
import database.database_manager


class Base(peewee.Model):
  class Meta:
    database = database.database_manager.DatabaseManager.db

  def __str__(self):
    return '%s()' % (self.__class__.__name__)


class Channel(Base):
  slack_name = peewee.CharField()
  slack_id = peewee.CharField(unique=True)
  is_direct = peewee.BooleanField(default=False)
  is_secure = peewee.BooleanField(default=True)

  def __str__(self):
    return '%s(%s %s %s %s)' % (
        self.__class__.__name__,
        self.slack_name,
        self.slack_id,
        self.is_direct,
        self.is_secure
    )

  def users(self):
    users = User.select().join(
        ChannelUserRelationship
    ).where(
        ChannelUserRelationship.channel == self
    )
    return users

  def direct_channel_user_name(self):
    if not self.is_direct:
        return ''
    if self.slack_name == 'USLACKBOT':
      return self.slack_name
    try:
      user = User.get(
          User.slack_id == self.slack_name
      )
      return user.slack_name
    except:
      return ''


class User(Base):
  slack_name = peewee.CharField()
  slack_id = peewee.CharField(unique=True)
  is_slackbot = peewee.BooleanField(default=False)

  def __str__(self):
    return '%s(%s %s %s)' % (
        self.__class__.__name__,
        self.slack_name,
        self.slack_id,
        self.is_slackbot
    )

  def channels(self):
    channels = Channel.select().join(
        ChannelUserRelationship
    ).where(
        ChannelUserRelationship.user == self
    )
    return channels


class Message(Base):
  text = peewee.CharField()
  slack_timestamp = peewee.CharField()
  channel = peewee.ForeignKeyField(Channel, related_name='messages')
  user = peewee.ForeignKeyField(User, related_name='messages')
  is_deleted = peewee.BooleanField(default=False)

  def __str__(self):
    return '%s(%s %s %s %s %s)' % (
        self.__class__.__name__,
        self.text,
        self.slack_timestamp,
        self.channel,
        self.user,
        self.is_deleted
    )


class Response(Base):
  text = peewee.CharField()
  generated_at = peewee.CharField()
  from_plugin = peewee.CharField(null=True)
  in_response_to = peewee.ForeignKeyField(
      Message,
      related_name='response',
      null=True
  )
  to_channel = peewee.ForeignKeyField(
      Channel,
      related_name='responses'
  )
  to_user = peewee.ForeignKeyField(User, related_name='responses')
  is_approved = peewee.BooleanField(default=False)
  is_sent = peewee.BooleanField(default=False)
  is_deleted = peewee.BooleanField(default=False)
  slack_timestamp = peewee.CharField(default='')

  def __str__(self):
    return '%s(%s %s %s %s %s %s %s %s %s %s)' % (
        self.__class__.__name__,
        self.text,
        self.generated_at,
        self.from_plugin,
        self.in_response_to,
        self.to_channel,
        self.to_user,
        self.is_approved,
        self.is_sent,
        self.is_deleted,
        self.slack_timestamp
    )

  def save(self, *args, **kwargs):
    if self.generated_at.__class__.__name__ == 'NoneType':
      self.generated_at = str('%.7f' % time.time())
    return super(Response, self).save(*args, **kwargs)


class ChannelUserRelationship(Base):
  '''
    Many-to-Many channel >-< user intermediary model.
  '''

  class Meta:
    indexes = ((('channel', 'user'), True),)
  channel = peewee.ForeignKeyField(Channel)
  user = peewee.ForeignKeyField(User)

  def __str__(self):
    return '%s(%s %s)' % (
        self.__class__.__name__,
        str(self.channel),
        str(self.user)
    )
