from rest_framework import viewsets, status, permissions
from util import get_remote_store
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from exceptions import DataServiceUnavailable


class ProjectsViewSet(viewsets.ViewSet):

    def list(self, request):
        username = request.user.username
        remote_store = get_remote_store(request.user)
        try:
            # project_names = remote_store.get_project_names()
            project_names = 'ProjectA ProjectB ProjectC'.split()
            serializer = Serializer(project_names, many=True)
            return Response(project_names)
        except Exception as e:
            raise DataServiceUnavailable(e)

