#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import time
import datetime
import peewee
import database.database_manager


class Base(peewee.Model):
  class Meta:
    database = database.database_manager.DatabaseManager.database

  def __str__(self):
    strr = [u'(%s' % self._class_name()]
    fields = self._fields()
    if len(fields) > 0:
      strr += [u'{']
      class_dict = self.__class__.__dict__
      for field in fields:
        strr += [
            u':%s %s' % (field, class_dict[field].__get__(self))
        ]
      strr += [u'})']
    else:
      strr += [u')']
    return u' '.join(strr)

  def timestamp_field_to_string(self, field):
    try:
      return datetime.datetime.fromtimestamp(
          float(field)
      ).strftime('%m-%d %H:%M:%S')
    except:
      return str(field)

  @classmethod
  def database(cls):
    return cls._meta.database

  @classmethod
  def _class_name(cls):
    return str(cls.__name__)

  @classmethod
  def _fields(cls):
    d = cls.__dict__
    fields = [
        str(k) for k, v in d.items() if
        'FieldDescriptor' in str(v) and k != 'id'
    ]
    return sorted(fields)


class Channel(Base):
  slack_name = peewee.CharField()
  slack_id = peewee.CharField(unique=True)
  is_direct = peewee.BooleanField(default=False)
  is_secure = peewee.BooleanField(default=True)
  is_subscribed = peewee.BooleanField(default=False)

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

  def slack_timestamp_to_string(self):
    return self.timestamp_field_to_string(
        self.slack_timestamp
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

  def save(self, *args, **kwargs):
    if self.generated_at.__class__.__name__ == 'NoneType':
      self.generated_at = str('%.7f' % time.time())
    return super(Response, self).save(*args, **kwargs)

  def generated_at_to_string(self):
    return self.timestamp_field_to_string(
        self.generated_at
    )


class ChannelUserRelationship(Base):
  '''
    Many-to-Many channel >-< user intermediary model.
  '''

  class Meta:
    indexes = ((('channel', 'user'), True),)

  channel = peewee.ForeignKeyField(Channel)
  user = peewee.ForeignKeyField(User)
