#!/usr/bin/python2

'''
  DAVID LETTIER
  (C) 2016.

  http://www.lettier.com/

  Slackotron
'''

import sys
import os
import subprocess
import signal
import time

execfile(
    '../bin/activate_this.py',
    dict(__file__='../bin/activate_this.py')
)

ENV = os.environ.copy()
ENV['PYTHONPATH'] = ":".join(sys.path)

SLACKTRON_PROCESS = subprocess.Popen(
    ['python', 'src/slackotron.py'],
    shell=False,
    env=ENV
)

while SLACKTRON_PROCESS.poll() is None:
  try:
    time.sleep(1)
  except KeyboardInterrupt:
    SLACKTRON_PROCESS.send_signal(signal.SIGINT)
time.sleep(1)
