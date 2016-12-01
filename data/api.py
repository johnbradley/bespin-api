from rest_framework import viewsets, status, permissions
from util import get_user_projects
from rest_framework.response import Response
from exceptions import DataServiceUnavailable
from data.models import Workflow, WorkflowVersion, Job, JobParam, JobParamDDSFile, \
    DDSApplicationCredential, DDSUserCredential
from data.serializers import WorkflowSerializer, WorkflowVersionSerializer, JobSerializer, \
    JobParamSerializer, JobParamDDSFileSerializer, DDSAppCredSerializer, DDSUserCredSerializer
from django_filters.rest_framework import DjangoFilterBackend


class ProjectsViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    def list(self, request):
        try:
            projects = get_user_projects(request.user)
            return Response(projects)
        except Exception as e:
            raise DataServiceUnavailable(e)


class WorkflowsViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer


class WorkflowVersionsViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = WorkflowVersion.objects.all()
    serializer_class = WorkflowVersionSerializer


class JobsViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def perform_create(self, serializer):
        self.save_with_user(serializer)

    def perform_update(self, serializer):
        self.save_with_user(serializer)

    def save_with_user(self, serializer):
        serializer.save(user=self.request.user)


class JobParamsViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = JobParam.objects.all()
    serializer_class = JobParamSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job', 'staging')

class JobParamDDSFilesViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = JobParamDDSFile.objects.all()
    serializer_class = JobParamDDSFileSerializer


class DDSAppCredViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = DDSApplicationCredential.objects.all()
    serializer_class = DDSAppCredSerializer


class DDSUserCredViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = DDSUserCredential.objects.all()
    serializer_class = DDSUserCredSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)
