from rest_framework import serializers
from django.contrib.auth.models import User
from data.models import VMStrategy, WorkflowConfiguration
import json


class WorkflowConfigurationSerializer(serializers.ModelSerializer):
    tag = serializers.SerializerMethodField()
    user_fields_json = serializers.SerializerMethodField()

    def get_tag(self, obj):
        return obj.make_tag()

    def get_user_fields_json(self, obj):
        fields = json.loads(obj.workflow_version.fields_json)
        system_order_json = json.loads(obj.system_job_order_json)
        system_keys = system_order_json.keys()
        user_fields_json = []
        for field in fields:
            if field['name'] not in system_keys:
                user_fields_json.append(field)
        return json.dumps(user_fields_json)

    class Meta:
        model = WorkflowConfiguration
        resource_name = 'workflow-configuration'
        fields = '__all__'


class VMStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = VMStrategy
        resource_name = 'vm-strategies'
        fields = '__all__'
