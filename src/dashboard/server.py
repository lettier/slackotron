#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2016.

  http://www.lettier.com/

  Slackotron
'''

import os

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))

import sys  # noqa

sys.path.insert(0, MODULE_PATH.split('/dashboard')[0])

import slackotron_settings  # noqa
import models  # noqa
from flask import Flask  # noqa
from flask import render_template  # noqa
from flask import jsonify  # noqa
from flask import request  # noqa

APPLICATION = Flask(__name__)
APPLICATION.config.from_object(__name__)

'''
  HOOKS
'''


@APPLICATION.before_request
def _db_connect():
  models.Base.database().connect()


@APPLICATION.teardown_request
def _db_close(exc):
  database = models.Base.database()
  if not database.is_closed():
    database.close()


'''
  PAGES
'''


@APPLICATION.route('/')
def index_page():
  direct_channels = get_direct_channels()
  channels = get_channels()
  users = get_users()
  return render_template(
    'index.html',
    direct_channels=direct_channels,
    channels=channels,
    channel_count=total_channel_count(direct_channels, channels),
    users=users,
    user_count=user_count(users),
    active_page_name='/'
  )


@APPLICATION.route('/pending_responses')
def pending_responses_page():
  pending_responses = []
  is_approved = False
  is_sent = False
  is_deleted = False
  for pending_response in models.Response.select().where(
    (models.Response.is_approved == is_approved) &
    (models.Response.is_sent == is_sent) &
    (models.Response.is_deleted == is_deleted)
  ).order_by(models.Response.generated_at.desc()):
    pending_responses.append(pending_response)
  pending_response_count = len(pending_responses)
  return render_template(
    'pending_responses.html',
    pending_responses=pending_responses,
    pending_response_count=pending_response_count,
    active_page_name='pending_responses'
  )


@APPLICATION.route('/channels')
def channels_page():
  direct_channels = get_direct_channels()
  channels = get_channels()
  return render_template(
    'channels.html',
    direct_channels=direct_channels,
    channels=channels,
    channel_count=total_channel_count(direct_channels, channels),
    active_page_name='channels'
  )


@APPLICATION.route('/post_a_message')
def post_a_message_page():
  direct_channels = get_direct_channels()
  channels = get_channels()
  users = get_users()
  return render_template(
    'post_a_message.html',
    direct_channels=direct_channels,
    channels=channels,
    channel_count=total_channel_count(direct_channels, channels),
    users=users,
    active_page_name='post_a_message'
  )


'''
  API
'''


@APPLICATION.route(
  '/responses',
  methods=['POST']
)
def create_response_api():
  params = request.json
  if params is None:
    return jsonify(success=False, message='No params given.'), 400
  try:
    channel = models.Channel.get(
      models.Channel.id == params['to_channel_id']
    )
    if channel.is_subscribed is False:
      return jsonify(success=False, message='Not subscribed to channel.'), 400
  except Exception:
    return jsonify(success=False, message='Channel not found.'), 400
  try:
    user = models.User.get(
      models.User.id == params['to_user_id']
    )
  except Exception:
    return jsonify(success=False, message='User not found.'), 400
  if 'text' not in params:
    return jsonify(success=False, message='Text parameter required.'), 400
  if params['text'] is None or params['text'] == '':
    return jsonify(success=False, message='Text parameter was blank.'), 400
  text = u'[ADMIN] ' + params['text']
  response = models.Response.create(
    text=text,
    to_channel=channel,
    to_user=user,
    is_approved=True,
    is_sent=False
  )
  return jsonify(success=True, message='Created.', response=response._data)


@APPLICATION.route(
  '/pending_responses/<pending_response_id>',
  methods=['PUT']
)
def approve_pending_response_api(pending_response_id):
  params = request.json
  if params is None:
    return jsonify(success=False, message='No params given.'), 400
  try:
    response = models.Response.get(
      models.Response.id == pending_response_id
    )
    if 'is_approved' in params:
      response.is_approved = params['is_approved']
      response.save()
  except models.Response.DoesNotExist as e:
    return jsonify(success=False, message=str(e)), 404
  return jsonify(
    success=True,
    message='Updated.',
    pending_response=response._data
  )


@APPLICATION.route(
  '/pending_responses/<pending_response_id>',
  methods=['DELETE']
)
def delete_pending_response_api(pending_response_id):
  try:
    response = models.Response.get(
      models.Response.id == pending_response_id
    )
    response.is_deleted = True
    response.save()
  except models.Response.DoesNotExist as e:
    return jsonify(success=False, message=str(e)), 404
  return jsonify(
      success=True,
      message='Deleted.',
      pending_response=response._data
  )


@APPLICATION.route(
  '/channels/<channel_id>',
  methods=['PUT']
)
def update_channel_security_api(channel_id):
  params = request.json
  if params is None:
    return jsonify(success=False, message='No params given.'), 400
  try:
    channel = models.Channel.get(
      models.Channel.id == channel_id
    )
    if 'is_secure' in params:
      channel.is_secure = params['is_secure']
      channel.save()
    elif 'is_subscribed' in params:
      channel.is_subscribed = params['is_subscribed']
      channel.save()
  except models.Channel.DoesNotExist as error:
    return jsonify(success=False, message=str(error)), 404
  return jsonify(success=True, message='Updated.', channel=channel._data)

'''
  HELPER METHODS
'''


def get_direct_channels():
  direct_channels = []
  is_direct = True
  for direct_channel in models.Channel.select().where(
    models.Channel.is_direct == is_direct
  ).order_by(
    models.Channel.slack_name
  ):
    if direct_channel.direct_channel_user_name() != '':
      direct_channels.append(direct_channel)
  return direct_channels


def get_channels():
  channels = []
  is_direct = False
  for channel in models.Channel.select().where(
    models.Channel.is_direct == is_direct
  ).order_by(
    models.Channel.slack_name
  ):
    channels.append(channel)
  return channels


def total_channel_count(direct_channels, channels):
  return len(direct_channels) + len(channels)


def get_users():
  users = []
  for user in models.User.select().order_by(
    models.User.slack_name
  ):
    if user.slack_id == slackotron_settings.BOT_SLACK_ID:
      continue
    users.append(user)
  return users


def user_count(users):
  return len(users)

if __name__ == '__main__':
  APPLICATION.run(
    port=slackotron_settings.DASHBOARD_PORT,
    debug=slackotron_settings.DASHBOARD_DEBUG
  )
