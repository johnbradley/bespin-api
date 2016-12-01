from rest_framework import serializers
from data.models import Workflow, WorkflowVersion, Job, JobParam, JobParamDDSFile, \
    DDSApplicationCredential, DDSUserCredential


class WorkflowSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Workflow
        fields = ('id', 'name', 'versions')


class WorkflowVersionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WorkflowVersion
        fields = ('id', 'workflow', 'object_name', 'created', 'url', 'version')


class JobSerializer(serializers.HyperlinkedModelSerializer):
    workflow_version = WorkflowVersionSerializer(read_only=True)
    class Meta:
        model = Job
        fields = ('id', 'workflow_version', 'user_id', 'created', 'state', 'last_updated',
                  'vm_flavor', 'vm_instance_name', 'params')
        read_only_fields = ('params',)


class JobParamDDSFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobParamDDSFile
        fields = ('id', 'project_id', 'file_id', 'path','dds_app_credentials', 'dds_user_credentials')


class JobParamSerializer(serializers.HyperlinkedModelSerializer):
    dds_file = JobParamDDSFileSerializer(read_only=True)
    class Meta:
        model = JobParam
        fields = ('id', 'job', 'name', 'type', 'value', 'staging', 'dds_file')


class DDSAppCredSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DDSApplicationCredential
        fields = ('id','name', 'agent_key', 'api_root')


class DDSUserCredSerializer(serializers.ModelSerializer):
    class Meta:
        model = DDSUserCredential
        fields = ('id','user', 'token')