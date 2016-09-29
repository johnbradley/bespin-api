from django.test import TestCase
from models import DDSApplicationCredential, DDSUserCredential, DDSResource
from django.db import IntegrityError
from uuid import UUID

from django.contrib.auth.models import User

class DDSApplicationCredentialTests(TestCase):

    # Not validating blank or null fields here, as it does not happen at the model layer
    # It is the responsibility of a form or serializer to do that.

    def test_unique_parameters1(self):
        app1 = DDSApplicationCredential.objects.create(name='app1', agent_key='abc123')
        self.assertIsNotNone(app1)
        app2 = DDSApplicationCredential.objects.create(name='app2', agent_key='def456')
        self.assertIsNotNone(app2)
        self.assertNotEqual(app1, app2)
        with self.assertRaises(IntegrityError):
            DDSApplicationCredential.objects.create(name='app3', agent_key=app1.agent_key)

    def test_unique_parameters2(self):
        DDSApplicationCredential.objects.create(name='app1', agent_key='abc123')
        with self.assertRaises(IntegrityError):
            DDSApplicationCredential.objects.create(name='app1', agent_key='ghi789')


class DDSUserCredentialTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('test_user')

    def test_unique_parameters1(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123')
        with self.assertRaises(IntegrityError):
            DDSUserCredential.objects.create(user=self.user, token='def456')

    def test_unique_parameters2(self):
        DDSUserCredential.objects.create(user=self.user, token='abc123')
        other_user = User.objects.create_user('other_user')
        with self.assertRaises(IntegrityError):
            DDSUserCredential.objects.create(user=other_user, token='abc123')


class DDSResourceTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user('user1')
        self.user2 = User.objects.create_user('user2')
        self.project1_id = UUID(int=1)
        self.project2_id = UUID(int=2)
        self.path1 = '/path1'
        self.path2 = '/path2'

    def test_multiple_projects(self):
        """
        Tests that multiple project IDs can exist with the same owner and path
        :return:
        """
        resource1 = DDSResource.objects.create(owner=self.user1, project_id=self.project1_id, path=self.path1)
        resource2 = DDSResource.objects.create(owner=self.user1, project_id=self.project2_id, path=self.path1)
        self.assertNotEqual(resource1, resource2)
        self.assertEqual(resource1.owner, resource2.owner)
        self.assertEqual(resource1.path, resource2.path)
        self.assertNotEqual(resource1.project_id, resource2.project_id)

    def test_multiple_paths(self):
        """
        Tests that multiple paths can exist with the same owner and project
        :return:
        """
        resource1 = DDSResource.objects.create(owner=self.user1, project_id=self.project1_id, path=self.path1)
        resource2 = DDSResource.objects.create(owner=self.user1, project_id=self.project1_id, path=self.path2)
        self.assertNotEqual(resource1, resource2)
        self.assertEqual(resource1.owner, resource2.owner)
        self.assertNotEqual(resource1.path, resource2.path)
        self.assertEqual(resource1.project_id, resource2.project_id)

    def test_multiple_owners(self):
        """
        Tests that mutliple owners can exist with the same project and path
        :return:
        """
        resource1 = DDSResource.objects.create(owner=self.user1, project_id=self.project1_id, path=self.path1)
        resource2 = DDSResource.objects.create(owner=self.user2, project_id=self.project1_id, path=self.path1)
        self.assertNotEqual(resource1, resource2)
        self.assertNotEqual(resource1.owner, resource2.owner)
        self.assertEqual(resource1.project_id, resource2.project_id)
        self.assertEqual(resource1.path, resource2.path)

    def test_requires_uniqueness(self):
        """
        Tests that two resources must be unique
        :return:
        """
        DDSResource.objects.create(owner=self.user1, project_id=self.project1_id, path=self.path1)
        with self.assertRaises(IntegrityError):
            DDSResource.objects.create(owner=self.user1, project_id=self.project1_id, path=self.path1)
