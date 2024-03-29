"""Notification channels for django-notifs."""

from json import dumps

import pika

from notifications.channels import BaseNotificationChannel


# noinspection PyMethodMayBeStatic
class BroadCastWebSocketChannel(BaseNotificationChannel):
    """Fanout notification for RabbitMQ."""

    def _connect(self):
        """Connect to the RabbitMQ server."""
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost')
        )
        channel = connection.channel()

        return connection, channel

    def construct_message(self):
        """Construct the message to be sent."""
        extra_data = self.notification_kwargs['extra_data']
        print(self.notification_kwargs)
        for k, v in self.notification_kwargs.items():
            print(k, v)

        # return dumps(extra_data['message'])
        new_message = {
            'user': extra_data['user'],
            'message': extra_data['message']
        }

        return dumps(new_message)

    def notify(self, message):
        """put the message of the RabbitMQ queue."""
        connection, channel = self._connect()

        uri = self.notification_kwargs['extra_data']['uri']

        channel.exchange_declare(exchange=uri, exchange_type='fanout')
        channel.basic_publish(exchange=uri, routing_key='', body=message)

        connection.close()
