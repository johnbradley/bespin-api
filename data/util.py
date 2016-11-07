from models import DDSUserCredential, DDSApplicationCredential
from django.core.exceptions import PermissionDenied
from ddsc.core.remotestore import RemoteStore
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
    app_cred = DDSApplicationCredential.objects.first()

    # Populate a config object
    config = Config()
    config.update_properties({'user_key': user_cred.token})
    config.update_properties({'agent_key': app_cred.agent_key})
    config.update_properties({'url': app_cred.api_root})

    remote_store = RemoteStore(config)
    return remote_store

