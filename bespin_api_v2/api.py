import json
from rest_framework import viewsets, permissions, status, mixins, generics
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from bespin_api_v2.serializers import AdminWorkflowSerializer, AdminWorkflowVersionSerializer, VMStrategySerializer, \
    WorkflowConfigurationSerializer, JobOrderDataSerializer, JobFileSerializer, WorkflowVersionSerializer, \
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
    serializer_class = JobFileSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job_file = serializer.save()
        serializer = self.get_serializer(instance=job_file)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class JobTemplateCreateJobView(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = JobOrderDataSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job_order_data = serializer.save()
        job_order_data.create_job(request.user)
        serializer = self.get_serializer(instance=job_order_data)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
