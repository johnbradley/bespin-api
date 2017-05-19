from models import DDSUserCredential, DDSEndpoint
from exceptions import WrappedDataServiceException
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from ddsc.core.remotestore import RemoteStore
from ddsc.core.ddsapi import DataServiceError
from ddsc.core.ddsapi import ContentType
from ddsc.config import Config
from gcb_web_auth.utils import get_oauth_token, get_dds_token_from_oauth
import requests

class DDSBase(object):
    @classmethod
    def from_list(cls, project_dicts):
        return [cls(p) for p in project_dicts]


class DDSProject(DDSBase):
    """
    A simple object to represent a DDSProject
    """

    def __init__(self, project_dict):
        self.id = project_dict.get('id')
        self.name = project_dict.get('name')
        self.description = project_dict.get('description')


class DDSResource(DDSBase):

    def __init__(self, resource_dict):
        self.id = resource_dict.get('id')
        self.name = resource_dict.get('name')
        self.kind = resource_dict.get('kind')
        self.project = resource_dict.get('project').get('id')
        parent = resource_dict.get('parent')
        if parent.get('kind') == 'dds-folder':
            self.folder = parent.get('id')
        else:
            self.folder = None
        current_version_dict = resource_dict.get('current_version')
        if current_version_dict:
            self.version = current_version_dict.get('version')
            self.version_id = current_version_dict.get('id')
            upload_dict = current_version_dict.get('upload')
        else:
            self.version = None
            self.version_id = None
            upload_dict = None

        if upload_dict:
            self.size = upload_dict.get('size') or 0
        else:
            self.size = 0


def get_remote_store(user):
    """
    :param user: A Django model user object
    :return: a ddsc.core.remotestore.RemoteStore object
    """
    # Get a DukeDS credential for the user
    if user.is_anonymous():
        raise PermissionDenied("Requires login")
    config = get_dds_config(user)
    remote_store = RemoteStore(config)
    return remote_store


def get_dds_config(user):
    """
    Create DukeDSClient Config based on our current user.
    Uses keys from DDSUserCredential if they exist, otherwise tries to use OAuth token for this user.
    :param user: A Django model user object
    :return: ddsc.config.Config: settings to use with ddsclient
    """
    config = Config()

    # Get our agent key
    app_cred = DDSEndpoint.objects.first()
    config.update_properties({'agent_key': app_cred.agent_key})
    config.update_properties({'url': app_cred.api_root})

    # Setup user key if exists, otherwise setup dds temporary auth token
    try:
        user_cred = DDSUserCredential.objects.get(user=user)
        config.update_properties({'user_key': user_cred.token})
    except ObjectDoesNotExist:
        oauth_token = get_oauth_token(user)
        user_auth_token = _get_dds_auth_token(app_cred, oauth_token)
        config.update_properties({'auth': user_auth_token})
    return config


def _get_dds_auth_token(app_cred, oauth_token):
    """
    Exchange oauth token for dds token.
    :param app_cred: DDSEndpoint: endpoint we will communicate with
    :param oauth_token: OAuthToken: contains 'access_token' to be exchanged 
    :return: str: dds temporary auth token value
    """
    headers = {
        'Content-Type': ContentType.json,
    }
    access_token = oauth_token.token_dict.get('access_token')
    data = {
        "access_token": access_token,
    }
    url = app_cred.api_root + "/user/api_token"
    response = requests.get(url, headers=headers, params=data)
    response.raise_for_status()
    return response.json()['api_token']


def get_user_projects(user):
    """
    Get the Duke DS Projects for a user
    :param user: User who has DukeDS credentials
    :return: [DDSProject] list of projects, including name, description, and id
    """
    try:
        remote_store = get_remote_store(user)
        projects = remote_store.data_service.get_projects().json()
        return DDSProject.from_list(projects['results'])
    except DataServiceError as dse:
        raise WrappedDataServiceException(dse)


def get_user_project(user, dds_project_id):
    """
    Get a single Duke DS Project for a user
    :param user: User who has DukeDS credentials
    :param dds_project_id: str: duke data service project id
    :return: DDSProject: project details
    """
    try:
        remote_store = get_remote_store(user)
        project = remote_store.data_service.get_project_by_id(dds_project_id).json()
        return DDSProject(project)
    except DataServiceError as dse:
        raise WrappedDataServiceException(dse)


def get_user_project_content(user, dds_project_id, search_str=None):
    """
    Get all files and folders contained in a project (includes nested files and folders).
    :param user: User who has DukeDS credentials
    :param dds_project_id: str: duke data service project id
    :param search_str: str: searches name of a file
    :return: [dict]: list of dicts for a file or folder
    """
    try:
        remote_store = get_remote_store(user)
        resources = remote_store.data_service.get_project_children(dds_project_id, name_contains=search_str).json()['results']
        return DDSResource.from_list(resources)
    except DataServiceError as dse:
        raise WrappedDataServiceException(dse)


def get_user_folder_content(user, dds_folder_id, search_str=None):
    """
    Get all files and folders contained in a project (includes nested files and folders).
    :param user: User who has DukeDS credentials
    :param dds_folder_id: str: duke data service folder id
    :param search_str: str: searches name of a file
    :return: [dict]: list of dicts for a file or folder
    """
    try:
        remote_store = get_remote_store(user)
        resources = remote_store.data_service.get_folder_children(dds_folder_id, name_contains=search_str).json()['results']
        return DDSResource.from_list(resources)
    except DataServiceError as dse:
        raise WrappedDataServiceException(dse)


def get_file_name(user, dds_file_id):
    """
    Lookup a filename based on a file id.
    :param user: User who has DukeDS credentials
    :param dds_file_id: str: duke data service file id
    :return: str: name of the file
    """
    try:
        remote_store = get_remote_store(user)
        return remote_store.data_service.get_file(dds_file_id).json()['name']
    except DataServiceError as dse:
        raise WrappedDataServiceException(dse)


def give_download_permissions(user, project_id, target_dds_user_id):
    """
    Using the data service permissions of user give file_downloader permissions to project_id to target_dds_user_credential
    :param user: Django User: User who can grant permissions to project_id
    :param project_id: str: uuid of the project we want to set permissions on
    :param target_dds_user_id: str: user who needs download permissions
    """
    try:
        remote_store = get_remote_store(user)
        data_service = remote_store.data_service
        data_service.set_user_project_permission(project_id, target_dds_user_id, auth_role='file_downloader')
    except DataServiceError as dse:
        raise WrappedDataServiceException(dse)
