from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User as django_user
from mock.mock import MagicMock, Mock, patch

# Create your tests here.

class ProjectsTestCase(APITestCase):

    def setUp(self):
        username = 'username'
        password = 'secret'
        django_user.objects.create_user(username, password=password)
        self.client.login(username=username, password=password)

    def testFailsUnauthenticated(self):
        self.client.logout()
        url = reverse('project-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('data.api.get_user_projects')
    def testListProjects(self, mock_get_user_projects):
        mock_get_user_projects.return_value = [{'id':'abc123','name':'ProjectA'}, {'id':'def567','name':'ProjectB'}]
        url = reverse('project-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

