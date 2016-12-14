from models import DDSUserCredential, DDSEndpoint
from exceptions import WrappedDataServiceException
from django.core.exceptions import PermissionDenied
from ddsc.core.remotestore import RemoteStore
from ddsc.core.ddsapi import DataServiceError
from ddsc.config import Config


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
    :return: [dict] list of project metadata, including name and id
    """
    try:
        remote_store = get_remote_store(user)
        return remote_store.data_service.get_projects().json()['results']
    except DataServiceError as dse:
        raise WrappedDataServiceException(dse)


def get_user_project(user, dds_project_id):
    """
    Get a single Duke DS Project for a user
    :param user: User who has DukeDS credentials
    :param dds_project_id: str: duke data service project id
    :return: dict: project details
    """
    try:
        remote_store = get_remote_store(user)
        return remote_store.data_service.get_project_by_id(dds_project_id).json()
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
