from rest_framework import serializers
from django.contrib.auth.models import User
from data.models import Workflow, WorkflowVersion, VMStrategy, WorkflowConfiguration, JobFileStageGroup, VMStrategy
from data.jobfactory import JobOrderData
import json


class AdminWorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        resource_name = 'workflows'
        fields = '__all__'


class AdminWorkflowVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowVersion
        resource_name = 'workflowversions'
        fields = ['id', 'workflow', 'description', 'object_name', 'created', 'version', 'url', 'fields']


class WorkflowConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowConfiguration
        resource_name = 'workflow-configuration'
        fields = '__all__'


class VMStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = VMStrategy
        resource_name = 'vm-strategies'
        fields = '__all__'


class JobOrderDataSerializer(serializers.Serializer):
    workflow_version = serializers.PrimaryKeyRelatedField(queryset=WorkflowVersion.objects.all())
    job_name = serializers.CharField()
    fund_code = serializers.CharField()
    stage_group = serializers.PrimaryKeyRelatedField(queryset=JobFileStageGroup.objects.all())
    user_job_order = serializers.DictField()
    job_vm_strategy = serializers.PrimaryKeyRelatedField(queryset=VMStrategy.objects.all(), allow_null=True)

    def create(self, validated_data):
        return JobOrderData(**validated_data)
