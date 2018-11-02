import json
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.db import transaction
from bespin_api_v2.serializers import AdminWorkflowSerializer, AdminWorkflowVersionSerializer, VMStrategySerializer, \
    WorkflowConfigurationSerializer, JobOrderDataSerializer
from data.serializers import JobSerializer
from data.models import Workflow, WorkflowVersion, VMStrategy, WorkflowConfiguration, JobFileStageGroup
from data.exceptions import BespinAPIException


class CreateListRetrieveModelViewSet(mixins.CreateModelMixin,
                                     mixins.ListModelMixin,
                                     mixins.RetrieveModelMixin,
                                     viewsets.GenericViewSet):
    pass


class AdminWorkflowViewSet(CreateListRetrieveModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = AdminWorkflowSerializer
    queryset = Workflow.objects.all()


class AdminWorkflowVersionViewSet(CreateListRetrieveModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = AdminWorkflowVersionSerializer
    queryset = WorkflowVersion.objects.all()


class AdminWorkflowConfigurationViewSet(CreateListRetrieveModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = WorkflowConfigurationSerializer
    queryset = WorkflowConfiguration.objects.all()


class VMStrategyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = VMStrategySerializer
    queryset = VMStrategy.objects.all()


class WorkflowConfigurationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WorkflowConfigurationSerializer

    def get_queryset(self):
        queryset = WorkflowConfiguration.objects.all()
        workflow_version_id = self.request.query_params.get('workflow_version', None)
        if workflow_version_id:
           queryset = queryset.filter(workflow_version__id=workflow_version_id)
        tag = self.request.query_params.get('tag', None)
        if tag:
            parts = WorkflowConfiguration.split_tag_parts(tag)
            if parts:
                workflow_tag, version_num, configuration_name = parts
                return queryset.filter(workflow_version__workflow__tag=workflow_tag,
                                       workflow_version__version=version_num,
                                       name=configuration_name)
            else:
                return WorkflowConfiguration.objects.none()
        else:
            return queryset

    @transaction.atomic
    @detail_route(methods=['post'], serializer_class=JobSerializer, url_path='create-job')
    def create_job(self, request, pk=None):
        """
        Create a new job based on our JobAnswerSet and return its json.
        """
        workflow_configuration = WorkflowConfiguration.objects.get(pk=pk)
        serializer = JobOrderDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job_order_data = serializer.save()
        job_factory = job_order_data.create_job_factory(request.user, workflow_configuration)
        job = job_factory.create_job()
        return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
