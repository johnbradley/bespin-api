from rest_framework import viewsets, status, permissions
from util import get_user_projects, get_user_project, get_user_project_content
from rest_framework.response import Response
from exceptions import DataServiceUnavailable
from data.models import Workflow, WorkflowVersion, Job, JobInputFile, DDSJobInputFile, \
    DDSEndpoint, DDSUserCredential, URLJobInputFile, JobError
from data.serializers import WorkflowSerializer, WorkflowVersionSerializer, JobSerializer, \
    DDSEndpointSerializer, DDSUserCredSerializer, JobInputFileSerializer, DDSJobInputFileSerializer, \
    URLJobInputFileSerializer, JobErrorSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import detail_route
from lando import LandoJob


class ProjectsViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    def list(self, request):
        try:
            projects = get_user_projects(request.user)
            return Response(projects)
        except Exception as e:
            raise DataServiceUnavailable(e)

    def retrieve(self, request, pk=None):
        project_info = get_user_project(request.user, pk)
        return Response(project_info)

    @detail_route(methods=['get'])
    def content(self, request, pk=None):
        return Response(get_user_project_content(request.user, pk))


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

    @detail_route(methods=['post'])
    def start(self, request, pk=None):
        job = LandoJob(pk)
        job.start()
        return Response({'status': 'ok'})

    @detail_route(methods=['post'])
    def cancel(self, request, pk=None):
        job = LandoJob(pk)
        job.cancel()
        return Response({'status': 'ok'})


class DDSJobInputFileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = DDSJobInputFile.objects.all().order_by('index')
    serializer_class = DDSJobInputFileSerializer


class JobInputFileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = JobInputFile.objects.all()
    serializer_class = JobInputFileSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)


class URLJobInputFileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = URLJobInputFile.objects.all().order_by('index')
    serializer_class = URLJobInputFileSerializer


class DDSEndpointViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = DDSEndpoint.objects.all()
    serializer_class = DDSEndpointSerializer


class DDSUserCredViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = DDSUserCredential.objects.all()
    serializer_class = DDSUserCredSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)


class JobErrorViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = JobError.objects.all()
    serializer_class = JobErrorSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)