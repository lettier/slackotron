#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import sys
import os
import subprocess
import signal
import time
import json
import decorators
import slackotron_settings
from lib.scribe import Scribe
from lib.locker import Locker
from slackotron_thread import SlackotronThread
from models import Channel
from models import User
from models import Message
from models import Response
from plugins.plugin_base import RABBITMQ_PLUGIN_RESPONSE_EXCHANGE
from plugins.plugin_base import RABBITMQ_PLUGIN_RESPONSE_QUEUE
from plugins.plugin_base import RABBITMQ_PLUGIN_RESPONSE_ROUTING_KEY


class PluginManager(Scribe, object):
  '''
    PluginManager(Scribe, object)
  '''
  plugins = []

  def __init__(self, **kwargs):
    self.slack = kwargs['slack']
    self.thread = None
    self.cwd = None
    self.env = {}
    self.plugin_dirs = []

  def start(self):
    '''
      start()
    '''
    self.__set_cwd()
    self.__set_env()
    self.__set_plugin_dirs()
    for plugin_dir in self.plugin_dirs:
      self.info('Loading plugin ' + plugin_dir)
      init_file = self.__write_plugin_init_file(plugin_dir)
      self.plugins.append(
          subprocess.Popen(
              ['python', init_file],
              shell=False,
              env=self.env
          )
      )
    self.thread = PluginManagerThread(
        **{
            'slack': self.slack
        }
    )
    self.thread.daemon = False
    self.thread.start()

  def stop(self):
    '''
      stop()
    '''
    self.info('Stopping plugins.')
    for plugin in self.plugins:
      plugin.send_signal(signal.SIGINT)
      while plugin.poll() is None:
        time.sleep(1)
    self.plugins = []
    self.thread.exit = True
    for plugin_dir in self.plugin_dirs:
      self.__erase_plugin_init_file(plugin_dir)

  def __set_cwd(self):
    '''
      __set_cwd
    '''
    self.cwd = os.path.dirname(os.path.realpath(__file__))

  def __set_env(self):
    '''
      __set_env()
    '''
    sys.path.insert(0, self.cwd + '/')
    env = os.environ.copy()
    env['PYTHONPATH'] = ":".join(sys.path)
    self.env = env

  def __set_plugin_dirs(self):
    '''
      __set_plugin_dirs()
    '''
    self.plugin_dirs = os.walk(self.cwd + '/').next()[1]

  def __get_class_name(self, plugin_dir):  # pylint:disable=no-self-use
    '''
      __get_class_name(plugin_dir)
    '''
    return ''.join([x.capitalize() for x in plugin_dir.split('_')])

  def __make_init_file(self, plugin_dir):
    '''
      __make_init_file(plugin_dir)
    '''
    init_file = self.cwd + '/' + plugin_dir + '/__init__.py'
    if os.path.isfile(init_file):
      os.remove(init_file)
    return init_file

  def __write_plugin_init_file(self, plugin_dir):
    '''
      __write_plugin_init_file(plugin_dir)
    '''
    class_name = self.__get_class_name(plugin_dir)
    init_file = self.__make_init_file(plugin_dir)
    filee = open(init_file, 'w')
    filee.write('import lib.scribe\n')
    filee.write('import ' + plugin_dir + '\n')
    filee.write('scribe = lib.scribe.Scribe()\n')
    filee.write('try:\n')
    filee.write('  ' + plugin_dir + '.' + class_name + '().run()\n')
    filee.write('except Exception as e:\n')
    filee.write('  scribe.error(e)\n')
    filee.close()
    return init_file

  def __erase_plugin_init_file(self, plugin_dir):
    '''
      __erase_plugin_init_file(plugin_dir)
    '''
    init_file = self.__make_init_file(plugin_dir)
    if os.path.isfile(init_file):
      os.remove(init_file)
    return init_file


class PluginManagerThread(SlackotronThread):
  '''
    PluginManagerThread(SlackotronThread)
  '''

  def __init__(self, *args, **kwargs):
    super(PluginManagerThread, self).__init__(*args, **kwargs)
    self.locker = Locker()

  @decorators.rabbitmq_subscribe(
      host=slackotron_settings.RABBITMQ_HOST_URL,
      exchange=RABBITMQ_PLUGIN_RESPONSE_EXCHANGE,
      queue=RABBITMQ_PLUGIN_RESPONSE_QUEUE,
      routing_key=RABBITMQ_PLUGIN_RESPONSE_ROUTING_KEY
  )
  def _run_once(self, *_, **kwargs):
    try:
      rmq_message = kwargs.get('rmq_message', '{}') or '{}'
      rmq_message = json.loads(rmq_message)
      if len(rmq_message) == 0:
        return None
      channel = Channel.get(
          Channel.id == rmq_message['channel_id']  # noqa pylint:disable=no-member
      )
      if channel.is_subscribed is False:
        return None
      user = User.get(
          User.id == rmq_message['user_id']  # noqa pylint:disable=no-member
      )
      message = Message.get(
          Message.id == rmq_message['message_id']  # noqa pylint:disable=no-member
      )
      plugin_name = rmq_message['plugin_name']
      plugin_response = rmq_message['plugin_response']
      if len(plugin_name) == 0:
        return None
      if len(plugin_response) == 0:
        return None
      is_approved = True if channel.is_secure is False \
          else False
      response = Response(
          text=plugin_response,
          from_plugin=plugin_name,
          in_response_to=message,
          to_channel=channel,
          to_user=user,
          is_approved=is_approved,
          is_sent=False,
      )
      lock_generator = self.locker.make_lock_generator('response')
      try:
        lock_generator.next()
        response.save()
      except Exception as error:
        self.error(error)
      finally:
        lock_generator.next()
    except Exception as error:
      self.error(error)
      return None
