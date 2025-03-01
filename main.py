
import json
from configparser import ConfigParser
import mysql.connector
import pika


# Loading config
config = ConfigParser()
config.read('config.ini')

# Connecting RabbitMQ
rabbit_connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=config.get(section='RABBIT', option='host'),
        port=config.getint(section='RABBIT', option='port'),
        credentials=pika.PlainCredentials(
            username=config.get(section='RABBIT', option='user'),
            password=config.get(section='RABBIT', option='password'),
        ),
    )
)


# Message queueing callback
def publish(channel, queue, mysql_cursor, table_name, raw_message_data):
    basic_query = f'SELECT id FROM {table_name} WHERE project_id=%(project_id)s AND enabled=TRUE;'

    mysql_cursor.execute(
        operation=basic_query,
        params={
            'table_name': table_name,
            'project_id': raw_message_data['project_id']
        }
    )
    results = mysql_cursor.fetchall()
    if len(results) > 0:
        for record in results:
            message = raw_message_data | {'integration_id': record[0]}
            channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent
                ),
            )
# publish


def callback(ch, method, properties, body):
    data = json.loads(body)

    # Connecting the database
    db = mysql.connector.connect(
        host=config.get(section='DATABASE', option='host'),
        port=config.getint(section='DATABASE', option='port'),
        database=config.get(section='DATABASE', option='database'),
        user=config.get(section='DATABASE', option='user'),
        password=config.get(section='DATABASE', option='password'),
    )
    cursor = db.cursor()

    # Loading projects
    cursor.execute(
        operation='SELECT id FROM projects WHERE id=%(project_id)s AND enabled=TRUE LIMIT 1;',
        params={'project_id': data['project_id']}
    )
    result = cursor.fetchone()

    if result is not None:
        channel_dispatcher = rabbit_connection.channel()

        services = {
            'emails_bz': config.get(section='APP', option='queue_email_bz'),
            'telegram_messages': config.get(section='APP', option='queue_tg_message'),
            # ... etc. ...
        }

        for table_name, queue in services.items():
            channel_dispatcher.queue_declare(queue=queue, durable=True)
            publish(
                channel=channel_dispatcher,
                queue=queue,
                mysql_cursor=cursor,
                table_name=table_name,
                raw_message_data=data
            )

    db.close()
    ch.basic_ack(delivery_tag=method.delivery_tag)
# callback


if __name__ == '__main__':
    rabbit_channel = rabbit_connection.channel()

    rabbit_channel.queue_declare(
        queue=config.get(section='APP', option='queue_dispatcher'),
        durable=True,
    )
    rabbit_channel.basic_qos(prefetch_count=1)

    rabbit_channel.basic_consume(
        queue=config.get(section='APP', option='queue_dispatcher'),
        on_message_callback=callback
    )

    rabbit_channel.start_consuming()
