from rest_framework import serializers
from django.contrib.auth.models import User
from data.models import Workflow, WorkflowVersion, VMStrategy, WorkflowConfiguration
import json

# This field can go away when we switch to JSONField
class JSONStrField(serializers.Field):
    def to_representation(self, value):
        return json.loads(value)

    def to_internal_value(self, data):
        return json.dumps(data)


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
    tag = serializers.SerializerMethodField()
    user_fields = serializers.SerializerMethodField()

    def get_tag(self, obj):
        return obj.make_tag()

    def get_user_fields(self, obj):
        """
        Determines user supplied fields by removing those with answers in the system_job_order 
        from the workflow version's fields. 
        """
        system_keys = obj.system_job_order.keys()
        user_fields = []
        for field in obj.workflow_version.fields:
            if field['name'] not in system_keys:
                user_fields.append(field)
        return user_fields

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
