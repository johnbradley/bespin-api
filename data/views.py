from django.shortcuts import render
from models import *
from django.contrib.auth.decorators import login_required
from ddsc.config import Config
from ddsc.core.remotestore import RemoteStore
from ddsc.core.util import ProjectFilenameList


def _get_remote_store(request):
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


@login_required
def browse_projects(request):
    username = request.user.username
    remote_store = _get_remote_store(request)
    project_names = remote_store.get_project_names()
    context = {'username': username, 'project_names': project_names}
    return render(request, 'browse_projects.html', context)


@login_required
def pick_resource(request):
    project_name = request.GET.get('project_name', None)
    remote_store = _get_remote_store(request)
    project = remote_store.fetch_remote_project(project_name)
    filename_list = ProjectFilenameList()
    filename_list.walk_project(project)
    context = {'project': project, 'resources': filename_list.details}
    return render(request, 'pick_resource.html', context)
