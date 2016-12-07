from django.test import TestCase
from models import DDSEndpoint, DDSUserCredential
from django.db import IntegrityError
from django.contrib.auth.models import User


class DDSEndpointTests(TestCase):

    # Not validating blank or null fields here, as it does not happen at the model layer
    # It is the responsibility of a form or serializer to do that.

    def test_unique_parameters1(self):
        endpoint1 = DDSEndpoint.objects.create(name='endpoint1', agent_key='abc123')
        self.assertIsNotNone(endpoint1)
        endpoint2 = DDSEndpoint.objects.create(name='endpoint2', agent_key='def456')
        self.assertIsNotNone(endpoint2)
        self.assertNotEqual(endpoint1, endpoint2)
        with self.assertRaises(IntegrityError):
            DDSEndpoint.objects.create(name='endpoint3', agent_key=endpoint1.agent_key)

    def test_unique_parameters2(self):
        DDSEndpoint.objects.create(name='endpoint1', agent_key='abc123')
        with self.assertRaises(IntegrityError):
            DDSEndpoint.objects.create(name='endpoint1', agent_key='ghi789')


class DDSUserCredentialTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.endpoint = DDSEndpoint.objects.create(name='app1', agent_key='abc123')

    def test_unique_parameters1(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)
        with self.assertRaises(IntegrityError):
            DDSUserCredential.objects.create(user=self.user, token='def456', endpoint=self.endpoint)

    def test_unique_parameters2(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123', endpoint=self.endpoint)
        other_user = User.objects.create_user('other_user')
        with self.assertRaises(IntegrityError):
            DDSUserCredential.objects.create(user=other_user, token='abc123', endpoint=self.endpoint)
