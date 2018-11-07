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
    tag = serializers.CharField(source='make_tag', read_only=True)
    user_fields = serializers.SerializerMethodField()

    def get_user_fields(self, obj):
        """
        Determines user supplied fields by removing those with answers in the system_job_order 
        from the workflow version's fields. 
        """
        system_keys = obj.system_job_order.keys()
        user_fields_json = []
        for field in obj.workflow_version.fields:
            if field['name'] not in system_keys:
                user_fields_json.append(field)
        return user_fields_json

    class Meta:
        model = WorkflowConfiguration
        resource_name = 'workflow-configuration'
        fields = ['id', 'name', 'tag', 'workflow_version', 'user_fields', 'system_job_order',
                  'default_vm_strategy', 'share_group', ]


class VMStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = VMStrategy
        resource_name = 'vm-strategies'
        fields = '__all__'


class JobOrderDataSerializer(serializers.Serializer):
    job_name = serializers.CharField()
    fund_code = serializers.CharField()
    stage_group = serializers.PrimaryKeyRelatedField(queryset=JobFileStageGroup.objects.all())
    user_job_order = serializers.DictField()
    job_vm_strategy = serializers.PrimaryKeyRelatedField(queryset=VMStrategy.objects.all(), allow_null=True)

    def create(self, validated_data):
        return JobOrderData(**validated_data)
