from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User as django_user
from mock.mock import MagicMock, Mock, patch
from exceptions import WrappedDataServiceException

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

    @patch('data.api.get_user_project')
    def testRetrieveProject(self, mock_get_user_project):
        project_id = 'abc123'
        mock_get_user_project.return_value = {'id': 'abc123', 'name': 'ProjectA'}
        url = reverse('project-list') + project_id + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'ProjectA')

    @patch('data.api.get_user_project')
    def testRetrieveProjectNotFound(self, mock_get_user_project):
        project_id = 'abc123'
        dds_error = MagicMock()
        dds_error.status_code = 404
        dds_error.message = 'Not Found'
        mock_get_user_project.side_effect = WrappedDataServiceException(dds_error)
        url = reverse('project-list') + project_id + '/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('data.api.get_user_project_content')
    def testRetrieveProjectContent(self, mock_get_user_project_content):
        project_id = 'abc123'
        mock_get_user_project_content.return_value = [{'id': '12355', 'name': 'test.txt'}]
        url = reverse('project-list') + project_id + '/content/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('data.api.get_user_project_content')
    def testRetrieveProjectContentNotFound(self, mock_get_user_project_content):
        project_id = 'abc123'
        dds_error = MagicMock()
        dds_error.status_code = 404
        dds_error.message = 'Not Found'
        mock_get_user_project_content.side_effect = WrappedDataServiceException(dds_error)
        url = reverse('project-list') + project_id + '/content/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('data.api.get_user_project_content')
    def testRetrieveProjectContentWithFilter(self, mock_get_user_project_content):
        project_id = 'abc123'
        mock_get_user_project_content.return_value = [{'id': '12355', 'name': 'test.txt'}]
        url = reverse('project-list') + project_id + '/content/?search=test'
        response = self.client.get(url, format='json')
        mock, params = mock_get_user_project_content.call_args
        user, project_id, search = mock
        self.assertEqual('test', search)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
