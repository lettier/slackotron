![Slackotron](docs/img/logo.png)

# Slackotron

A [Slack](https://www.slack.com/) bot extendable via plugins.

## Screenshots

![](http://i.imgur.com/w6YAs7T.png)  
![](http://i.imgur.com/BsrBCPZ.jpg)  
![](http://i.imgur.com/hgBarlS.png)  
![](http://i.imgur.com/YQ4mcrH.jpg)  
![](http://i.imgur.com/LMgs9r9.png)  
![](http://i.imgur.com/FYkKKwX.png)  

## Quick Start

```bash
# Install Python2.
# Install JDK 8.
# Install and run Redis.
# Install and run RabbitMQ.
# Download the Stanford Parser and NER (see dependencies below).
python2_location=$(which python2) # Arch Linux
python2_location=$(which python) # Ubuntu or Mac OSX
virtualenv --no-site-packages --python=$python2_location --always-copy \
slackotron_venv
cd slackotron_venv/
source ./bin/activate
# Clone this Git repository.
git clone
cd slackotron/
# Install the needed Python modules.
pip install -r requirements.txt
# Install the Berkeley SQLite DB
cd ../lib/python2.7/site-packages/playhouse/
./berkeley_build.sh
cd ../../../../slackotron/
# Create the Slackotron settings file.
cp src/slackotron_settings.py.template src/slackotron_settings.py
# Fill in your specific settings.
# Look for:
#   - Slack API Token
#   - Bot Slack Name
#   - Bot Icon URL
#   - Bot Emoji
#   - Java Home Location
#     - Mac users:
#       - JAVA_HOME='/Library/Java/JavaVirtualMachines/jdk1.8.0_31.jdk/Contents/Home/bin/'
#   - Stanford Parser Location
#   - Stanford Parser Models Location
#   - Stanford NER Location
#   - Stanford NER Classifier Location
cd src/plugins/
# For each plugin in plugins.
  cd plugin_name/
  # Create the plugin settings file.
  cp plugin_name_settngs.py.template plugin_name_settings.py
  # Fill in your specific settings.
cd ../../
python src/slackotron.py
# Point your browser to http://localhost:55555/
# to use the dashboard.
# Visit http://localhost:55555/channels to subscribe
# to the channels you wish.
```

## Architecture Overview

### Models

Slackotron has its own internal models that are stored in a
 Berkeley SQLite database (DB).
The models include message, user, channel, and response.
A message has one user and channel.
A channel has many users and messages.
A channel can either be a Slack channel or direct-message (DM).
A user has many channels and messages.
A response has one message, user, and channel.

### Threads

The main Slackotron process (MSP) initializes the Channel User Manager
 which starts a thread that in turn runs the channel subscribers and publishers.
Channel subscribers pull in the latest raw Slack messages, generating
 Slackotron messages, for their channel.
Upon message generation, a channel subscriber publishes a RabbitMQ (RMQ)
 message to the Slackotron plugins exchange (SPE).
This RMQ message contains the Slackotron message, channel, and user ID.
Since the plugins exchange is fanout, all plugin queues receive the same RMQ message.
Channel publishers query the DB for all approved unsent responses for their channel.
Per approved unsent response, a channel publisher posts the response's text
 to their Slack DM or channel and marks the response as sent.
Channel subscribers and publishers are added or removed during runtime based on
 the selections on the dashboard channels page.

In addition to the channel subscribers/publishers thread, the Plugin Manager
 initializes a thread which turns plugin responses from RabbitMQ into persisted
 responses stored in the DB.
These responses will be picked up by the channel subscribers/publishers thread.

### Plugins

The majority of Slackotron's functionality resides with its plugins.
Each plugin runs in its own process upon initialization and
 has its own RMQ queue attached to the SPE.
Based on a plugin's configuration, a Slackotron message's text may activate a plugin.
Upon activation, a plugin performs some operation and may or may not send a RMQ message
 to the main Slackotron RMQ exchange and subsequent queue.
Plugin RMQ messages contain the plugin's response text.
The MSP dequeues these RMQ messages and generates responses.

### Security

Slackotron employs a level of security per each of its channels.
With security on, responses must be approved by the bot operator via
 the dashboard.
Each response's text is scrubbed of profanity if PROFANITY_FILTER_ON
 is set to true in the settings.
Within the dashboard, security per channel can be either turned off or on.

### Dashboard

The Slackotron dashboard is initialized upon boot of the MSP and
 runs in its own process.
The underlying technology is a Flask application that listens on port 55555
 by default.
The dashboard has four main pages.
The first page is an overview of the Slack DMs, channels, and users
 that Slackotron knows about.
The second page lists the responses awaiting approval.
It is here that responses can be approved or deleted.
The third page lists the Slackotron channels.
It is here that the bot operator can either turn off or on a
 channel's security and/or subscribe to individual channels.
The slackbot channel is subscribed by default.
The fourth page allows the bot operator to post a message to a Slack
 DM or channel and user.
Messages posted from the dashboard will contain the text "\[ADMIN\]"
 in Slack.

### An Example

Jane posts a message "Hello Slackotron!" to the Slack channel named general.
The channel subscriber, for general, generates a message with ID 0.
Message, with ID 0, has user with ID 1 and channel with ID 2.
The channel subscriber sends the RMQ message
 "{channel_id: 2, user_id: 1, message_id: 0}" to the SPE.
Plugin 0 dequeues and queries for message, user, and channel with ID 0,
 1, and 2 respectively.
Plugin 0 is not activated.
Plugin 1 does the same and is activated.
Plugin 1 sends the RMQ message
 "{channel_id: 2, user_id: 1, message_id: 0, response_text: "Hello!}" to
 the main Slackotron RMQ exchange.
The MSP dequeues and generates a response with ID 3 and text "@jane, Hello!".
Security is on for channel, with ID 2, so the response is marked not approved.
The bot operator goes to http://localhost:55555/pending_responses/ and sees
 the awaiting response.
The bot operator approves the response.
The channel publisher queries for unsent approved responses for channel with ID 2.
Response, with ID 3, is returned.
The channel publisher posts "@jane, Hello!" to the Slack channel named general
 and marks the response, with ID 3, as sent.

## Dependencies

* OS
  * [JDK 8](http://openjdk.java.net/install/)
  * [Python2](https://www.python.org/downloads/)
  * [Redis](http://redis.io/download)
  * [RabbitMQ](https://www.rabbitmq.com/download.html)
  * [Stanford Parser version 3.4.1](http://nlp.stanford.edu/software/lex-parser.shtml)
  * [Stanford Named Entity Recognizer version 3.4](http://nlp.stanford.edu/software/CRF-NER.shtml)
* Python
  * BeautifulSoup
  * Colorama
  * Httplib2
  * Flask
  * NLTK
  * Numpy
  * Pattern
  * Peewee
  * Pika
  * Redis
  * Requests

_(C) 2015 David Lettier._  
http://www.lettier.com/
