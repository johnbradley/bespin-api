from rest_framework import viewsets, permissions
from util import get_user_projects, get_user_project, get_user_project_content, get_user_folder_content
from rest_framework.response import Response
from exceptions import DataServiceUnavailable, WrappedDataServiceException, BespinAPIException
from data.models import Workflow, WorkflowVersion, Job, JobInputFile, DDSJobInputFile, \
    DDSEndpoint, DDSUserCredential, URLJobInputFile, JobError, JobOutputDir
from data.serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import detail_route
from lando import LandoJob
from django.db.models import Q
from jobfactory import create_job_factory


class DDSViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def _ds_operation(self, func, *args):
        try:
            return func(*args)
        except WrappedDataServiceException:
            raise # passes along status code, e.g. 404
        except Exception as e:
            raise DataServiceUnavailable(e)


class DDSProjectsViewSet(DDSViewSet):
    """
    Interfaces with DukeDS API to provide project listing and details.
    Though it is not backed by django models, the ReadOnlyModelViewSet base class
    still works well
    """
    serializer_class = DDSProjectSerializer

    def get_queryset(self):
        return self._ds_operation(get_user_projects, self.request.user)

    def get_object(self):
        project_id = self.kwargs.get('pk')
        return self._ds_operation(get_user_project, self.request.user, project_id)


class DDSResourcesViewSet(DDSViewSet):
    """
    Interfaces with DukeDS API to list files and folders using query parameters. To list the root level
    of a project, GET with ?project_id=:project_id, and to list a folder within a project,
    GET with ?folder_id=:folder_id
    """
    serializer_class = DDSResourceSerializer

    def get_queryset(self):
        # check for project id or folder_id
        folder_id = self.request.query_params.get('folder_id', None)
        project_id = self.request.query_params.get('project_id', None)
        if folder_id:
            return self._ds_operation(get_user_folder_content, self.request.user, folder_id)
        elif project_id:
            return self._ds_operation(get_user_project_content, self.request.user, project_id)
        else:
            raise BespinAPIException(400, 'Getting dds-resources requires either a project_id or folder_id query parameter')


class WorkflowsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer


class WorkflowVersionsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = WorkflowVersion.objects.all()
    serializer_class = WorkflowVersionSerializer


class JobsViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobSerializer

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user)

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

    @detail_route(methods=['post'])
    def restart(self, request, pk=None):
        job = LandoJob(pk)
        job.restart_job()
        return Response({'status': 'ok'})


class AdminJobsViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = AdminJobSerializer
    queryset = Job.objects.all()


class DDSJobInputFileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DDSJobInputFileSerializer

    def get_queryset(self):
        return DDSJobInputFile.objects.filter(job_input_file__job__user=self.request.user)


class JobInputFileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobInputFileSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)

    def get_queryset(self):
        return JobInputFile.objects.filter(job__user=self.request.user)


class AdminJobInputFileViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = JobInputFileSerializer
    queryset = JobInputFile.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)


class URLJobInputFileViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = URLJobInputFileSerializer

    def get_queryset(self):
        return URLJobInputFile.objects.filter(job_input_file__job__user=self.request.user)


class DDSEndpointViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DDSEndpointSerializer
    queryset = DDSEndpoint.objects.all()


class DDSUserCredViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DDSUserCredSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)

    def get_queryset(self):
        return DDSUserCredential.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        self.save_with_user(serializer)

    def perform_update(self, serializer):
        self.save_with_user(serializer)

    def save_with_user(self, serializer):
        serializer.save(user=self.request.user)


class AdminDDSUserCredentialsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    queryset = DDSUserCredential.objects.all()
    serializer_class = AdminDDSUserCredSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)


class JobErrorViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobErrorSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)

    def get_queryset(self):
        return JobError.objects.filter(job__user=self.request.user)


class AdminJobErrorViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    queryset = JobError.objects.all()
    serializer_class = JobErrorSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('job',)


class JobOutputDirViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = JobOutputDir.objects.all()
    serializer_class = JobOutputDirSerializer


class JobQuestionnaireViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = JobQuestionnaire.objects.all()
    serializer_class = JobQuestionnaireSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('workflow_version',)


class JobQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = JobQuestion.objects.all()
    serializer_class = JobQuestionSerializer


class JobAnswerSetViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobAnswerSetSerializer

    def get_queryset(self):
        return JobAnswerSet.objects.filter(user=self.request.user)

    @detail_route(methods=['post'])
    def create_job(self, request, pk=None):
        job_answer_set = JobAnswerSet.objects.filter(user=self.request.user, pk=pk).first()
        job_factory = create_job_factory(self.request.user, job_answer_set)
        cwl_input = job_factory.build_cwl_input()
        return Response({
            'cwl_input': cwl_input,

        })


class JobAnswerViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobAnswerSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('questionnaire',)

    def get_queryset(self):
        return JobAnswer.objects.filter(Q(user=self.request.user) | Q(questionnaire__isnull=False))


class JobStringAnswerViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobStringAnswerSerializer
    queryset = JobStringAnswer.objects.all()


class JobDDSFileAnswerViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobDDSFileAnswerSerializer
    queryset = JobDDSFileAnswer.objects.all()
