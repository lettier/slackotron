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
from scribe import Scribe


class PluginManager(Scribe, object):
  plugins = []

  def start_plugins(self):
    cwd = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, cwd + '/')
    env = os.environ.copy()
    env['PYTHONPATH'] = ":".join(sys.path)
    plugin_dirs = os.walk(cwd + '/').next()[1]
    for plugin_dir in plugin_dirs:
      self.info('Loading plugin ' + plugin_dir)
      class_name = ''.join([x.capitalize() for x in plugin_dir.split('_')])
      init_file = cwd + '/' + plugin_dir + '/__init__.py'
      if os.path.isfile(init_file):
        os.remove(init_file)
      f = open(init_file, 'w')
      f.write('import scribe\n')
      f.write('import ' + plugin_dir + '\n')
      f.write('scribe = scribe.Scribe()\n')
      f.write('try:\n')
      f.write('\t' + plugin_dir + '.' + class_name + '().run()\n')
      f.write('except Exception as e:\n')
      f.write('\tscribe.error(e)\n')
      f.close()
      self.plugins.append(
          subprocess.Popen(
              ['python', init_file],
              shell=False,
              env=env
          )
      )

  def stop_plugins(self):
    self.info('Stopping plugins.')
    for plugin in self.plugins:
      plugin.kill()
