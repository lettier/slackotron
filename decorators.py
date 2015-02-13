#!/usr/bin/env python

'''
  DAVID LETTIER
  (C) 2015.

  http://www.lettier.com/

  Slackotron
'''

import traceback
import functools
import json
import pika
from scribe import Scribe

scribe = Scribe()


def rabbitmq_subscribe(**_kwargs):
  def rabbitmq_subcribe_decorator(func):
    @functools.wraps(func)
    def wrapper(self):
      connection = pika.BlockingConnection(
          parameters=pika.ConnectionParameters(
              host=_kwargs['host']
          )
      )
      channel = connection.channel()
      channel.exchange_declare(
          exchange=_kwargs['exchange'],
          exchange_type=_kwargs['exchange_type'],
          durable=True
      )
      if 'queue' not in _kwargs:
        _kwargs['queue'] = self.__class__.__name__
      channel.queue_declare(
          queue=_kwargs['queue'],
          durable=True
      )
      channel.queue_bind(
          queue=_kwargs['queue'],
          exchange=_kwargs['exchange'],
          routing_key=_kwargs['routing_key']
      )
      basic_get_ok, basic_properties, rmq_message = channel.basic_get(
          queue=_kwargs['queue']
      )
      return_value = None
      if rmq_message is not None and rmq_message != 'null':
        try:
          return_value = func(self, rmq_message=rmq_message)
          channel.basic_ack(
              delivery_tag=basic_get_ok.delivery_tag
          )
        except Exception as e:
          scribe.error(e)
          traceback.print_exc()
      if rmq_message == 'null':
          channel.basic_ack(
              delivery_tag=basic_get_ok.delivery_tag
          )
      channel.close()
      connection.close()
      return return_value
    return wrapper
  return rabbitmq_subcribe_decorator


def rabbitmq_publish(**_kwargs):
  def rabbitmq_publish_decorator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
      connection = pika.BlockingConnection(
          parameters=pika.ConnectionParameters(
              host=_kwargs['host']
          )
      )
      channel = connection.channel()
      channel.exchange_declare(
          exchange=_kwargs['exchange'],
          exchange_type=_kwargs['exchange_type'],
          durable=True
      )
      channel.confirm_delivery()
      if 'queue' in _kwargs:
        channel.queue_declare(
            queue=_kwargs['queue'],
            durable=True
        )
        channel.queue_bind(
            queue=_kwargs['queue'],
            exchange=_kwargs['exchange'],
            routing_key=_kwargs['routing_key']
        )
      return_value = func(self, *args, **kwargs)
      bodies = []
      if return_value.__class__.__name__ != 'list':
        bodies.append(return_value)
      else:
        bodies = return_value
      for body in bodies:
        try:
          basic_publish_ok = channel.basic_publish(
              exchange=_kwargs['exchange'],
              body=json.dumps(body),
              routing_key=_kwargs['routing_key'],
              properties=pika.BasicProperties(
                  content_type='application/json',
                  delivery_mode=1
              )
          )
          if not basic_publish_ok:
            scribe.warning('Message was not delivered!')
        except Exception as e:
          scribe.error(e)
      channel.close()
      connection.close()
      return return_value
    return wrapper
  return rabbitmq_publish_decorator
