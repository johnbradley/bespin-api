from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User as django_user
from mock.mock import MagicMock, Mock, patch

# Create your tests here.

class ProjectsTestCase(APITestCase):

    @patch('data.api.get_remote_store')
    def testListProjects(self, mock_get_remote_store):
        mock_get_remote_store.return_value = MagicMock(get_project_names=MagicMock(return_value=['project1','project2']))
        url = reverse('project-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


