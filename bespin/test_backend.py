from django.test.utils import override_settings
from django.test import TestCase
from mock import patch

from backend import BespinOAuth2Backend

class BespinOAuth2BackendTestCase(TestCase):

    def setUp(self):
        self.details = {'dukeUniqueID': 'abc123'}

    @override_settings(REQUIRED_GROUP_MANAGER_GROUP='test-group')
    @patch('bespin.backend.BespinOAuth2Backend.verify_user_belongs_to_group')
    def test_check_user_details_verifies_required_group(self, mock_verify):
        backend = BespinOAuth2Backend()
        backend.check_user_details(self.details)
        self.assertTrue(mock_verify.called)
        self.assertTrue(mock_verify.call_args('abc123','test-group'))

    @override_settings(REQUIRED_GROUP_MANAGER_GROUP=None)
    @patch('bespin.backend.BespinOAuth2Backend.verify_user_belongs_to_group')
    def test_check_user_details_skips_none_group(self, mock_verify):
        backend = BespinOAuth2Backend()
        backend.check_user_details(self.details)
        self.assertFalse(mock_verify.called)

    @override_settings(REQUIRED_GROUP_MANAGER_GROUP='')
    @patch('bespin.backend.BespinOAuth2Backend.verify_user_belongs_to_group')
    def test_check_user_details_skips_emptystring_group(self, mock_verify):
        backend = BespinOAuth2Backend()
        backend.check_user_details(self.details)
        self.assertFalse(mock_verify.called)
