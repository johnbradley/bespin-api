from django.core.management.base import BaseCommand
from data.models import LandoConnection
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    help = 'Creates the lando (rabbitmq) connection object with the specified settings'

    def add_arguments(self, parser):
        parser.add_argument('host')
        parser.add_argument('username')
        parser.add_argument('password')
        parser.add_argument('queuename')

    def _delete_old_connections(self):
        old_connections = LandoConnection.objects.all()
        if old_connections:
            self.stderr.write("Removing old LandoConnections")
            for old_connection in old_connections:
                old_connection.delete()

    def handle(self, **options):
        host = options['host']
        username = options['username']
        password = options['password']
        queue_name = options['queuename']
        try:
            connection = LandoConnection.objects.get(host=host, username=username, password=password,
                                                     queue_name=queue_name)
        except ObjectDoesNotExist:
            connection = None
        if connection:
            self.stderr.write("LandoConnection with these settings already exists with id {}".format(connection.id))
        else:
            self._delete_old_connections()
            connection = LandoConnection.objects.create(host=host, username=username, password=password,
                                                        queue_name=queue_name)
            self.stdout.write("LandoConnection created ith id {}".format(host, connection.id))
