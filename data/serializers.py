from rest_framework import serializers
from data.models import Workflow, WorkflowVersion, Job, JobInputFile, DDSJobInputFile, \
    DDSEndpoint, DDSUserCredential, JobOutputProject, URLJobInputFile, JobError, JobAnswerSet, \
    JobQuestionnaire, VMFlavor, VMProject


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        resource_name = 'workflows'
        fields = ('id', 'name', 'versions')
        read_only_fields = ('versions',)


class WorkflowVersionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.workflow.name

    class Meta:
        model = WorkflowVersion
        resource_name = 'workflow-versions'
        fields = ('id', 'workflow', 'name', 'description', 'object_name', 'created', 'url', 'version')


class JobOutputProjectSerializer(serializers.ModelSerializer):
    def validate(self, data):
        request = self.context['request']
        # You must own the job you are attaching this output directory onto
        if data['job'].user != request.user:
            raise serializers.ValidationError("This job belongs to another user.")
        return data

    class Meta:
        model = JobOutputProject
        resource_name = 'job-output-projects'
        fields = '__all__'


class AdminJobOutputProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOutputProject
        resource_name = 'job-output-projects'
        fields = '__all__'


class JobErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobError
        resource_name = 'job-errors'
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    output_dir = JobOutputProjectSerializer(required=False, read_only=True)
    vm_project_name = serializers.CharField(required=False)
    state = serializers.CharField(read_only=True)
    step = serializers.CharField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    job_errors = JobErrorSerializer(required=False, read_only=True, many=True)

    class Meta:
        model = Job
        resource_name = 'jobs'
        fields = ('id', 'workflow_version', 'user', 'name', 'created', 'state', 'step', 'last_updated',
                  'vm_flavor', 'vm_instance_name', 'vm_project_name', 'job_order', 'output_dir',
                  'job_errors')


class AdminJobSerializer(serializers.ModelSerializer):
    workflow_version = WorkflowVersionSerializer(required=False)
    output_dir = JobOutputProjectSerializer(required=False, read_only=True)
    vm_project_name = serializers.CharField(required=False)
    user_id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)
    class Meta:
        model = Job
        resource_name = 'jobs'
        fields = ('id', 'workflow_version', 'user_id', 'name', 'created', 'state', 'step', 'last_updated',
                  'vm_flavor', 'vm_instance_name', 'vm_project_name', 'job_order', 'output_dir')


class DDSEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DDSEndpoint
        resource_name = 'dds-endpoints'
        fields = ('id', 'name', 'api_root')


class DDSUserCredSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    class Meta:
        model = DDSUserCredential
        resource_name = 'dds-user-credentials'
        fields = ('id', 'user', 'token', 'endpoint')


class ReadOnlyDDSUserCredSerializer(serializers.ModelSerializer):
    """
    Non-Admin users can only see the keys from the available DukeDS credentials(setup by admin).
    They need access to the keys so they can give download permission to the bespin user.    
    """
    class Meta:
        model = DDSUserCredential
        resource_name = 'dds-user-credentials'
        fields = ('id', 'user', 'endpoint')


class DDSJobInputFileSerializer(serializers.ModelSerializer):
    def validate(self, data):
        request = self.context['request']
        # You must own the job-input-file you are attaching this output directory onto
        if data['job_input_file'].job.user != request.user:
            raise serializers.ValidationError("This job_input_file belongs to another user.")
        return data

    class Meta:
        model = DDSJobInputFile
        resource_name = 'dds-job-input-files'
        fields = '__all__'


class URLJobInputFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = URLJobInputFile
        resource_name = 'url-job-input-files'
        fields = '__all__'


class JobInputFileSerializer(serializers.ModelSerializer):
    dds_files = serializers.SerializerMethodField()
    url_files = serializers.SerializerMethodField()

    # Sort inner dds files by their index so we can keep our arrays in the same order.
    def get_dds_files(self, obj):
        qset = DDSJobInputFile.objects.filter(job_input_file__pk=obj.pk).order_by('index')
        ser = DDSJobInputFileSerializer(qset, many=True, read_only=True)
        return ser.data

    # Sort inner url files by their index so we can keep our arrays in the same order.
    def get_url_files(self, obj):
        qset = URLJobInputFile.objects.filter(job_input_file__pk=obj.pk).order_by('index')
        ser = URLJobInputFileSerializer(qset, many=True, read_only=True)
        return ser.data

    class Meta:
        model = JobInputFile
        resource_name = 'job-input-files'
        fields = ('id', 'job', 'file_type', 'workflow_name', 'dds_files', 'url_files')


class AdminDDSEndpointSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DDSEndpoint
        resource_name = 'dds-endpoints'
        fields = ('id','name', 'agent_key', 'api_root')


class AdminDDSUserCredSerializer(serializers.ModelSerializer):
    endpoint = AdminDDSEndpointSerializer()

    class Meta:
        model = DDSUserCredential
        resource_name = 'dds-user-credentials'
        fields = ('id', 'user', 'token', 'endpoint')


class DDSProjectSerializer(serializers.Serializer):
    """
    Serializer for dds_resources.DDSProject
    """
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()

    class Meta:
        resource_name = 'dds-projects'


class DDSResourceSerializer(serializers.Serializer):
    kind = serializers.CharField()
    id = serializers.UUIDField()
    name = serializers.CharField()
    project = serializers.UUIDField()
    folder = serializers.UUIDField()
    version = serializers.IntegerField()
    version_id = serializers.UUIDField()
    size = serializers.IntegerField()

    class Meta:
        resource_name = 'dds-resources'


class VMFlavorSerializer(serializers.ModelSerializer):

    class Meta:
        model = VMFlavor
        resource_name = 'vm-flavors'
        fields = '__all__'


class VMProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = VMProject
        resource_name = 'vm-projects'
        fields = '__all__'


class JobAnswerSetSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = JobAnswerSet
        resource_name = 'job-answer-sets'
        fields = '__all__'


class JobQuestionnaireSerializer(serializers.ModelSerializer):
    vm_flavor = VMFlavorSerializer()
    vm_project = VMProjectSerializer()

    class Meta:
        model = JobQuestionnaire
        resource_name = 'job-questionnaires'
        fields = '__all__'

