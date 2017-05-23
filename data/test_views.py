from django.test import TestCase
from rest_framework import status
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User as django_user
from views import create_bespin_session_cookie_value
from rest_framework.authtoken.models import Token
from mock.mock import MagicMock, patch, Mock
import json
import urllib


class TestViews(TestCase):
    def setUp(self):
        self.user = django_user.objects.create_user('joe', password='secret')

    def test_create_bespin_cookie_creates_token(self):
        cookie_value = create_bespin_session_cookie_value(self.user)

        token = Token.objects.get(user=self.user)
        auth_data = {"authenticated": {"authenticator": "authenticator:drf-token-authenticator", "token": token.key}}
        expected = urllib.quote(json.dumps(auth_data))
        self.assertEqual(expected, cookie_value)

    def test_create_bespin_cookie_reads_token(self):
        token = Token.objects.create(user=self.user)

        cookie_value = create_bespin_session_cookie_value(self.user)

        auth_data = {"authenticated": {"authenticator": "authenticator:drf-token-authenticator", "token": token.key}}
        expected = urllib.quote(json.dumps(auth_data))
        self.assertEqual(expected, cookie_value)

    @patch("data.views.gcb_auth_views")
    def test_authorize_with_no_service_to_unconfigured(self, mock_gcb_auth_views):
        mock_gcb_auth_views.get_service.return_value = None
        url = reverse('auth-authorize')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('unconfigured', response['Location'])

    @patch("data.views.gcb_auth_views")
    def test_authorize_with_service(self, mock_gcb_auth_views):
        mock_gcb_auth_views.authorization_url.return_value = ('/someurl', 'somestate')
        url = reverse('auth-authorize')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual('/someurl', response['Location'])

    @patch("data.views.gcb_auth_views")
    @patch("data.views.authenticate")
    def test_authorize_callback_no_user_goes_to_slash(self, mock_authenticate, mock_gcb_auth_views):
        mock_gcb_auth_views.pop_state.return_value = '/someurl'
        mock_authenticate.return_value = None
        url = reverse('auth-callback')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual('/', response['Location'])
        self.assertNotIn('bespinsession', response.cookies)
