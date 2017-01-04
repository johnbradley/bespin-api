from models import DDSUserCredential, DDSEndpoint
from exceptions import WrappedDataServiceException
from django.core.exceptions import PermissionDenied
from ddsc.core.remotestore import RemoteStore
from ddsc.core.ddsapi import DataServiceError
from ddsc.config import Config

class DDSProject(object):
    """
    A simple object to represent a DDSProject
    """

    def __init__(self, project_dict):
        self.id = project_dict.get('id')
        self.name = project_dict.get('name')
        self.description = project_dict.get('description')

    @classmethod
    def from_list(cls, project_dicts):
        return [cls(p) for p in project_dicts]


def get_remote_store(user):
    """
    :param user: A Django model user object
    :return: a ddsc.core.remotestore.RemoteStore object
    """
    # Get a DukeDS credential for the user
    if user.is_anonymous():
        raise PermissionDenied("Requires login")

    user_cred = DDSUserCredential.objects.get(user=user)

    # Get our agent key
    app_cred = DDSEndpoint.objects.first()

    # Populate a config object
    config = Config()
    config.update_properties({'user_key': user_cred.token})
    config.update_properties({'agent_key': app_cred.agent_key})
    config.update_properties({'url': app_cred.api_root})

    remote_store = RemoteStore(config)
    return remote_store


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


def get_user_project_content(user, dds_project_id, search_str=''):
    """
    Get all files and folders contained in a project (includes nested files and folders).
    :param user: User who has DukeDS credentials
    :param dds_project_id: str: duke data service project id
    :param search_str: str: searches name of a file
    :return: [dict]: list of dicts for a file or folder
    """
    try:
        remote_store = get_remote_store(user)
        return remote_store.data_service.get_project_children(dds_project_id, name_contains=search_str).json()['results']
    except DataServiceError as dse:
        raise WrappedDataServiceException(dse)
