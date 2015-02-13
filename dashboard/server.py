#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron--An extensible slack bot.
'''

import os
module_path = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, module_path.split('/dashboard')[0])
import slackotron_settings
import models
from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request

application = Flask(__name__)
application.config.from_object(__name__)

'''
  PAGES
'''


@application.route('/')
def index():
  _direct_channels = direct_channels()
  _channels = channels()
  _users = users()
  return render_template(
      'index.html',
      direct_channels=_direct_channels,
      channels=_channels,
      channel_count=total_channel_count(_direct_channels, _channels),
      users=_users,
      user_count=user_count(_users),
      active_page_name='/'
  )


@application.route('/pending_responses')
def pending_responses():
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


@application.route('/channel_security')
def channel_security():
  _direct_channels = direct_channels()
  _channels = channels()
  return render_template(
      'channel_security.html',
      direct_channels=_direct_channels,
      channels=_channels,
      channel_count=total_channel_count(_direct_channels, _channels),
      active_page_name='channel_security'
  )


@application.route('/post_a_message')
def post_a_message():
  _direct_channels = direct_channels()
  _channels = channels()
  _users = users()
  return render_template(
      'post_a_message.html',
      direct_channels=_direct_channels,
      channels=_channels,
      channel_count=total_channel_count(_direct_channels, _channels),
      users=_users,
      active_page_name='post_a_message'
  )


'''
  API
'''


@application.route(
    '/responses',
    methods=['POST']
)
def create_response():
  params = request.json
  print(params)
  if params is None:
    return jsonify(success=False, message='No params given.'), 400
  try:
    channel = models.Channel.get(
        models.Channel.id == params['to_channel_id']
    )
  except:
    return jsonify(success=False, message='Channel not found.'), 400
  try:
    user = models.User.get(
        models.User.id == params['to_user_id']
    )
  except:
    return jsonify(success=False, message='User not found.'), 400
  if 'text' not in params:
    return jsonify(success=False, message='Text parameter required.'), 400
  if params['text'] is None or params['text'] == '':
    return jsonify(success=False, message='Text parameter was blank.'), 400
  text = u'[OVERRIDE] ' + params['text']
  response = models.Response.create(
      text=text,
      to_channel=channel,
      to_user=user,
      is_approved=True,
      is_sent=False
  )
  response.save()
  return jsonify(success=True, message='', response=response._data)


@application.route(
    '/pending_responses/<pending_response_id>',
    methods=['PUT']
)
def approve_pending_response(pending_response_id):
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
  return jsonify(success=True, message='', pending_response=response._data)


@application.route(
    '/pending_responses/<pending_response_id>',
    methods=['DELETE']
)
def delete_pending_response(pending_response_id):
  try:
    response = models.Response.get(
        models.Response.id == pending_response_id
    )
    response.is_deleted = True
    response.save()
  except models.Response.DoesNotExist as e:
    return jsonify(success=False, message=str(e)), 404
  return '', 200


@application.route(
    '/channels/<channel_id>',
    methods=['PUT']
)
def update_channel_security(channel_id):
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
  except models.Channel.DoesNotExist as e:
    return jsonify(success=False, message=str(e)), 404
  return jsonify(success=True, message='', channel=channel._data)

'''
  HELPER METHODS
'''


def direct_channels():
  _direct_channels = []
  is_direct = True
  for direct_channel in models.Channel.select().where(
      models.Channel.is_direct == is_direct
  ).order_by(
      models.Channel.slack_name
  ):
    if direct_channel.direct_channel_user_name() != '':
      _direct_channels.append(direct_channel)
  return _direct_channels


def channels():
  _channels = []
  is_direct = False
  for channel in models.Channel.select().where(
      models.Channel.is_direct == is_direct
  ).order_by(
      models.Channel.slack_name
  ):
    _channels.append(channel)
  return _channels


def total_channel_count(direct_channels, channels):
  return len(direct_channels) + len(channels)


def users():
  _users = []
  for user in models.User.select().order_by(
      models.User.slack_name
  ):
    if user.slack_id == slackotron_settings.BOT_SLACK_ID:
      continue
    _users.append(user)
  return _users


def user_count(users):
  return len(users)

if __name__ == '__main__':
  application.run(
      port=slackotron_settings.DASHBOARD_PORT,
      debug=slackotron_settings.DASHBOARD_DEBUG
  )
