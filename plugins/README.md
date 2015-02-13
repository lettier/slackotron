## Slackotron

A [Slack](https://api.slack.com/) bot customizable via plugins.

### Creating a Plugin

```bash
cd plugins/
mkdir my_plugin
cd my_plugin
touch __init__.py
touch my_plugin.py
touch my_plugin_settings.py
```

#### ./myplugin.py

```python
#!/usr/bin/env python

import
import plugins.plugin_base
import my_plugin_settings

# Make sure your plugin name matches its snake case directory name.
# my_plugin => MyPlugin
class MyPlugin(plugins.plugin_base.PluginBase):
  activation_strings = [
      "activate myplugin!",
      "call myplugin!"
  ]
  # You could also leave activation_strings empty to always be activated.
  # Define your settings.
  my_setting = my_plugin_settings.MY_SETTING

  # The method you must override.
  # Takes the channel, user, and message that activated your plugin.
  def _callback(self, channel, user, message):
    # Any logic here that you would like.
    # You can cache something in Redis.
    self.redis_client.set('key', 'value')
    # See plugins/plugin_base.py for more.
    # If you want to remove the string that activated your plugin:
    message_text = self._strip_bot_name_activation_string(message.text.lower())
    # Post something to the channel and user that activated your plugin...
    return 'My plugin's response.'
    # ...remember to return a string or None.
    # Or return...
    return None
    # ...to do nothing.
```

#### ./myplugin_settings.py

```python
#!/usr/bin/env python

'''
  MY_SETTING

  Short description.
'''

MY_SETTING = 'This is my setting.'
```


_(C) 2015 David Lettier._  
http://www.lettier.com/
