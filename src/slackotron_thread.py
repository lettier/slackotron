import threading
import traceback
from lib.scribe import Scribe


class SlackotronThread(Scribe, threading.Thread, object):
  lock = threading.Lock()

  def __init__(self, *args, **kwargs):
    threading.Thread.__init__(self)
    self.slack = kwargs['slack']
    self.exit = False

  def run(self):
    self.info(
        self.__class__.__name__ + ' started.'
    )
    while not self.exit:
      try:
        self._run_once()
      except Exception as e:
        self.error(e.__class__.__name__)
        self.error(e)
        traceback.print_exc()
        continue
    self.info(
        self.__class__.__name__ + ' stopped.'
    )

  def _run_once(self):
    pass
