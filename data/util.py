from models import DDSUserCredential, DDSApplicationCredential
from ddsc.core.remotestore import RemoteStore
from ddsc.config import Config

def get_remote_store(request):
    # Get a DukeDS credential for the user
    user_cred = DDSUserCredential.objects.get(user=request.user)

    # Get our agent key
    app_cred = DDSApplicationCredential.objects.first()

    # Populate a config object
    config = Config()
    config.update_properties({'user_key': user_cred.token})
    config.update_properties({'agent_key': app_cred.agent_key})
    config.update_properties({'url': app_cred.api_root})

    remote_store = RemoteStore(config)
    return remote_store

