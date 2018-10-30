from rest_framework import serializers
from django.contrib.auth.models import User
from data.models import Workflow, WorkflowVersion, VMStrategy, WorkflowConfiguration
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
        fields = '__all__'


class JSONStrField(serializers.Field):
    """
    Color objects are serialized into 'rgb(#, #, #)' notation.
    """
    def to_representation(self, value):
        return json.loads(value)

    def to_internal_value(self, data):
        return json.dumps(data)


class WorkflowConfigurationSerializer(serializers.ModelSerializer):
    tag = serializers.SerializerMethodField()
    system_job_order = JSONStrField(source="system_job_order_json")

    def get_tag(self, obj):
        return obj.make_tag()

    class Meta:
        model = WorkflowConfiguration
        resource_name = 'workflow-configuration'
        fields = ['id', 'name', 'tag', 'workflow_version', 'system_job_order', 'default_vm_strategy', 'share_group']


class VMStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = VMStrategy
        resource_name = 'vm-strategies'
        fields = '__all__'
