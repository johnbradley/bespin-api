from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class Command(BaseCommand):
    help = 'Adds user with specified token name'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('tokenname')

    def handle(self, **options):
        username = options['username']
        tokenname = options['tokenname']
        user = User.objects.create(username=username)
        t = Token.objects.create(key=tokenname, user=user)
