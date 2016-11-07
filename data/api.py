from rest_framework import viewsets, status, permissions
from util import get_user_projects
from rest_framework.response import Response
from exceptions import DataServiceUnavailable


class ProjectsViewSet(viewsets.ViewSet):

    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        try:
            projects = get_user_projects(request.user)
            return Response(projects)
        except Exception as e:
            raise DataServiceUnavailable(e)

