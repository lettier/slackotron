#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron--An extensible slack bot.
'''

import sys
import os
import subprocess
from scribe import Scribe


class DashboardManager(Scribe, object):

  def start_dashboard(self):
    cwd = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, cwd + '/')
    env = os.environ.copy()
    env['PYTHONPATH'] = ":".join(sys.path)
    self.info('Starting dashboard.')
    self.server_process = subprocess.Popen(
        ['python', cwd + '/server.py'],
        shell=False,
        env=env
    )

  def stop_dashboard(self):
    self.info('Stopping dashboard.')
    if hasattr(self, 'server_process'):
      self.server_process.kill()
