import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.db import transaction
from bespin_api_v2.serializers import VMStrategySerializer, WorkflowConfigurationSerializer
from data.serializers import JobSerializer
from data.models import VMStrategy, WorkflowConfiguration, JobFileStageGroup
from data.jobfactory import create_job_factory_for_workflow_configuration, JobOrderData


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
        job_name = request.data.get('job_name')
        fund_code = request.data.get('fund_code')
        stage_group_id = request.data.get('stage_group')
        user_job_order = request.data.get('user_job_order')
        job_vm_strategy_id = request.data.get('job_vm_strategy')
        workflow_configuration = WorkflowConfiguration.objects.get(pk=pk)
        system_job_order = json.loads(workflow_configuration.system_job_order_json)

        job_order_data = JobOrderData(
            stage_group=JobFileStageGroup.objects.get(pk=stage_group_id),
            system_job_order=system_job_order,
            user_job_order=user_job_order,
        )
        try:
            job_vm_strategy = VMStrategy.objects.get(pk=job_vm_strategy_id)
        except VMStrategy.DoesNotExist:
            job_vm_strategy = None

        job_factory = create_job_factory_for_workflow_configuration(workflow_configuration, request.user,
                                                                    job_name, fund_code, job_order_data,
                                                                    job_vm_strategy=job_vm_strategy)

        job = job_factory.create_job()
        serializer = JobSerializer(job)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
