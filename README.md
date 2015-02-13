![Slackotron]()

## Slackotron

A [Slack](https://api.slack.com/) bot customizable via plugins.

### Quick Start

```bash
# Install Python2.
# Install and run Redis.
# Install and run RabbitMQ.
# Download the Stanford Parser and NER.
virtualenv --no-site-packages --python=/usr/bin/python2 --always-copy \
slackotron_venv
cd slackotron_venv
source ./bin/activate
git clone
cd slackotron
pip install -r requirements.txt
cd ../lib/python2.7/site-packages/playhouse/
./berkeley_build.sh
cd ../../../../slackotron
cp settings.py.template settings.py
# Fill in your specific settings.
cd plugins/
# For each plugin in plugins.
  cd plugin/
  cp *settngs.py.template *settings.py
  # Fill in your specific settings.
cd ../../
python slackotron.py
# Point your browser to http://localhost:55555/
```

### Dependencies
* OS
    * Python2
    * Redis
    * RabbitMQ
    * Stanford Parser version 3.4.1
    * Stanford Named Entity Recognizer version 3.4
* Python
    * Pika
    * BeautifulSoup
    * Httplib2
    * NLTK
    * Numpy
    * Peewee
    * Redis
    * Requests
    * Flask
    * Colorama

_(C) 2015 David Lettier._  
http://www.lettier.com/
