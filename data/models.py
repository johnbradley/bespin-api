from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class DDSApplicationCredential(models.Model):
    """
    Stores the agent key for this application
    """
    name = models.CharField(max_length=255, blank=False, unique=True)
    agent_key = models.CharField(max_length=32, blank=False, unique=True)
    api_root = models.URLField()


class DDSUserCredential(models.Model):
    """
    DDS Credentials for bespin users
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=False)
    token = models.CharField(max_length=32, blank=False, unique=True)


class Workflow(models.Model):
    """
    Name of a workflow that will apply some processing to some data.
    """
    name = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name


class WorkflowVersion(models.Model):
    """
    Specific version of a Workflow.
    """
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='versions')
    object_name = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    version = models.CharField(max_length=32, blank=False)
    url = models.URLField()

    def __unicode__(self):
        return '{} version: {} created: {}'.format(self.workflow.name, self.version, self.created)


class Job(models.Model):
    """
    Instance of a workflow that is in some state of progress.
    """
    JOB_STATES = (
        ('N', 'New'),
        ('V', 'Create VM'),
        ('S', 'Staging In'),
        ('R', 'Running'),
        ('O', 'Store Job Output'),
        ('T', 'Terminate VM'),
        ('F', 'Finished'),
        ('E', 'Errored'),
        ('C', 'Canceled')
    )
    workflow_version = models.ForeignKey(WorkflowVersion, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    state = models.CharField(max_length=1, choices=JOB_STATES, default='N')
    last_updated = models.DateTimeField(auto_now=True, blank=False)
    vm_flavor = models.CharField(max_length=255, blank=False, default='m1.small')
    vm_instance_name = models.CharField(max_length=255, blank=False, null=True)
    workflow_input_json = models.TextField(null=True)

    def __unicode__(self):
        workflow_name = self.workflow_version.workflow
        return '{} ({}) for user {}'.format(workflow_name, self.get_state_display(), self.user)


class JobOutputDir(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, null=False, related_name='output_dir')
    dir_name = models.CharField(max_length=255, blank=False, null=True)
    project_id = models.CharField(max_length=255, blank=False, null=True)
    dds_app_credentials = models.ForeignKey(DDSApplicationCredential, on_delete=models.CASCADE, null=True)
    dds_user_credentials = models.ForeignKey(DDSUserCredential, on_delete=models.CASCADE, null=True)

    def __unicode__(self):
        return 'Directory name: {} Project: {}'.format(self.dir_name, self.project_id)


class JobInputFile(models.Model):
    DUKE_DS_FILE = 'dds_file'
    DUKE_DS_FILE_ARRAY = 'dds_file_array'
    URL_FILE = 'url_file'
    URL_FILE_ARRAY = 'url_file_array'
    INPUT_FILE_TYPE = (
        (DUKE_DS_FILE, 'DukeDS File'),
        (DUKE_DS_FILE_ARRAY, 'DukeDS File Array'),
        (URL_FILE, 'URL File'),
        (URL_FILE_ARRAY, 'URL File Array'),
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=False, related_name='input_files')
    file_type = models.CharField(max_length=30, choices=INPUT_FILE_TYPE)
    workflow_name = models.CharField(max_length=255, null=True)

    def __unicode__(self):
        return 'Job Input File "{}"  ({})'.format(self.workflow_name, self.file_type)


class DDSJobInputFile(models.Model):
    job_input_file = models.ForeignKey(JobInputFile, on_delete=models.CASCADE, null=False, related_name='dds_files')
    project_id = models.CharField(max_length=255, blank=False, null=True)
    file_id = models.CharField(max_length=255, blank=False, null=True)
    dds_app_credentials = models.ForeignKey(DDSApplicationCredential, on_delete=models.CASCADE)
    dds_user_credentials = models.ForeignKey(DDSUserCredential, on_delete=models.CASCADE)
    destination_path = models.CharField(max_length=255, blank=False, null=True)
    index = models.IntegerField(null=True)

    def __unicode__(self):
        return 'DDS Job Input File "{}" ({}) id:{}'.format(self.destination_path, self.job_input_file.workflow_name,
                                                     self.file_id)


class URLJobInputFile(models.Model):
    job_input_file = models.ForeignKey(JobInputFile, on_delete=models.CASCADE, null=False, related_name='url_files')
    url = models.TextField(null=True)
    destination_path = models.CharField(max_length=255, blank=False, null=True)
    index = models.IntegerField(null=True)

    def __unicode__(self):
        return 'URL Job Input File {} ({})'.format(self.url, self.job_input_file.workflow_name)

