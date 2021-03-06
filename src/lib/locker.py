#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2016.

  http://www.lettier.com/

  Slackotron
'''

import os
import errno
import shutil
import time
from lib.scribe import Scribe

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))


class Locker(Scribe, object):

  def make_lock_generator(self, key, give_up=60):
    self._make_dir()

    path = self._get_path()
    path_file_key = os.path.normpath(
        path + '/%s.lock' % key
    )

    def generator():
      flags = os.O_CREAT | os.O_EXCL
      spin = True
      start = time.time()
      while spin:
        try:
          os.open(path_file_key, flags)
          spin = False
          continue
        except OSError as error:
          if error.errno == errno.EEXIST:
            spin = True
            continue
          else:
            raise error
        if give_up is not None:
          if time.time() - start > give_up:
            raise Exception('Could not acquire lock.')

      yield

      try:
        os.remove(path_file_key)
      except Exception:
        pass

      yield

    return generator()

  def unlock_all(self):
    try:
      self._make_dir()
      shutil.rmtree(self._get_path())
    except Exception as error:
      self.error(error)

  def _get_path(self):
    return os.path.normpath(MODULE_PATH + '/locks')

  def _make_dir(self):
    path = self._get_path()
    if not os.path.exists(path):
      os.mkdir(path)
