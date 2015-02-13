import sys
import logging
import inspect
from rainbow_logging_handler import RainbowLoggingHandler
logger = logging.getLogger('slackotron')
logger.setLevel(logging.DEBUG)
logger.propagate = False
formatter = logging.Formatter(
    '[%(asctime)s] %(name)s %(message)s'
)
handler = RainbowLoggingHandler(
    sys.stderr
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class Scribe(object):
  logger = logger

  def debug(self, message):
    self.logger.info(self.__format_message(message))

  def info(self, message):
    self.logger.info(self.__format_message(message))

  def warning(self, message):
    message = self.__make_white_on_blue(message)
    self.logger.warning(self.__format_message(message))

  def error(self, message):
    message = self.__make_white_on_magenta(message)
    self.logger.error(self.__format_message(message))

  def critical(self, message):
    message = self.__make_white_on_red(message)
    self.logger.critical(self.__format_message(message))

  def __format_message(self, message):
    filename, function, line_number = self.__stack_info(3)
    filename = self.__make_yellow(filename)
    function = self.__make_green(function)
    line_number = self.__make_cyan(line_number)
    if message.__class__.__name__ not in ['str', 'unicode']:
      try:
        message = str(message)
      except UnicodeEncodeError:
        message = unicode(message).encode('utf-8', 'ignore')
    return filename + ':' + function + ':' + line_number + ' ' + message

  def __make_cyan(self, string):
    return self.__color_format(36, str(string))

  def __make_green(self, string):
    return self.__color_format(32, str(string))

  def __make_yellow(self, string):
    return self.__color_format(33, str(string))

  def __make_white_on_red(self, string):
    return self.__color_format(41, str(string))

  def __make_white_on_magenta(self, string):
    return self.__color_format(45, str(string))

  def __make_white_on_blue(self, string):
    return self.__color_format(44, str(string))

  def __color_format(self, color_code, string):
    return '\033[1;' + str(color_code) + 'm' + string + '\033[1;m'

  def __stack_info(self, level):
    try:
      caller_frame = inspect.stack()[level][0]
      info = inspect.getframeinfo(caller_frame)
      filename = str(info.filename).split('/')[-1]
      function = str(info.function)
      line_number = str(info.lineno)
      return filename, function, line_number
    except:
      return '?', '?', '?'
