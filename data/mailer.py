from models import LandoConnection
import pickle
from lando_messaging.workqueue import WorkQueueConnection

EMAIL_EXCHANGE = "EmailExchange"
ROUTING_KEY = "SendEmail"


class MailerConfig(object):
    """
    Settings for the AMQP queue we send messages to bespin-mailer over.
    """
    def __init__(self):
        self.work_queue_config = LandoConnection.objects.first()
        print(self.work_queue_config)


class MailerClient(object):
    def __init__(self):
        self.config = MailerConfig()

    def send(self, send_email_id):
        work_queue_connection = WorkQueueConnection(self.config)
        body = pickle.dumps({"send_email": send_email_id})
        work_queue_connection.connect()
        channel = work_queue_connection.connection.channel()
        channel.basic_publish(exchange=EMAIL_EXCHANGE,
                              routing_key=ROUTING_KEY,
                              body=body)
        work_queue_connection.close()
