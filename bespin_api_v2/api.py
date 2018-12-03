import json
from rest_framework import viewsets, permissions, status, mixins, generics
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from bespin_api_v2.serializers import AdminWorkflowSerializer, AdminWorkflowVersionSerializer, VMStrategySerializer, \
    WorkflowConfigurationSerializer, JobTemplateMinimalSerializer, JobTemplateSerializer, WorkflowVersionSerializer, \
    ShareGroupSerializer
from data.serializers import JobSerializer
from data.models import Workflow, WorkflowVersion, VMStrategy, WorkflowConfiguration, JobFileStageGroup, ShareGroup
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



class WorkflowVersionsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = WorkflowVersion.objects.all()
    serializer_class = WorkflowVersionSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('workflow',)


class WorkflowConfigurationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = WorkflowConfigurationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('workflow',)

    def get_queryset(self):
        queryset = WorkflowConfiguration.objects.all()
        workflow_tag = self.request.query_params.get('workflow_tag', None)
        if workflow_tag:
            queryset =  queryset.filter(workflow__tag=workflow_tag)
        return queryset


class ShareGroupViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = ShareGroup.objects.all()
    serializer_class = ShareGroupSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('name', 'email', )


class JobTemplateInitView(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobTemplateMinimalSerializer

    def perform_create(self, serializer):
        job_template = serializer.save()
        job_template.populate_job_order()


class JobTemplateCreateJobView(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobTemplateSerializer

    def perform_create(self, serializer):
        job_template = serializer.save()
        job_template.create_and_populate_job(self.request.user)
