# Slackotron

A [Slack](https://www.slack.com/) bot customizable via plugins.

## Current Plugins

* beer - gives a random beer recommendation
* big_lebowski - gives a random quote from the movie
* calculator_duck - gives the answer to a mathematical expression
* chatty_kathy - analyzes a user's text and finds a (somewhat) related reply from the internet
* chuck_norris - gives a random chuck norris joke
* clean_up - deletes either the bot's or bot operator's Slack messages
* gif_gopher - searches and retrieves a GIF
* happy_sad - analyzes a user's text for sentiment and sends an appropriate emoji
* lunch - suggests a random place to grab lunch
* net_lingo - translates internet jargon/acronyms
* pivotal_pull - pulls queried stories from PivotalTracker and posts them to Slack
* recipe_puppy - gives a random recipe based on user given ingredients
* slack_scrapper - downloads all Slack messages
* weather - gives the current weather condition with a link
* yoda_speak - translates a user's text to sound like yoda

## Creating a Plugin

```bash
cd plugins/
mkdir my_plugin
cd my_plugin
touch __init__.py
touch my_plugin.py
touch my_plugin_settings.py.template
cp my_plugin_settings.py.template my_plugin_settings.py
```

### ./my_plugin.py

```python
#!/usr/bin/env python

import plugins.plugin_base
import my_plugin_settings


# Make sure your plugin name matches its snake case directory name.
# my_plugin => MyPlugin
class MyPlugin(plugins.plugin_base.PluginBase):
  activation_strings = [
      "activate my plugin!",
      "call my plugin!"
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
    # If you want to remove the string and/or bot slack name that activated
    # your plugin:
    message_text = self._clean_up_message_text(message.text.lower())
    # Post something to the channel and user that activated your plugin...
    return 'My plugin's response.'
    # ...remember to return a string or None.
    # Or return...
    return None
    # ...to do nothing.
```

### ./my_plugin_settings.py.template

```python
#!/usr/bin/env python

'''
  MY_SETTING

  Short description.
'''

MY_SETTING = 'This is my setting.'
```

### ./my_plugin_settings.py

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
