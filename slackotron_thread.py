import threading
import traceback
from scribe import Scribe


class SlackotronThread(Scribe, threading.Thread, object):
  lock = threading.Lock()

  def __init__(self, *args, **kwargs):
    threading.Thread.__init__(self)
    self.slack = kwargs['slack']
    self.stop_thread = False

  def run(self):
    self.info(
        self.__class__.__name__ + ' started.'
    )
    while not self.stop_thread:
      try:
        self._run_once()
      except Exception as e:
        self.error('Exception:')
        self.error(e)
        traceback.print_exc()
        continue
    self.info(
        self.__class__.__name__ + ' stopped.'
    )

    def _run_once(self):
      pass
