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
from lib.scribe import Scribe


class DashboardManager(Scribe, object):

  def start(self):
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

  def stop(self):
    self.info('Stopping dashboard.')
    if hasattr(self, 'server_process'):
      try:
        cpids = subprocess.check_output(
            ['pgrep', '-P', str(self.server_process.pid)]
        ).splitlines()
        for cpid in cpids:
          self.info('Killing child process PID %s.' % cpid)
          os.kill(int(cpid), signal.SIGINT)
      except Exception as e:
        self.error(e)
      self.server_process.send_signal(signal.SIGINT)
      while self.server_process.poll() is None:
        time.sleep(1)
      self.info('Dashboard stopped.')
