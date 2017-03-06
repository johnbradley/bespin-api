from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = 'Adds user with specified token name'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password')
        parser.add_argument('tokenkey')

    def _create_user(self, username, password):
        user, created = User.objects.get_or_create(username=username, is_staff=True, is_superuser=True)
        if created:
            self.stdout.write("User '{}' created ith id {}".format(username, user.id))
        else:
            self.stderr.write("User '{}', already exists with id {}".format(username, user.id))
        user.set_password(password)
        user.save()
        return user

    @staticmethod
    def _get_old_token(user):
        try:
            return Token.objects.get(user=user)
        except ObjectDoesNotExist:
            return None

    def _delete_old_token(self, token):
        tokenkey = token.key
        token.delete()
        self.stderr.write("Previous token '{}' deleted".format(tokenkey))

    def _create_token(self, user, tokenkey):
        Token.objects.create(key=tokenkey, user=user)
        self.stdout.write("Token '{}' created.".format(tokenkey))

    def handle(self, **options):
        username = options['username']
        password = options['password']
        tokenkey = options['tokenkey']
        user = self._create_user(username, password)
        old_token = self._get_old_token(user)
        if old_token:
            if old_token.key == tokenkey:
                self.stderr.write("Token '{}' already exists".format(tokenkey))
            else:
                self._delete_old_token(old_token)
                self._create_token(user, tokenkey)
        else:
            self._create_token(user, tokenkey)
