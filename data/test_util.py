from __future__ import absolute_import
from django.test import TestCase
from data.util import has_download_permissions, DataServiceError, WrappedDataServiceException
from mock import patch, Mock


class HasDownloadPermissionsTestCase(TestCase):
    @patch('data.util.get_dds_config_for_credentials')
    @patch('data.util.RemoteStore')
    def test_has_download_permissions_user_already_has_permissions(self, mock_remote_store, mock_get_dds_config):
        dds_user_credential = Mock()
        project_id = '123'
        mock_remote_store.return_value.data_service.get_user_project_permission.return_value.json.return_value = {
            'auth_role': {
                'id': 'file_downloader'
            }
        }
        self.assertTrue(has_download_permissions(dds_user_credential, project_id))
        mock_remote_store.return_value.data_service.get_user_project_permission.return_value.json.return_value = {
            'auth_role': {
                'id': 'file_downloader'
            }
        }
        self.assertTrue(has_download_permissions(dds_user_credential, project_id))
        mock_remote_store.return_value.data_service.get_user_project_permission.return_value.json.return_value = {
            'auth_role': {
                'id': 'file_editor'
            }
        }
        self.assertTrue(has_download_permissions(dds_user_credential, project_id))
        mock_remote_store.return_value.data_service.get_user_project_permission.return_value.json.return_value = {
            'auth_role': {
                'id': 'project_admin'
            }
        }
        self.assertTrue(has_download_permissions(dds_user_credential, project_id))

    @patch('data.util.get_dds_config_for_credentials')
    @patch('data.util.RemoteStore')
    def test_has_download_permissions_user_wrong_permissions(self, mock_remote_store, mock_get_dds_config):
        dds_user_credential = Mock()
        project_id = '123'
        mock_remote_store.return_value.data_service.get_user_project_permission.return_value.json.return_value = {
            'auth_role': {
                'id': 'project_metadata_viewer'
            }
        }
        self.assertFalse(has_download_permissions(dds_user_credential, project_id))

    @patch('data.util.get_dds_config_for_credentials')
    @patch('data.util.RemoteStore')
    def test_has_download_permissions_user_no_permissions(self, mock_remote_store, mock_get_dds_config):
        dds_user_credential = Mock()
        project_id = '123'
        data_service_error = DataServiceError(response=Mock(status_code=404), url_suffix=Mock(), request_data=Mock())
        mock_remote_store.return_value.data_service.get_user_project_permission.side_effect = data_service_error
        self.assertFalse(has_download_permissions(dds_user_credential, project_id))

    @patch('data.util.get_dds_config_for_credentials')
    @patch('data.util.RemoteStore')
    def test_has_download_permissions_unexpected_error(self, mock_remote_store, mock_get_dds_config):
        dds_user_credential = Mock()
        project_id = '123'
        data_service_error = DataServiceError(response=Mock(status_code=500), url_suffix=Mock(), request_data=Mock())
        mock_remote_store.return_value.data_service.get_user_project_permission.side_effect = data_service_error
        with self.assertRaises(WrappedDataServiceException):
            self.assertFalse(has_download_permissions(dds_user_credential, project_id))
